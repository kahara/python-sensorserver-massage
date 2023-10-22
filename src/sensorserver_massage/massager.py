"""The massager"""
# pylint: disable=W1203

import datetime
import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy
import polars as pl
from polars import Series

# from scipy.signal import periodogram  # type: ignore

from .denoise import denoise_1d_mctv, Parameter  # type: ignore

# import matplotlib.pyplot as plt

LOGGER = logging.getLogger(__name__)


@dataclass
class Massager:
    """The massager"""

    source: Path = field()
    destination: Path = field()
    starttime: datetime.datetime = field()
    offset_nanos: int = field(init=False)
    raw: pl.LazyFrame = field(init=False)
    preprocessed: pl.LazyFrame = field(init=False)
    processed: pl.LazyFrame = field(init=False)

    def __post_init__(self) -> None:
        """Load the data"""

        self.raw = pl.scan_ndjson(self.source)
        LOGGER.info(f"We have a {self.raw}")

        self.offset_nanos: int = (
            (
                self.starttime.astimezone(tz=datetime.timezone.utc)
                - datetime.datetime.utcfromtimestamp(0).astimezone(tz=datetime.timezone.utc)
            ).total_seconds()
            * 1000000000
        ) - self.raw.first().collect()["timestamp"][0]
        LOGGER.info(f"Starting offset is {self.offset_nanos}ns")

    def preprocess(self):
        """Subtract medians, then denoise"""

        # @lru_cache
        def denoise(samples: Series) -> Any:
            """Attempt to recover more of the signal"""
            sig = 0.5
            lam = numpy.sqrt(sig * len(samples)) / 10  # 5
            num = 100
            err = 0.001
            alp = 0.3 / lam

            return pl.datatypes.maybe_cast(denoise_1d_mctv(samples, Parameter(lam, num, err, alp)), pl.List(pl.Float64))

        self.preprocessed = (
            self.raw.select(
                (pl.from_epoch(pl.col("timestamp") + self.offset_nanos, time_unit="ns")).set_sorted().alias("utc"),
                pl.col("values"),
            )
            .group_by_dynamic(index_column="utc", every="5m", period="10m", offset="0s")
            .agg(
                [
                    (
                        pl.col("values")
                        .list.take(0)
                        .explode()
                        .sub(pl.col("values").list.take(0).explode().median())
                        .map_elements(denoise)
                        .pow(2)
                        .alias("x")
                        + pl.col("values")
                        .list.take(1)
                        .explode()
                        .sub(pl.col("values").list.take(1).explode().median())
                        .map_elements(denoise)
                        .pow(2)
                        .alias("y")
                        + pl.col("values")
                        .list.take(2)
                        .explode()
                        .sub(pl.col("values").list.take(2).explode().median())
                        .map_elements(denoise)
                        .pow(2)
                        .alias("z")
                    )
                    .sqrt()
                    .alias("amplitudes"),
                ]
            )
        )

        LOGGER.debug(f"Preprocessed query looks like {self.preprocessed.explain(optimized=True)}")
        # LOGGER.debug(f"Preprocessed data looks like {self.preprocessed.collect()}")

    def process(self):
        """Compute"""

        self.processed = self.preprocessed.select(
            pl.col("utc"), pl.col("amplitudes").list.eval(pl.element().pow(2)).list.mean().sqrt().alias("rms")
        )

        LOGGER.debug(f"Processed query looks like {self.processed.explain(optimized=True)}")
        # LOGGER.debug(f"Processed data looks like {self.processed.collect()}")

    def run(self) -> int:
        """Run the massaging"""

        self.preprocess()
        self.process()

        LOGGER.info(f"Writing to {self.destination}")
        self.processed.collect().write_csv(sys.stdout if self.destination is None else self.destination)

        return 0

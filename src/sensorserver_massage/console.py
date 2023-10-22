"""CLI entrypoints for sensorserver-massage"""
# pylint: disable=W1203
import datetime
import sys
import logging
from pathlib import Path

import click
from dateutil.parser import isoparse

from datastreamcorelib.logging import init_logging
from sensorserver_massage import __version__
from sensorserver_massage.massager import Massager


LOGGER = logging.getLogger(__name__)


@click.command()
@click.version_option(version=__version__)
@click.option("-l", "--loglevel", help="Python log level, 10=DEBUG, 20=INFO, 30=WARNING, 40=CRITICAL", default=30)
@click.option("-v", "--verbose", count=True, help="Shorthand for info/debug loglevel (-v/-vv)")
@click.option("-s", "--source", help="Source JSONlines file")
@click.option("-d", "--destination", help="Destination CSV file")
def sensorserver_massage_cli(loglevel: int, verbose: int, source: Path, destination: Path) -> None:
    """Foo!"""
    if verbose == 1:
        loglevel = 20
    if verbose >= 2:
        loglevel = 10
    init_logging(loglevel)
    LOGGER.setLevel(loglevel)

    massager = Massager(source, destination, starttime_from_sourcefilename(Path(source)))

    sys.exit(massager.run())


def starttime_from_sourcefilename(source: Path) -> datetime.datetime:
    """Extract starting timestamp from source file name"""
    starttime = isoparse(source.name.replace(".jsonl", ""))
    LOGGER.info(f"Start time is {starttime}")
    return starttime

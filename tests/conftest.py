"""Test fixtures"""
import logging
from libadvian.logging import init_logging


# pylint: disable=W0621
init_logging(logging.DEBUG)
LOGGER = logging.getLogger(__name__)

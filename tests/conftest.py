"""Test fixtures"""
from typing import Any, AsyncGenerator
import asyncio
from pathlib import Path
import logging
import platform
import random

import tomlkit  # type: ignore
import pytest
import pytest_asyncio
from libadvian.testhelpers import nice_tmpdir  # pylint: disable=W0611
from libadvian.logging import init_logging
from datastreamservicelib.reqrep import REPMixin, REQMixin
from datastreamservicelib.service import SimpleService
from datastreamservicelib.compat import asyncio_eventloop_check_policy, asyncio_eventloop_get

from sensorserver_massage.defaultconfig import DEFAULT_CONFIG_STR
from sensorserver_massage.service import Sensorserver_massageService


# pylint: disable=W0621
init_logging(logging.DEBUG)
LOGGER = logging.getLogger(__name__)
asyncio_eventloop_check_policy()


@pytest.fixture
def event_loop():  # type: ignore
    """override pytest-asyncio default eventloop"""
    loop = asyncio_eventloop_get()
    LOGGER.debug("Yielding {}".format(loop))
    yield loop
    loop.close()


class ExampleREPlier(REPMixin, SimpleService):
    """Implement simple REPly interface, you can use this to mock some other services REPly API"""

    async def echo(self, *args: Any) -> Any:
        """return the args"""
        _ = self
        await asyncio.sleep(0.01)
        return args


class ExampleREQuester(REQMixin, SimpleService):
    """Can be used to test Sensorserver_massageService REP api via REQuests from outside"""


@pytest_asyncio.fixture
async def service_instance(nice_tmpdir: str) -> Sensorserver_massageService:
    """Create a service instance for use with tests"""
    parsed = tomlkit.parse(DEFAULT_CONFIG_STR)
    # On platforms other than windows, do not bind to TCP (and put the sockets into temp paths/ports)
    pub_sock_path = "ipc://" + str(Path(nice_tmpdir) / "sensorserver_massage_pub.sock")
    rep_sock_path = "ipc://" + str(Path(nice_tmpdir) / "sensorserver_massage_rep.sock")
    if platform.system() == "Windows":
        pub_sock_path = f"tcp://127.0.0.1:{random.randint(1337, 65000)}"  # nosec
        rep_sock_path = f"tcp://127.0.0.1:{random.randint(1337, 65000)}"  # nosec
    parsed["zmq"]["pub_sockets"] = [pub_sock_path]
    parsed["zmq"]["rep_sockets"] = [rep_sock_path]
    # Write a testing config file
    configpath = Path(nice_tmpdir) / "sensorserver_massage_testing.toml"
    with open(configpath, "wt", encoding="utf-8") as fpntr:
        fpntr.write(tomlkit.dumps(parsed))
    # Instantiate service and return it
    serv = Sensorserver_massageService(configpath)
    return serv


@pytest_asyncio.fixture
async def replier_instance(nice_tmpdir: str) -> ExampleREPlier:
    """Create a replier instance for use with tests"""
    parsed = tomlkit.parse(DEFAULT_CONFIG_STR)
    # Do not bind to TCP socket for testing and use test specific temp directory
    pub_sock_path = "ipc://" + str(Path(nice_tmpdir) / "sensorserver_massage_replier_pub.sock")
    rep_sock_path = "ipc://" + str(Path(nice_tmpdir) / "sensorserver_massage_replier_rep.sock")
    if platform.system() == "Windows":
        pub_sock_path = f"tcp://127.0.0.1:{random.randint(1337, 65000)}"  # nosec
        rep_sock_path = f"tcp://127.0.0.1:{random.randint(1337, 65000)}"  # nosec
    parsed["zmq"]["pub_sockets"] = [pub_sock_path]
    parsed["zmq"]["rep_sockets"] = [rep_sock_path]
    # Write a testing config file
    configpath = Path(nice_tmpdir) / "sensorserver_massage_testing_replier.toml"
    with open(configpath, "wt", encoding="utf-8") as fpntr:
        fpntr.write(tomlkit.dumps(parsed))
    # Instantiate service and return it
    serv = ExampleREPlier(configpath)
    return serv


@pytest_asyncio.fixture
async def requester_instance(nice_tmpdir: str) -> ExampleREQuester:
    """Create a requester instance for use with tests"""
    parsed = tomlkit.parse(DEFAULT_CONFIG_STR)
    # Do not bind to TCP socket for testing and use test specific temp directory
    pub_sock_path = "ipc://" + str(Path(nice_tmpdir) / "sensorserver_massage_requester_pub.sock")
    if platform.system() == "Windows":
        pub_sock_path = f"tcp://127.0.0.1:{random.randint(1337, 65000)}"  # nosec
    parsed["zmq"]["pub_sockets"] = [pub_sock_path]
    # Write a testing config file
    configpath = Path(nice_tmpdir) / "sensorserver_massage_testing_requester.toml"
    with open(configpath, "wt", encoding="utf-8") as fpntr:
        fpntr.write(tomlkit.dumps(parsed))
    # Instantiate service and return it
    serv = ExampleREQuester(configpath)
    return serv


@pytest_asyncio.fixture
async def running_service_instance(service_instance: Sensorserver_massageService) -> AsyncGenerator[Sensorserver_massageService, None]:
    """Yield a running service instance, shut it down after the test"""
    task = asyncio.create_task(service_instance.run())
    # Yield a moment so setup can do it's thing
    await asyncio.sleep(0.1)

    yield service_instance

    service_instance.quit()

    try:
        await asyncio.wait_for(task, timeout=2)
    except TimeoutError:
        task.cancel()
    finally:
        # Clear alarms and default exception handlers
        Sensorserver_massageService.clear_exit_alarm()
        asyncio.get_event_loop().set_exception_handler(None)


@pytest_asyncio.fixture
async def running_requester_instance(requester_instance: ExampleREQuester) -> AsyncGenerator[ExampleREQuester, None]:
    """Yield a running service instance, shut it down after the test"""
    task = asyncio.create_task(requester_instance.run())
    # Yield a moment so setup can do it's thing
    await asyncio.sleep(0.1)

    yield requester_instance

    requester_instance.quit()

    try:
        await asyncio.wait_for(task, timeout=2)
    except TimeoutError:
        task.cancel()
    finally:
        # Clear alarms and default exception handlers
        ExampleREQuester.clear_exit_alarm()
        asyncio.get_event_loop().set_exception_handler(None)


@pytest_asyncio.fixture
async def running_replier_instance(replier_instance: ExampleREPlier) -> AsyncGenerator[ExampleREPlier, None]:
    """Yield a running service instance, shut it down after the test"""
    task = asyncio.create_task(replier_instance.run())
    # Yield a moment so setup can do it's thing
    await asyncio.sleep(0.1)

    yield replier_instance

    replier_instance.quit()

    try:
        await asyncio.wait_for(task, timeout=2)
    except TimeoutError:
        task.cancel()
    finally:
        # Clear alarms and default exception handlers
        ExampleREPlier.clear_exit_alarm()
        asyncio.get_event_loop().set_exception_handler(None)

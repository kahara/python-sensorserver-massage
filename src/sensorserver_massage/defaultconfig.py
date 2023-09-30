"""Default configuration file contents"""

# Remember to add tests for keys into test_sensorserver_massage.py
DEFAULT_CONFIG_STR = """
[zmq]
pub_sockets = ["ipc:///tmp/sensorserver_massage_pub.sock", "tcp://*:53706"]
rep_sockets = ["ipc:///tmp/sensorserver_massage_rep.sock", "tcp://*:53707"]

""".lstrip()

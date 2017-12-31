import socket
import config_loader
import threading
import sys
import daemon
import canopy_interface as ci
from canopy_interface import Command
from socket_utils import ConfigurableTCPServer, HeartbeatTCPHandler, cprint

"""The name of the YAML file from which to get configurations"""
SERVER_CONFIG_FILE_NAME = "server-config.yml"


class CanopyServer(daemon.Daemon):
    """TCP socket-based server for Canopy"""

    def __init__(self, pidfile):
        """Creates a Canopy server based on server-config.yml file"""
        daemon.Daemon.__init__(self, pidfile, stderr='/tmp/canopyserver.log')
        self.addr = (config["host"], config["port"])
        self.cmd_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # set up API interface
        ci.callback = self.__command_callback
        web_addr = (config["web_host"], config["web_port"])
        self.interface = ci.CanopyInterface(web_addr)

    def run(self):
        """Begin listening asynchronously for canopy clients"""

        # run heartbeat TCP server
        self.s = ConfigurableTCPServer(self.addr, HeartbeatTCPHandler, config)
        self.s_thread = threading.Thread(target=self.s.serve_forever)
        self.s_thread.start()
        cprint("canopy server listening at (%s, %d)\n" % self.addr, config)

        # run API interface
        self.interface.run()

    def __command_callback(self, cmd_type, *args):
        """Connects to CommandTCPHandler of a client and relays command"""

        retval = None

        if cmd_type == Command.LOG:
            cprint("canopy server log callback", config)
            service = args[0]

            # check validity of referenced service
            if service in self.s.connections:
                service_addr = self.s.connections[service]
                cmd_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                cmd_s.connect(service_addr)

                cmd_s.sendall(b"LOGS %s" % service.encode("utf-8"))
                logs = cmd_s.recv(1024).strip().decode()
                cmd_s.close()
                retval = logs

        elif cmd_type == Command.COMMAND:
            # TODO: implement commands
            pass

        elif cmd_type == Command.STATUS:
            cprint("canopy server status callback", config)
            retval = " ".join(self.s.connections.keys())

        return retval


if __name__ == "__main__":
    config = config_loader.load(SERVER_CONFIG_FILE_NAME)
    daemon = CanopyServer('/tmp/canopyserver-daemon.pid')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print("Unknown command")
            sys.exit(2)
        sys.exit(0)
    print("Usage: %s start|stop|restart" % sys.argv[0])
    sys.exit(2)

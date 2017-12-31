from socketserver import ThreadingTCPServer, StreamRequestHandler
import sys


class ConfigurableTCPServer(ThreadingTCPServer):
    """TCP server that takes a config object and stores connection metadata"""

    def __init__(self, server_address, RequestHandlerClass, config=None):
        self.config = config
        self.connections = {}
        ThreadingTCPServer.__init__(self, server_address, RequestHandlerClass)


class HeartbeatTCPHandler(StreamRequestHandler):
    """Handle connections and maintain set of live clients"""

    def handle(self):
        cprint("\033[92mnew connection: (%s, %d)\033[0m"
               % self.client_address, self.server.config)
        self.request.settimeout(self.server.config["timeout"])

        # maintain set of services on client
        client_services = set()

        # receive and initialize socket on command port
        while True:
            try:
                command_bytes = self.request.recv(1024).strip()
                command_addr = command_bytes.decode().split(":")
                command_addr[1] = int(command_addr[1])
                self.request.sendall(b"ACK")
                break
            except ValueError:
                self.request.sendall(b"NACK")
        cprint("    set command addr: %s" % command_addr, self.server.config)

        while True:
            # self.request is the TCP socket connected to the client
            data = self.request.recv(1024).strip()

            # request terminated or timed out
            if data == b"":
                break

            # update list of live services
            new_client_services = set()
            for service in data.split(b" "):
                if service is not b"DORMANT_RELAY":
                    new_client_services.add(service.decode())

            # new connections
            for new_serv in new_client_services - client_services:
                self.server.connections[new_serv] = tuple(command_addr)
                client_services.add(new_serv)

            # broken connections
            for broken_serv in client_services - new_client_services:
                del self.server.connections[broken_serv]
                client_services.remove(broken_serv)

        cprint("\033[93mend connection: (%s, %d)\033[0m\n"
               % self.client_address, self.server.config)

        # remove client from live connections
        for serv in self.client_services:
            del self.server.connections[serv]


def cprint(message, config):
    """Custom wrapper to print depending on config silent setting"""

    if not config["silent"]:
        sys.stderr.write(message+"\n")

from twisted.internet import protocol, reactor, endpoints
import logging

class Echo(protocol.Protocol):
    def connectionMade(self):
        self.transport.write("GROOT\n")
        self.transport.loseConnection()

class EchoFactory(protocol.Factory):
    def buildProtocol(self, addr):
        return Echo()

endpoints.serverFromString(reactor, "tcp:1234").listen(EchoFactory())
logging.warning("Running at localhost:1234")
reactor.run()

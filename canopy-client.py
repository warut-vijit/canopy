from twisted.internet import protocol, reactor
from sys import stdout

class Echo(protocol.Protocol):
    def dataReceived(self, data):
        stdout.write(data)

class EchoClientFactory(protocol.ClientFactory):
    def startedConnecting(self, connector):
        print('Started to connect.')

    def buildProtocol(self, addr):
        print('Connected.')
        return Echo()

    def clientConnectionLost(self, connector, reason):
        print('Lost connection.  Reason:', reason)
        reactor.stop()

    def clientConnectionFailed(self, connector, reason):
        print('Connection failed. Reason:', reason)

reactor.connectTCP("127.0.0.1", 1234, EchoClientFactory())
reactor.run()

# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.


import os
import sys
from twisted.internet import reactor, protocol, ssl


path = os.path.dirname(os.path.abspath(__file__))
KEYFILE = os.path.join(path, "ssl_test_rsa")    # Private key
CERTFILE = os.path.join(path, "ssl_test.crt")   # Certificate (self-signed)


class Echo(protocol.Protocol):
    """This is just about the simplest possible protocol"""

    def connectionMade(self):
         self.transport.setTcpNoDelay(True)

    def dataReceived(self, data):
        "As soon as any data is received, write it back."
        self.transport.write(data)


def main():
    """This runs the protocol on port 25000"""
    factory = protocol.ServerFactory()
    factory.protocol = Echo
    if len(sys.argv) > 1 and sys.argv[1] == '--ssl':
        reactor.listenSSL(25000, factory,
                          ssl.DefaultOpenSSLContextFactory(KEYFILE, CERTFILE))
    else:
        reactor.listenTCP(25000,factory)
    reactor.run()

# this only runs if the module was *not* imported
if __name__ == '__main__':
    main()

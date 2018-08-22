# Taken from curio: https://github.com/dabeaz/curio

import os
import sys
from gevent.server import StreamServer
from socket import *

# this handler will be run for each incoming connection in a dedicated greenlet
def echo(socket, address):
    print('New connection from %s:%s' % address)
    try:
        socket.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
    except (OSError, NameError):
        pass
    while True:
        data = socket.recv(100000)
        if not data:
            break
        socket.sendall(data)
    socket.close()

if __name__ == '__main__':
    kwargs = {}
    if len(sys.argv) > 1 and sys.argv[1] == '--ssl':
        path = os.path.dirname(os.path.abspath(__file__))
        kwargs['keyfile'] = os.path.join(path, "ssl_test_rsa")
        kwargs['certfile'] = os.path.join(path, "ssl_test.crt")
    server = StreamServer(('0.0.0.0', 25000), echo, **kwargs)
    server.serve_forever()

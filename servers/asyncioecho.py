import argparse
import asyncio
import gc
import uvloop
import os.path

from socket import *


PRINT = 0


async def echo_server(loop, address, unix, ssl=None):
    if unix:
        sock = socket(AF_UNIX, SOCK_STREAM)
    else:
        sock = socket(AF_INET, SOCK_STREAM)
        sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.bind(address)
    sock.listen(5)
    sock.setblocking(False)
    if PRINT:
        print('Server listening at', address)
    with sock:
        while True:
            client, addr = await loop.sock_accept(sock)
            if PRINT:
               print('Connection from', addr)
            if ssl:
                client = ssl.wrap_socket(client, server_side=True)
            loop.create_task(echo_client(loop, client))


async def echo_client(loop, client):
    try:
        client.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
    except (OSError, NameError):
        pass

    with client:
        while True:
            data = await loop.sock_recv(client, 102400)
            if not data:
                break
            await loop.sock_sendall(client, data)
    if PRINT:
        print('Connection closed')


async def echo_client_streams(reader, writer):
    sock = writer.get_extra_info('socket')
    try:
        sock.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
    except (OSError, NameError):
        pass
    if PRINT:
        print('Connection from', sock.getpeername())
    while True:
         data = await reader.readline()
         if not data:
             break
         writer.write(data)
    if PRINT:
        print('Connection closed')
    writer.close()


class EchoProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        self.transport = transport
        sock = transport.get_extra_info('socket')
        try:
            sock.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
        except (OSError, NameError):
            pass

    def connection_lost(self, exc):
        self.transport = None

    def data_received(self, data):
        self.transport.write(data)


class EchoBufferedProtocol(asyncio.BufferedProtocol):
    def connection_made(self, transport):
        self.transport = transport
        self.buffer = bytearray(256 * 1024)
        self.view = memoryview(self.buffer)
        sock = transport.get_extra_info('socket')
        try:
            sock.setsockopt(IPPROTO_TCP, TCP_NODELAY, 1)
        except (OSError, NameError):
            pass

    def connection_lost(self, exc):
        self.transport = None

    def get_buffer(self, sizehint):
        return self.buffer

    def buffer_updated(self, nbytes):
        self.transport.write(self.view[:nbytes].tobytes())


async def print_debug(loop):
    while True:
        print(chr(27) + "[2J")  # clear screen
        loop.print_debug_info()
        await asyncio.sleep(0.5, loop=loop)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--uvloop', default=False, action='store_true')
    parser.add_argument('--streams', default=False, action='store_true')
    parser.add_argument('--proto', default=False, action='store_true')
    parser.add_argument('--buffered', default=False, action='store_true')
    parser.add_argument('--addr', default='127.0.0.1:25000', type=str)
    parser.add_argument('--print', default=False, action='store_true')
    parser.add_argument('--ssl', action='store_true', help='enable SSL')
    args = parser.parse_args()

    if args.uvloop:
        loop = uvloop.new_event_loop()
        print('using UVLoop')
    else:
        loop = asyncio.new_event_loop()
        print('using asyncio loop')

    if args.ssl:
        import ssl
        path = os.path.dirname(os.path.abspath(__file__))
        KEYFILE = os.path.join(path, "ssl_test_rsa")
        CERTFILE = os.path.join(path, "ssl_test.crt")
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile=CERTFILE, keyfile=KEYFILE)
        ssl = context
    else:
        ssl = None

    asyncio.set_event_loop(loop)
    loop.set_debug(False)

    if args.print:
        PRINT = 1

    if hasattr(loop, 'print_debug_info'):
        loop.create_task(print_debug(loop))
        PRINT = 0

    unix = False
    if args.addr.startswith('file:'):
        unix = True
        addr = args.addr[5:]
        if os.path.exists(addr):
            os.remove(addr)
    else:
        addr = args.addr.split(':')
        addr[1] = int(addr[1])
        addr = tuple(addr)

    print('serving on: {}'.format(addr))

    if args.streams:
        if args.proto:
            print('cannot use --stream and --proto simultaneously')
            exit(1)

        if args.proto:
            print('cannot use --stream and --buffered simultaneously')
            exit(1)

        print('using asyncio/streams')
        if unix:
            coro = asyncio.start_unix_server(echo_client_streams,
                                             addr, loop=loop, ssl=ssl,
                                             limit=1024 * 1024)
        else:
            coro = asyncio.start_server(echo_client_streams,
                                        *addr, loop=loop, ssl=ssl,
                                        limit=1024 * 1024)
        srv = loop.run_until_complete(coro)
    elif args.proto:
        if args.streams:
            print('cannot use --stream and --proto simultaneously')
            exit(1)

        if args.buffered:
            print('using buffered protocol')
            protocol = EchoBufferedProtocol
        else:
            print('using simple protocol')
            protocol = EchoProtocol

        if unix:
            coro = loop.create_unix_server(protocol, addr, ssl=ssl)
        else:
            coro = loop.create_server(protocol, *addr, ssl=ssl)
        srv = loop.run_until_complete(coro)
    else:
        print('using sock_recv/sock_sendall')
        loop.create_task(echo_server(loop, addr, unix, ssl=ssl))
    try:
        loop.run_forever()
    finally:
        if hasattr(loop, 'print_debug_info'):
            gc.collect()
            print(chr(27) + "[2J")
            loop.print_debug_info()

        loop.close()

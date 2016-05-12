#!/usr/bin/env python3
import sys
import logging
import argparse
import ssl

# asyncio requires at least Python 3.3
if sys.version_info.major < 3 or \
    (sys.version_info.major > 2 and
    sys.version_info.minor < 3):
    print('At least Python version 3.3 is required to run this script!')
    sys.exit(1)

# Python 3.4 ships with asyncio in the standard libraries. Users with Python 3.3
# need to install it, e.g.: pip install asyncio
try:
    import asyncio
except ImportError:
    print('Please install asyncio!')
    sys.exit(1)
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass

LOGGER = logging.getLogger(__name__)

ARGS = argparse.ArgumentParser(description="Traffic forwarder")

ARGS.add_argument(
    '-H', '--host', default='127.0.0.1',
    help='Host to listen [default: %(default)s]')
ARGS.add_argument(
    '-p', '--port', type=int, default=8800,
    help='Port to listen [default: %(default)d]')
ARGS.add_argument(
    '-T', '--target', default='127.0.0.1',
    help='Host to connect [default: %(default)s]')
ARGS.add_argument(
    '-x', '--target-port', type=int, default=8080,
    help='Port to connect [default: %(default)d]')
ARGS.add_argument(
    '--ssl', action='store_true', dest='ssl',
    default=False, help='Create a SSL listener')
ARGS.add_argument(
    '--cert', help='Certificate for SSL server')
ARGS.add_argument(
    '--target-ssl', action='store_true', dest='target_ssl',
    default=False, help='Connect to target with SSL')

ARGS.add_argument(
    '-v', '--verbose', action='count', dest='level',
    default=2, help='Verbose logging (repeat for more verbosity)')
ARGS.add_argument(
    '-q', '--quiet', action='store_const', const=0, dest='level',
    default=2, help='Only log errors')


def request_hook(request):
    """Manipulate request before they will be sent to the target."""
    return request


def response_hook(response):
    """Manipulate response before they will be sent back to the source."""
    return response


class ForwardClient(asyncio.Protocol):

    def __init__(self, transport):
        self.connected = False
        self.server_transport = transport

    def connection_made(self, transport):
        self.connected = True
        self.transport = transport

    def data_received(self, data):
        LOGGER.debug('Client data received: {}'.format(data))
        data = response_hook(data)
        self.server_transport.write(data)

    def connection_lost(self, *args):
        self.connected = False


class ForwardProtocol(asyncio.Protocol):

    def __init__(self, target, target_port, target_ssl=None, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self.target = target
        self.target_port = target_port
        self.target_ssl = target_ssl
        self.clients = {}

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        LOGGER.debug('Data received: {!r}'.format(data))
        asyncio.Task(self.send_data(data))

    @asyncio.coroutine
    def send_data(self, data):
        peername = self.transport.get_extra_info('peername')
        client = self.clients.get(peername)

        if not client or not client.connected:
            if self.target_ssl:
                ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            else:
                ssl_context = None
            c = ForwardClient(self.transport)
            protocol, client = yield from self.loop.create_connection(
                lambda: c, self.target, self.target_port, ssl=ssl_context)
            self.clients[peername] = client

        data = request_hook(data)
        client.transport.write(data)


def main():
    args = ARGS.parse_args()
    levels = [logging.ERROR, logging.WARN, logging.INFO, logging.DEBUG]
    if args.level > 2:
        format = '[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s'
    else:
        format = '%(message)s'
    logging.basicConfig(level=levels[min(args.level, len(levels)-1)], format=format)

    if args.ssl:
        if not args.cert:
            LOGGER.error('Certificate missing')
            return 1
        ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_ctx.load_cert_chain(args.cert)
    else:
        ssl_ctx = None

    loop = asyncio.get_event_loop()

    forwarder = ForwardProtocol(args.target, args.target_port, target_ssl=args.target_ssl)
    coro = loop.create_server(
        lambda: forwarder, args.host, args.port, ssl=ssl_ctx)

    server = loop.run_until_complete(coro)

    try:
        loop.run_forever()
    except OSError:
        pass
    except KeyboardInterrupt:
        server.close()
        loop.run_until_complete(server.wait_closed())
    finally:
        loop.close()

    return 0


if __name__ == '__main__':
    sys.exit(main())

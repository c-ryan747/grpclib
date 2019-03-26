import asyncio

from grpclib.utils import graceful_exit
from grpclib.server import Server
from grpclib.server import Stream

from .helloworld_pb2 import HelloReply, HelloRequest
from .helloworld_grpc import GreeterBase


class Greeter(GreeterBase):

    # UNARY_UNARY - simple RPC
    async def UnaryUnaryGreeting(
        self,
        stream: Stream[HelloRequest, HelloReply],
    ) -> None:
        request = await stream.recv_message()
        message = 'Hello, {}!'.format(request.name)
        await stream.send_message(HelloReply(message=message))

    # UNARY_STREAM - response streaming RPC
    async def UnaryStreamGreeting(
        self,
        stream: Stream[HelloRequest, HelloReply],
    ) -> None:
        request = await stream.recv_message()
        await stream.send_message(
            HelloReply(message='Hello, {}!'.format(request.name)))
        await stream.send_message(
            HelloReply(message='Goodbye, {}!'.format(request.name)))

    # STREAM_UNARY - request streaming RPC
    async def StreamUnaryGreeting(
        self,
        stream: Stream[HelloRequest, HelloReply],
    ) -> None:
        names = []
        async for request in stream:
            names.append(request.name)
        message = 'Hello, {}!'.format(' and '.join(names))
        await stream.send_message(HelloReply(message=message))

    # STREAM_STREAM - bidirectional streaming RPC
    async def StreamStreamGreeting(
        self,
        stream: Stream[HelloRequest, HelloReply],
    ) -> None:
        async for request in stream:
            message = 'Hello, {}!'.format(request.name)
            await stream.send_message(HelloReply(message=message))
        # Send another message to demonstrate responses are not
        # coupled to requests.
        message = 'Goodbye, all!'
        await stream.send_message(HelloReply(message=message))


async def main(*, host: str = '127.0.0.1', port: int = 50051) -> None:
    loop = asyncio.get_running_loop()
    server = Server([Greeter()], loop=loop)
    with graceful_exit([server], loop=loop):
        await server.start(host, port)
        print(f'Serving on {host}:{port}')
        await server.wait_closed()


if __name__ == '__main__':
    asyncio.run(main())

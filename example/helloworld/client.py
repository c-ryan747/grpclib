import asyncio

from grpclib.client import Channel

from .helloworld_pb2 import HelloRequest
from .helloworld_grpc import GreeterStub


async def main() -> None:
    loop = asyncio.get_event_loop()
    channel = Channel('127.0.0.1', 50051, loop=loop)
    stub = GreeterStub(channel)

    response = await stub.SayHello(HelloRequest(name2='World'))
    print(response.message2)


if __name__ == '__main__':
    asyncio.run(main())

import gc
import asyncio

import objgraph

from dummy_pb2 import DummyRequest, DummyReply

from test_functional import UnixClientServer


def collect():
    objects = gc.get_objects()
    return {id(obj): obj for obj in objects}


async def stunt(loop):
    async with UnixClientServer(loop=loop) as (handler, stub):
        reply = await stub.UnaryUnary(DummyRequest(value='ping'))
        assert reply == DummyReply(value='pong')
        assert handler.log == [DummyRequest(value='ping')]


def test():
    loop = asyncio.new_event_loop()

    # warm up
    loop.run_until_complete(stunt(loop))

    gc.collect()
    gc.disable()
    try:
        pre = collect()

        loop.run_until_complete(stunt(loop))
        loop.stop()
        loop.close()
        # gc.collect()

        obj = objgraph.by_type('EventsProcessor')[0]
        objgraph.show_backrefs(obj, max_depth=10, filename='graph.png')

        post = collect()

        diff = set(post).difference(pre)
        diff.discard(id(pre))
        for i in diff:
            try:
                print(post[i])
            except Exception:
                print('...')
        # print([now[i] for i in diff])
        # print([type(now[i]) for i in diff])
    finally:
        gc.enable()
    1/0

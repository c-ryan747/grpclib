import sys
import asyncio

from types import TracebackType
from typing import Optional, Type
from contextlib import contextmanager

from .const import IService
from .metadata import Deadline


if sys.version_info > (3, 7):
    _current_task = asyncio.current_task
else:
    _current_task = asyncio.Task.current_task


class Wrapper:
    """Special wrapper for coroutines to wake them up in case of some error.

    Example:

    .. code-block:: python

        w = Wrapper()

        async def blocking_call():
            with w:
                await asyncio.sleep(10)

        # and somewhere else:
        w.cancel(NoNeedToWaitError('With explanation'))

    """
    _error = None
    _task = None

    cancelled = None

    def __enter__(self) -> None:
        if self._task is not None:
            raise RuntimeError('Concurrent call detected')

        if self._error is not None:
            raise self._error

        self._task = _current_task()
        assert self._task is not None, 'Called not inside a task'

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> None:
        self._task = None
        if self._error is not None:
            raise self._error

    def cancel(self, error: Exception) -> None:
        self._error = error
        if self._task is not None:
            self._task.cancel()
        self.cancelled = True


class DeadlineWrapper(Wrapper):
    """Deadline wrapper to specify deadline once for any number of awaiting
    method calls.

    Example:

    .. code-block:: python

        dw = DeadlineWrapper()

        with dw.start(deadline):
            await handle_request()

        # somewhere during request handling:

        async def blocking_call():
            with dw:
                await asyncio.sleep(10)

    """
    @contextmanager
    def start(self, deadline: Deadline, *, loop=None):
        loop = loop or asyncio.get_event_loop()
        timeout = deadline.time_remaining()
        if not timeout:
            raise asyncio.TimeoutError('Deadline exceeded')

        def callback():
            self.cancel(asyncio.TimeoutError('Deadline exceeded'))

        timer = loop.call_later(timeout, callback)
        try:
            yield self
        finally:
            timer.cancel()


def _service_name(service: IService) -> str:
    methods = service.__mapping__()
    method_name: Optional[str] = next(iter(methods), None)
    if method_name is None:
        raise ValueError('No methods defined in the service')
    else:
        _, service_name, _ = method_name.split('/')
        return service_name

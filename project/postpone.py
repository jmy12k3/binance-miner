from contextvars import ContextVar
from typing import List, Optional


def _default_list() -> Optional[List]:
    return None


should_postpone = ContextVar("should_postpone", default=False)
postponed_calls = ContextVar("postponed_calls", default=_default_list())


def heavy_call(func):
    def wrap(*args, **kwargs):
        if should_postpone.get():
            postponed_calls.get().append((func, args, kwargs))
        else:
            func(*args, **kwargs)

    return wrap


def postpone_heavy_calls(func):
    def wrap(*args, **kwargs):
        if should_postpone.get():
            func(*args, **kwargs)
        else:
            should_postpone.set(True)
            if postponed_calls.get() is None:
                postponed_calls.set([])
            try:
                func(*args, **kwargs)
            finally:
                should_postpone.set(False)
                pcs = postponed_calls.get()
                for pfunc, pargs, pkwargs in pcs:
                    pfunc(*pargs, **pkwargs)
                pcs.clear()

    return wrap

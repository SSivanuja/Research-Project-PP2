import time
from contextlib import contextmanager

@contextmanager
def timed_section(timings: dict, name: str):
    t0 = time.time()
    try:
        yield
    finally:
        timings[name] = round((time.time() - t0) * 1000.0, 2)  # ms

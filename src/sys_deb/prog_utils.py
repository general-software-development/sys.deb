from rich.progress import Progress, TaskID
from typing import Callable
from functools import wraps

def advance_progress(prog: Progress, task: TaskID, amount: float | int = 1):
    def decorator(fn: Callable):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            result = fn(*args, **kwargs)
            prog.advance(task, amount)
            return result

        return wrapper

    return decorator

import datetime
import functools
import json
from typing import Any, ParamSpec, Protocol, TypeVar
from urllib.request import urlopen

INVALID_CRITICAL_COUNT = "Breaker count must be positive integer!"
INVALID_RECOVERY_TIME = "Breaker recovery time must be positive integer!"
VALIDATIONS_FAILED = "Invalid decorator args."
TOO_MUCH = "Too much requests, just wait."

P = ParamSpec("P")
R_co = TypeVar("R_co", covariant=True)


class CallableWithMeta(Protocol[P, R_co]):
    __name__: str
    __module__: str

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> R_co: ...


class BreakerError(Exception):
    def __init__(self, message: str, func_name: str, block_time: datetime.datetime):
        super().__init__(message)
        self.func_name = func_name
        self.block_time = block_time


class CircuitBreaker:
    def __init__(
        self,
        critical_count: int = 5,
        time_to_recover: int = 30,
        triggers_on: type[Exception] = Exception,
    ):
        errors = []
        if not isinstance(critical_count, int) or critical_count <= 0:
            errors.append(ValueError(INVALID_CRITICAL_COUNT))

        if not isinstance(time_to_recover, int) or time_to_recover <= 0:
            errors.append(ValueError(INVALID_RECOVERY_TIME))

        if errors:
            raise ExceptionGroup(VALIDATIONS_FAILED, errors)

        self.critical_count = critical_count
        self.time_to_recover = time_to_recover
        self.triggers_on = triggers_on

    def __call__(self, func: CallableWithMeta[P, R_co]) -> CallableWithMeta[P, R_co]:
        failures = 0
        block_time = None

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal failures, block_time

            self.check_block(func, block_time)

            try:
                result = func(*args, **kwargs)
            except self.triggers_on as exc:
                failures += 1
                if failures >= self.critical_count:
                    block_time = datetime.datetime.now(datetime.UTC)
                    raise BreakerError(
                        message=TOO_MUCH,
                        func_name=self.get_func_name(func),
                        block_time=block_time,
                    ) from exc
                raise

            failures = 0
            block_time = None
            return result

        return wrapper

    def get_func_name(self, func: CallableWithMeta) -> str:
        return f"{func.__module__}.{func.__name__}"

    def check_block(self, func: CallableWithMeta, block_time: datetime.datetime | None):
        if block_time is None:
            return

        now = datetime.datetime.now(datetime.UTC)
        if (now - block_time).total_seconds() < self.time_to_recover:
            raise BreakerError(
                message=TOO_MUCH,
                func_name=self.get_func_name(func),
                block_time=block_time,
            )


circuit_breaker = CircuitBreaker(5, 30, Exception)


@circuit_breaker
def get_comments(post_id: int) -> Any:
    response = urlopen(f"https://jsonplaceholder.typicode.com/comments?postId={post_id}")
    return json.loads(response.read())


if __name__ == "__main__":
    comments = get_comments(1)

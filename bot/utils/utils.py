from time import sleep

from bot.utils.Logger import logger


def retry(times, exceptions, wait_exponential_multiplier=None, wait_exponential_max=None):
    """
    Retry Decorator. Retries the wrapped function multiple times if an exception is thrown or the function returns false
    :param times: The number of times to repeat the wrapped function/method
    :param exceptions: Lists of exceptions that trigger a retry attempt
    :param wait_exponential_multiplier: The exponential multiplier in milliseconds. E.g. if the multiplier is 1000 ms,
                                        it will wait 1 second before the first retry, then 2, 4, 8, ...
    :param wait_exponential_max: The maximum time to wait in milliseconds.
    """
    def decorator(func):
        def new_fn(*args, **kwargs):
            _wait_exponential_multiplier = 1 if wait_exponential_multiplier is None else wait_exponential_multiplier
            _wait_exponential_max = 1073741823 if wait_exponential_max is None else wait_exponential_max

            def exponential_sleep(previous_attempt_number):
                exp = 2 ** previous_attempt_number
                result = _wait_exponential_multiplier * exp
                if result > _wait_exponential_max:
                    result = _wait_exponential_max
                if result < 0:
                    result = 0
                return result / 1000.0

            attempt = 0
            ret = False
            while attempt < times:
                attempt += 1
                try:
                    ret = func(*args, **kwargs)
                    if ret:
                        return ret
                except exceptions as e:
                    logger.error(e)

                # Wait.
                if wait_exponential_multiplier:
                    seconds = exponential_sleep(attempt - 1)
                    logger.info(f"Sleep {seconds} seconds before retrying.")
                    sleep(seconds)

            return ret
        return new_fn
    return decorator

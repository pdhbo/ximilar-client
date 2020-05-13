from functools import wraps
import time


def retry_when(*exceptions, attempts=4, start_pause=5, multiply_pause=4, verbose=1):
    """
    Decorator which repeats given function in case any given exception occurs.
    By default, execute 4 times with 5, 20 and 80 second breaks between attempts.
    Exception is re-thrown only if number of attempts is exceeded.

    :param exceptions: one or more exceptions this decorator will catch
    :param attempts: how many times we will try to call the function; default 4
    :param start_pause: how many seconds we will be between first and second attempt; default 5
    :param multiply_pause: how the time between attempts will change; default 4 (pause is 4x longer after each failure)
    :param verbose: 0 for no prints, 1 print message when function call is no successful; default: 1
    """

    def decorator(function):
        @wraps(function)
        def wrap(*args, **kwargs):
            next_try_sec = start_pause

            for i in range(5):
                try:
                    return function(*args, **kwargs)
                except exceptions as e:
                    if verbose >= 1:
                        print(
                            f"{type(e).__name__} occurred. Attempt {i + 1}/{attempts}, "
                            + f"next try in {next_try_sec:.1f} seconds."
                        )
                    if i + 1 == attempts:
                        raise e

                    time.sleep(next_try_sec)
                    next_try_sec *= multiply_pause

        return wrap

    return decorator

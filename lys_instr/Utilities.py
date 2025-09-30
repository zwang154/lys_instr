import time


def preciseSleep(sleepTime):
    """
    Sleep for the specified interval (in seconds) with improved temporal precision.

    Avoids overshooting the requested sleep time by busy-waiting for the last ~0.5 ms.

    Args:
        sleepTime (float): The total time to sleep, in seconds.
    """
    wakeTime = time.perf_counter() + sleepTime
    while True:
        now = time.perf_counter()
        remaining = wakeTime - now
        if remaining > 0.001:
            time.sleep(remaining - 0.0005)
        elif remaining > 0:
            pass
        else:
            break
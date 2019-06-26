import __main__
import os
import datetime


def path(*objects):
    """
    Returns path relative to caller file location with additional objects
    """
    newPath = ((__main__.__file__).split(os.sep))[:-1]
    for i in objects:
        newPath.append(i)
    return (os.sep).join(str(y) for y in newPath)


def now():
    """
    Returns the time depending on time zone (will look at file soon)
    """
    return datetime.datetime.now() + datetime.timedelta(hours=7)

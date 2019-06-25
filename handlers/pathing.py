import __main__
import os


def path(*objects):
    """
    Returns path relative to caller file location with additional objects
    """
    newPath = ((__main__.__file__).split(os.sep))[:-1]
    for i in objects:
        newPath.append(i)
    return (os.sep).join(str(y) for y in newPath)

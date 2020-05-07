import sys
import os
import typing as t


def path(*filepath: t.Iterable) -> str:
    """Returns absolute path from main caller file to another location.

    Args:
        filepath (:obj:`t.Iterable`): Items to add to the curent filepath.

    Returns:
        String of relative filepath with OS based seperator.

    Examples:
        >>> print(path('tmp', 'image.png'))
        C:\\Users\\Xithr\\Pictures\\image.png

    """
    absolute = os.path.abspath(os.path.dirname(sys.argv[0]))
    return (os.sep).join(map(str, [absolute] + list(filepath)))

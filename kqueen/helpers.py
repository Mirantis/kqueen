"""Helpers are providing elementary functions and wrappers."""
import re

BINARY_PREFIX = {
    # decimal
    'm': 1000 ** -1,
    'k': 1000,
    'M': 1000 ** 2,
    'G': 1000 ** 3,
    'T': 1000 ** 4,
    'P': 1000 ** 5,
    # binary
    'mi': 1024 ** -1,
    'Ki': 1024,
    'Mi': 1024 ** 2,
    'Gi': 1024 ** 3,
    'Ti': 1024 ** 4,
    'Pi': 1024 ** 5,
}


def prefix_to_num(st):
    """Read string with prefix and return number.

    Args:
        st (string): String representation of value with prefix

    Returns:
        float: Calculated value without binary prefix

    Example:

        >>> prefix_to_num('1k')
        1000.0

    """
    num = ''
    prefix = ''

    # split number and prefix
    for i in range(len(st)):
        symbol = st[i]
        if symbol.isdigit() or symbol == '.':
            num += symbol
        else:
            prefix += symbol
    num = float(num)
    prefix = str(prefix).strip()

    # no prefix
    if prefix == '':
        return num

    # find multiplicator
    if prefix not in BINARY_PREFIX:
        raise ValueError('Prefix {} can not be parsed'.format(prefix))

    return num * BINARY_PREFIX[prefix]


def camel_split(st):
    """Split string by CamelCase.

    Args:
        st (string): Input string

    Returns:
        list: List of works splitted by camel case
    """

    return re.sub('(?!^)([A-Z][a-z]+)', r' \1', st).split()

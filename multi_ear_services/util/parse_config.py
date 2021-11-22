# absolute imports
import os
from configparser import ConfigParser, MissingSectionHeaderError


__all__ = ['parse_config']


def parse_config(filenames, config=None, defaults=None, **kwargs):
    """Parse a single config file using ConfigParser.read() while catching the
    MissingSectionHeaderError to the section '[default]'.
    """

    # subsitute clean environment
    if defaults is True:
        defaults = os.environ
    if defaults:
        for key, val in defaults.items():
            if '%' in val:
                defaults.pop(key)

    # init
    config = config or ConfigParser(defaults=defaults, **kwargs)

    # Config paths should be list or tuple
    if isinstance(filenames, str):
        filenames = [filenames]
    elif not isinstance(filenames, (list, tuple)):
        raise TypeError('filenames should be a str or a list/tuple of str')

    # parse files and add DEFAULT section if missing
    for filename in filenames:
        with open(filename, 'r') as f:
            try:
                config.read_file(f, source=config)
            except MissingSectionHeaderError:
                f_str = '[DEFAULT]\n' + f.read()
                config.read_string(f_str)

    return config

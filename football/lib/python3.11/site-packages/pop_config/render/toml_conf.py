"""
Define the yaml loader interface
"""

try:
    import toml

    HAS_TOML = (True,)
except ImportError as e:
    HAS_TOML = False, str(e)

__virtualname__ = "toml"


def __virtual__(hub):
    return HAS_TOML


def load(hub, path):
    """
    use toml to read in a file
    """
    try:
        with open(path) as fp_:
            return toml.loads(fp_.read())
    except FileNotFoundError:
        pass
    return {}


def render(hub, val):
    """
    Take the string and render it in json
    """
    return toml.loads(val)

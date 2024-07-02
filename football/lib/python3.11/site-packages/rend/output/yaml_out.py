from collections.abc import Mapping

import yaml

__virtualname__ = "yaml"


def display(hub, data):
    """
    Print the raw data
    """

    # # yaml safe_dump doesn't know how to represent subclasses of dict.
    # # this registration allows arbitrary dict types to be represented
    # # without conversion to a regular dict.
    def any_dict_representer(dumper, data):
        return dumper.represent_dict(data)

    yaml.add_multi_representer(dict, any_dict_representer, Dumper=yaml.SafeDumper)
    yaml.add_multi_representer(Mapping, any_dict_representer, Dumper=yaml.SafeDumper)

    return yaml.safe_dump(data)

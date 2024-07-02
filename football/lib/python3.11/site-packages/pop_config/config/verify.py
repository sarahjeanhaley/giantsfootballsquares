from typing import Dict
from typing import Iterable


def sanitize(hub, raw_cli: Dict[str, Dict], opt: Dict) -> bool:
    """
    Perform bulletproofing and sanitization of arguments

    If this function grows any larger it should be broken into a subsystem
    """
    for dyne, config in opt.items():
        for option, final_value in config.items():
            if option not in raw_cli:
                continue

            if not final_value:
                continue

            option_cli_config = raw_cli[option]

            if not isinstance(final_value, Iterable) or isinstance(
                final_value, (str, bytes)
            ):
                final_value = [final_value]

            # If the CLI_CONFIG specifies "choices" for the option,
            # ensure that the final value chosen for this option is one of them
            if "choices" in option_cli_config:
                choices = option_cli_config["choices"]

                # Cast the final value to a string to check it against choices
                for v in final_value:
                    if v not in choices:
                        raise ValueError(
                            f"invalid choice: {repr(v)} (choose from {', '.join(map(repr, choices))})"
                        )

    return True

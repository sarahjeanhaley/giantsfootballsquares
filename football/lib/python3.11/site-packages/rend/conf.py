CLI_CONFIG = {
    "file": {
        "options": ["--file", "-f"],
    },
    "pipe": {
        "options": ["--pipe", "-p"],
    },
    "output": {
        "options": ["--output", "-o"],
    },
}
CONFIG = {
    "file": {
        "default": None,
        "help": "Pass in a file location that will be rendered",
    },
    "pipe": {
        "default": "yaml",
        "help": "Define what render pipeline should be used",
    },
    "output": {
        "default": None,
        "help": "Define which outputter system should be used to display the result of this render",
    },
    "enable_jinja_sandbox": {
        "default": False,
        "help": "Enable sandboxed environment for Jinja rendering. Jinja sandboxing is disabled by default.",
    },
    "jinja_sandbox_safe_hub_refs": {
        "default": [".*"],
        "help": "Hub reference paths that should be allowed for Jinja rendering in the sandboxed environment. "
        "Everything on the hub is allowed by default.",
    },
}
GLOBAL = {}
SUBS = {}
DYNE = {
    "rend": ["rend"],
    "output": ["output"],
}

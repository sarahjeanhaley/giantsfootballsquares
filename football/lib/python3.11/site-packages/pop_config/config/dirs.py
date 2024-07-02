"""
Find the conf.py files specified in sources
"""
import importlib
import os.path
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import dict_tools.update

LOADED_MOD_CHOICES = "loaded_mod_choices_ref"


def load(hub, sources: List[str], dyne_names: List[str], cli: str):
    """
    Look over the sources list and find the correct conf.py files
    """
    # Dynamic names
    # Merged the sources dyne names with any passed dyne names
    # Load up and extend the raw with all of the dynamic names
    if not isinstance(sources, list):
        sources = [sources]

    unique_sources = []
    for source in sources:
        if source not in unique_sources and source != cli:
            unique_sources.append(source)
    # Make sure that the cli dyne name is processed last, so that it is authoritative on sourced defaults
    unique_sources.append(cli)

    # Get the base configs from imported sources
    raw = hub.config.dirs.find_configs(unique_sources)
    # Find dynamic namespaces on the hub that extend the DYNEs of the sources
    hub.config.dirs.resolve_dynes(unique_sources, dyne_names, raw)
    # Update the configs of parents that got new values from their merged children
    hub.config.dirs.resolve_sources(unique_sources, raw)
    # Ensure that options that specify a "dyne" of "__cli__" should always be shown
    hub.config.dirs.resolve_cli_config(unique_sources, raw, cli)

    return raw


def find_configs(hub, sources: List[str]):
    """
    Import the sources and locate their conf.py
    """
    raw = {}
    for source in sources:
        try:
            path, data = hub.config.dirs.import_conf(source)
            for k, v in data.items():
                v["PATH"] = path
            dict_tools.update.update(raw, data)
        except ImportError as e:
            hub.log.error(f"Could not find conf.py for '{source}': {e}")
    return raw


def import_conf(hub, imp: str) -> Tuple[str, Dict]:
    """
    Load up a python path, parse it and return the conf dataset
    """
    ret = {imp: {}}
    cmod = importlib.import_module(f"{imp}.conf")
    path = os.path.dirname(cmod.__file__)
    for section in hub.config.SECTIONS:
        ret[imp][section] = getattr(cmod, section, {})
    return path, ret


def resolve_dynes(hub, sources: List[str], dyne_names: List[str], raw: Dict):
    """
    Check if  a vertically merged project extends the CONFIG, CLI_CONFIG, or SUBCOMMANDS
    of its vertical parent and merge the options.
    """
    pop_dynes = hub.pop.dyne.get()

    for name, dyne_data in pop_dynes.items():
        # Use the name of the source, not the dyne
        for k, v in raw.items():
            if os.path.join(v["PATH"], name) in dyne_data["paths"]:
                dyne_data["SOURCE"] = k
                name = k
                break

        if name not in sources:
            continue

        if "CONFIG" in dyne_data:
            for key, val in dyne_data["CONFIG"].items():
                config_draw = {}
                new_dyne = hub.config.dirs.resolve_dyne(
                    dyne_data=val, draw=config_draw, key=key
                )

                if new_dyne in sources:
                    dict_tools.update.update(raw[new_dyne]["CONFIG"], config_draw)

                if key not in dyne_data["CLI_CONFIG"]:
                    continue

                # If the dyne is defined for this option in the CONFIG -- propogate it to the CLI_CONFIG
                if "dyne" not in dyne_data["CLI_CONFIG"][key]:
                    dyne_data["CLI_CONFIG"][key]["dyne"] = new_dyne
                    continue

                # Even if we are not operating on the authoritative CLI, ensure that extended configs get processed
                if (
                    "SOURCE" in dyne_data
                    and dyne_data["SOURCE"] == name
                    and key not in raw[name]["CONFIG"]
                    and name in dyne_names
                ):
                    raw[name]["CONFIG"][key] = val
                    continue

        if "CLI_CONFIG" in dyne_data:
            for key, val in dyne_data["CLI_CONFIG"].items():
                cli_draw = {}
                new_dyne = hub.config.dirs.resolve_dyne(
                    dyne_data=val, draw=cli_draw, key=key
                )

                if new_dyne in sources:
                    dict_tools.update.update(raw[new_dyne]["CLI_CONFIG"], cli_draw)
        if "SUBCOMMANDS" in dyne_data:
            for key, val in dyne_data["SUBCOMMANDS"].items():
                subcmd_draw = {}
                new_dyne = hub.config.dirs.resolve_dyne(
                    dyne_data=val, draw=subcmd_draw, key=key
                )
                if new_dyne in sources:
                    dict_tools.update.update(raw[new_dyne]["SUBCOMMANDS"], subcmd_draw)


def resolve_dyne(hub, dyne_data: Dict, draw: Dict, key: str) -> str or None:
    """
    Find out if the CONFIG/CLI_CONFIG/SUBCOMMANDS of a dyne extends another dyne
    """
    new_dyne = dyne_data.get("dyne", None)
    if new_dyne == "__cli__":
        return None
    elif new_dyne:
        draw[key] = dyne_data
        dyne_data["source"] = new_dyne

    return new_dyne


def resolve_sources(hub, sources: List[str], raw_cli: Dict[str, Any]):
    """
    If a cli opt defines a "source", then update the source defaults with the new values
    """
    for name in sources:
        if name not in raw_cli:
            continue
        dyne_config = raw_cli[name].get("CONFIG", {})
        if not dyne_config:
            continue

        to_remove = set()
        for opt_name, opt_data in dyne_config.items():
            source = opt_data.get("source")
            if not source:
                continue
            if source not in raw_cli:
                raw_cli[source] = {}
            if "CONFIG" not in raw_cli[source]:
                raw_cli[source]["CONFIG"] = {}
            # Remove the option from its parent and add it to the config of the source
            if source != name:
                to_remove.add(opt_name)
            if opt_name in raw_cli[source]["CONFIG"]:
                raw_cli[source]["CONFIG"][opt_name].update(opt_data)
            else:
                raw_cli[source]["CONFIG"][opt_name] = opt_data

        for item in to_remove:
            dyne_config.pop(item)


def resolve_cli_config(hub, sources: List[str], raw: Dict[str, Any], cli: str):
    """
    Find configs with options that use "__cli__" as their dyne
    """
    for name in sources:
        if name not in raw:
            raw[name] = {"CONFIG": {}, "CLI_CONFIG": {}, "SUBCOMMANDS": {}}

        dyne_data = raw[name]
        dyne_data["name"] = name
        if "CONFIG" in dyne_data:
            hub.config.dirs.parse_config(dyne_data, source=name)
        if "CLI_CONFIG" in dyne_data:
            cli_draw = hub.config.dirs.parse_cli(dyne_data, source=name)
            dict_tools.update.update(raw[cli]["CLI_CONFIG"], cli_draw)
        if "SUBCOMMANDS" in dyne_data:
            subcmd_draw = hub.config.dirs.parse_subcommand(dyne_data, source=name)
            dict_tools.update.update(raw[cli]["SUBCOMMANDS"], subcmd_draw)


def parse_config(hub, dyne_data: Dict[str, Dict], source: str) -> Dict:
    """
    If a dyne is defined in "CONFIG" -- ensure that it is also defined in "CLI_CONFIG"
    """
    config_draw = {}

    for key, val in dyne_data["CONFIG"].items():
        new_dyne = hub.config.dirs.resolve_cli(
            dyne_data=val, source=source, draw=config_draw, key=key
        )

        if not new_dyne:
            continue

        if key not in dyne_data["CLI_CONFIG"]:
            continue

        # If the dyne is defined for this option in the CONFIG -- propogate it to the CLI_CONFIG
        if "dyne" not in dyne_data["CLI_CONFIG"][key]:
            dyne_data["CLI_CONFIG"][key]["dyne"] = new_dyne
    return config_draw


def parse_cli(hub, dyne_data: Dict, source: str) -> Dict:
    """
    Handle special keys that are passed to options in CLI_CONFIG
    """
    cli_draw = {}
    for key, val in dyne_data["CLI_CONFIG"].items():
        # Set the "choices" parameter based on loaded mods at the given ref
        if val.get(LOADED_MOD_CHOICES):
            ref = val.pop(LOADED_MOD_CHOICES)
            try:
                val["choices"] = sorted(
                    name for name in hub[ref]._loaded if name != "init"
                )
            except AttributeError:
                hub.log.debug(f"Could not load choices for ref: '{ref}'")

        hub.config.dirs.resolve_cli(
            dyne_data=val, source=source, draw=cli_draw, key=key
        )
    return cli_draw


def parse_subcommand(hub, dyne_data: Dict, source: str) -> Dict:
    """
    Add app-merged subcommands to the main cli
    """
    subcmd_draw = {}
    for key, val in dyne_data["SUBCOMMANDS"].items():
        hub.config.dirs.resolve_cli(
            dyne_data=val, source=source, draw=subcmd_draw, key=key
        )
    return subcmd_draw


def resolve_cli(hub, dyne_data: Dict, source: str, draw: Dict, key: str) -> str or None:
    """
    If an option specifies "__cli__" as its dyne, then make sure it always gets drawn.
    """
    new_dyne = dyne_data.get("dyne", None)
    if new_dyne == "__cli__":
        dyne_data.pop("dyne")
        draw[key] = dyne_data
        dyne_data["source"] = source
        return None
    elif new_dyne and "source" not in dyne_data:
        dyne_data["source"] = new_dyne

    return new_dyne


def verify(hub, opts):
    """
    Verify that the environment and all named directories in the
    configuration exist
    """
    for imp in opts:
        for key in opts[imp]:
            if key == "root_dir":
                continue
            if key == "config_dir":
                continue
            if key.endswith("_dir"):
                if not os.path.isdir(opts[imp][key]):
                    os.makedirs(opts[imp][key])

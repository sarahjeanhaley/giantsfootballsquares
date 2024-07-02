import os
import pathlib


class _DefaultOption:
    pass


def _insert_default_placeholders(raw):
    defaults = {}
    for imp in raw:
        defaults[imp] = {}
        for key, data in raw[imp]["CONFIG"].items():
            if "default" not in data:
                raise KeyError(f"No default value for '{key}' in '{imp}'s conf.py")
            defaults[imp][key] = data["default"]
            data["default"] = _DefaultOption
    return defaults


def _restore_raw_defaults(raw, defaults):
    # undo our modification of the raw data structure
    for imp in raw:
        for key, data in raw[imp]["CONFIG"].items():
            raw[imp]["CONFIG"][key]["default"] = defaults[imp][key]


def _replace_default_placeholders(ret, defaults):
    for imp in ret:
        for key, data in ret[imp].items():
            if data is _DefaultOption:
                ret[imp][key] = defaults[imp][key]
    return ret


def _reroot_paths(defaults, root):
    for imp in defaults:
        for key, val in defaults[imp].items():
            try:
                path = pathlib.Path(val or "")
            except TypeError:
                continue
            if key == "root_dir":
                defaults[imp][key] = root
            elif (key.endswith(("_dir", "_path", "_file"))) and path.is_absolute():
                # only update absolute paths for keys
                #  ending in _dir, _path or _file
                defaults[imp][key] = _reroot_path(val, imp, root)


def _get_root(ret, cli):
    if "root_dir" not in ret.get(cli, {}):
        # there is no root_dir parameter, do not activate roots system
        #  otherwise there would be no way to *disable* the system
        #  either by leaving out root_dir, or manually specifying root_dir=/
        return None

    # root_dir is not configured, maybe use home directory
    if ret[cli]["root_dir"] is _DefaultOption:
        if hasattr(os, "geteuid") and os.geteuid() != 0:
            # Using pathlib.Path on all paths makes testing on multiple OSes much easier.
            # Since we can just patch pathlib.Path to be pathlib.PureWindowsPath or pathlib.PurePosixPath
            return str(pathlib.Path(os.path.expanduser("~")) / f".{cli}")
        else:
            return None
    else:
        return ret[cli]["root_dir"]


def _reroot_path(val, imp, new_root):
    root = pathlib.Path(new_root)
    path = pathlib.Path(val)
    if path.is_absolute() and imp in path.parts:
        # remove the root from the path, then join it to the main root
        return str(root.joinpath(*path.parts[1:]))
    return val


def pre_apply(hub, ctx):
    kwargs = ctx.get_arguments()
    ctx.cache["root_defaults"] = _insert_default_placeholders(kwargs["raw"])


def post_apply(hub, ctx):
    kwargs = ctx.get_arguments()
    _restore_raw_defaults(kwargs["raw"], ctx.cache["root_defaults"])
    root = _get_root(ctx.ret, kwargs["cli"])
    if root:
        _reroot_paths(ctx.cache["root_defaults"], root)
    _replace_default_placeholders(ctx.ret, ctx.cache["root_defaults"])

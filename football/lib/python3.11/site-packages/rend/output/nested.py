"""
Recursively display nested data
===============================

Example output::

    some key:
        ----------
        foo:
            ----------
            bar:
                baz
            dictionary:
                ----------
                abc:
                    123
                def:
                    456
            list:
                - Hello
                - World
"""
import unicodedata
from numbers import Number
from typing import Mapping

try:
    # Colorama handles ansi escape sequences on Windows properly
    # Other libraries result in KeyboardInterrupts on Windows in obscure edge-cases
    import colorama

    HAS_LIBS = (True,)
except ImportError as e:
    HAS_LIBS = False, str(e)


def __virtual__(hub):
    return HAS_LIBS


def to_str(s, encoding="utf-8", errors: str = "strict", normalize: bool = False):
    """
    Given str, bytes, bytearray, or unicode (py2), return str
    """

    def _normalize(st):
        try:
            return unicodedata.normalize("NFC", st) if normalize else st
        except TypeError:
            return st

    if not isinstance(encoding, (tuple, list)):
        encoding = (encoding,)

    if isinstance(s, str):
        return _normalize(s)

    exc = None
    if isinstance(s, (bytes, bytearray)):
        for enc in encoding:
            try:
                return _normalize(s.decode(enc, errors))
            except UnicodeDecodeError as err:
                exc = err
                continue
        # The only way we get this far is if a UnicodeDecodeError was
        # raised, otherwise we would have already returned (or raised some
        # other exception).
        raise exc  # pylint: disable=raising-bad-type
    raise TypeError(f"expected str, bytes, or bytearray not {type(s)}")


def to_unicode(
    hub, s, encoding="utf-8", errors: str = "strict", normalize: bool = False
):
    def _normalize(st):
        return unicodedata.normalize("NFC", st) if normalize else st

    if not isinstance(encoding, (tuple, list)):
        encoding = (encoding,)

    if isinstance(s, str):
        return _normalize(s)
    elif isinstance(s, (bytes, bytearray)):
        return _normalize(hub.output.nested.to_str(s, encoding, errors))
    raise TypeError(f"expected str, bytes, or bytearray not {type(s)}")


def ustring(hub, indent, color, msg, prefix="", suffix="", endc=colorama.Fore.RESET):
    indent *= " "
    fmt = "{0}{1}{2}{3}{4}{5}"

    try:
        return fmt.format(indent, color, prefix, msg, endc, suffix)
    except UnicodeDecodeError:
        try:
            return fmt.format(
                indent,
                color,
                prefix,
                hub.output.nested.to_unicode(msg),
                endc,
                suffix,
            )
        except UnicodeDecodeError:
            # msg contains binary data that can't be decoded
            return str(fmt).format(indent, color, prefix, msg, endc, suffix)


def recurse(hub, ret, indent, prefix, out):
    """
    Recursively iterate down through data structures to determine output
    """
    if isinstance(ret, bytes):
        try:
            ret = ret.decode()
        except UnicodeDecodeError:
            # ret contains binary data that can't be decoded
            pass
    elif isinstance(ret, tuple) and hasattr(ret, "_asdict"):
        # Turn named tuples into dictionaries for output
        ret = ret._asdict()

    if ret is None or ret is True or ret is False:
        out.append(
            hub.output.nested.ustring(
                indent, colorama.Fore.LIGHTYELLOW_EX, ret, prefix=prefix
            )
        )
    # Number includes all python numbers types
    #  (float, int, long, complex, ...)
    # use repr() to get the full precision also for older python versions
    # as until about python32 it was limited to 12 digits only by default
    elif isinstance(ret, Number):
        out.append(
            hub.output.nested.ustring(
                indent, colorama.Fore.LIGHTYELLOW_EX, repr(ret), prefix=prefix
            )
        )
    elif isinstance(ret, str):
        first_line = True
        for line in ret.splitlines():
            line_prefix = " " * len(prefix) if not first_line else prefix
            if isinstance(line, bytes):
                out.append(
                    hub.output.nested.ustring(
                        indent,
                        colorama.Fore.YELLOW,
                        "Not string data",
                        prefix=line_prefix,
                    )
                )
                break
            out.append(
                hub.output.nested.ustring(
                    indent, colorama.Fore.GREEN, line, prefix=line_prefix
                )
            )
            first_line = False
    elif isinstance(ret, (list, tuple)):
        color = colorama.Fore.GREEN
        for ind in ret:
            if isinstance(ind, (list, tuple, Mapping)):
                out.append(hub.output.nested.ustring(indent, color, "|_"))
                prefix = "" if isinstance(ind, Mapping) else "- "
                hub.output.nested.recurse(ind, indent + 2, prefix, out)
            else:
                hub.output.nested.recurse(ind, indent, "- ", out)
    elif isinstance(ret, Mapping):
        if indent:
            color = colorama.Fore.CYAN
            out.append(hub.output.nested.ustring(indent, color, "----------"))

        keys = ret.keys()
        color = colorama.Fore.CYAN
        for key in keys:
            val = ret[key]
            out.append(
                hub.output.nested.ustring(
                    indent, color, str(key), suffix=":", prefix=prefix
                )
            )
            hub.output.nested.recurse(val, indent + 4, "", out)
    return out


def display(hub, data):
    """
    Display ret data
    """
    with colorama.colorama_text():
        lines = hub.output.nested.recurse(ret=data, indent=0, prefix="", out=[])
    try:
        return "\n".join(lines)
    except UnicodeDecodeError:
        # output contains binary data that can't be decoded
        return "\n".join(  # future lint: disable=blacklisted-function
            [str(x) for x in lines]
        )

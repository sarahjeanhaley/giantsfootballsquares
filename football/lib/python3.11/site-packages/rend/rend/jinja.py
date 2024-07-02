"""
Render jinja data
"""
import base64
import os
import re
from typing import Any
from typing import List

import jinja2.ext
import jinja2.sandbox
import pop.contract

import rend.exc


def _base64encode(string):
    if string is None:
        return ""
    return base64.b64encode(string.encode()).decode()


def _base64decode(string):
    if string is None:
        return ""
    return base64.b64decode(string.encode()).decode()


class RenderSandboxedEnvironment(jinja2.sandbox.SandboxedEnvironment):
    """
    Jinja sandboxed environment that hide portion of hub
    """

    def __init__(self, safe_hub_refs: List[str], *args: Any, **kwargs: Any) -> None:
        self._safe_hub_refs = [re.compile(i) for i in safe_hub_refs]
        super().__init__(*args, **kwargs)

    def is_safe_attribute(self, obj: Any, attr: str, value: Any) -> bool:
        # Only allow safe hub references in Jinja environment
        if isinstance(value, pop.contract.ContractedAsync):
            return any(
                safe_hub_ref.match(value.ref) for safe_hub_ref in self._safe_hub_refs
            )

        return super().is_safe_attribute(obj, attr, value)


async def render(hub, data, params=None):
    """
    Render the given data through Jinja2
    """
    if params is None:
        params = {}

    env_args = {
        "extensions": [],
        "loader": jinja2.FileSystemLoader(os.getcwd()),
        "undefined": jinja2.StrictUndefined,
        "enable_async": True,
    }

    if hasattr(jinja2.ext, "do"):
        env_args["extensions"].append("jinja2.ext.do")
    if hasattr(jinja2.ext, "loopcontrols"):
        env_args["extensions"].append("jinja2.ext.loopcontrols")

    if hub.OPT.rend.enable_jinja_sandbox:
        jinja_env = RenderSandboxedEnvironment(  # nosec
            safe_hub_refs=hub.OPT.rend.jinja_sandbox_safe_hub_refs or [],
            **env_args,
        )
    else:
        jinja_env = jinja2.Environment(  # nosec
            **env_args,
        )

    jinja_env.filters["b64encode"] = _base64encode
    jinja_env.filters["b64decode"] = _base64decode

    if isinstance(data, bytes):
        data = data.decode("utf-8")

    try:
        template = jinja_env.from_string(data)
        ret = await template.render_async(params=params, hub=hub)
    except jinja2.exceptions.UndefinedError as exc:
        raise rend.exc.RenderException(f"Jinja variable: {exc.message}")
    except jinja2.exceptions.TemplateSyntaxError as exc:
        problem = []
        for arg in exc.args:
            if isinstance(arg, str):
                problem.append(arg)
            else:
                problem.append(str(arg))

        raise rend.exc.RenderException(f"Jinja syntax error: {' '.join(problem)}")
    return ret

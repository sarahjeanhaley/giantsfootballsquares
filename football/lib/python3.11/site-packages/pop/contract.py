"""
Contracts to enforce loader objects
"""
import asyncio
import functools
import inspect
import os
import re
import warnings
from collections import defaultdict
from types import ModuleType
from typing import Dict
from typing import Iterable
from typing import List

import pop.exc
import pop.hub
import pop.verify


class ContractedContext:
    """
    Contracted function calling context
    """

    def __init__(
        self,
        func: functools.partial,
        args: Iterable,
        kwargs: Dict,
        signature,
        ref,
        name,
        ret=None,
        cache=None,
    ):  # pylint: disable=too-many-arguments
        if cache is None:
            cache = {}

        self.func = func
        self.args = list(args)
        self.kwargs = kwargs
        self.signature = signature
        self.ref = ref
        self.__name__ = name
        self.ret = ret
        self.cache = cache

    def get_argument(self, name):
        """
        Return the value corresponding to a function argument after binding the contract context
        argument and keyword arguments to the function signature.
        """
        return self.get_arguments()[name]

    def get_arguments(self):
        """
        Return a dictionary of all arguments that will be passed to the function and their
        values, including default arguments.
        """
        if "__bound_signature__" not in self.cache:
            try:
                handle_param_aliases(self.signature.parameters, self.kwargs)
                self.cache["__bound_signature__"] = self.signature.bind(
                    *self.args, **self.kwargs
                )
            except TypeError as e:
                for frame in inspect.trace(0):
                    if frame.function == "bind" and frame.filename.endswith(
                        os.sep + "inspect.py"
                    ):
                        raise pop.exc.BindError(e)
                raise
            # Apply any default values from the signature
            self.cache["__bound_signature__"].apply_defaults()
        return self.cache["__bound_signature__"].arguments


def load_contract(
    contracts: "pop.hub.Sub",
    default_contracts: List[str],
    mod: ModuleType,
    name: str,
) -> List["pop.lodaer.LoadedMod"]:
    """
    return a Contract object loaded up
    Dynamically create the correct Contracted type
    :param contracts: Contracts functions to add to the sub
    :param default_contracts: The contracts that have been marked as defaults
    :param mod: A loader module
    :param name: The name of the module to get from the loader
    """
    raws = []
    if not contracts:
        return raws
    loaded_contracts = []
    if hasattr(contracts, name):
        loaded_contracts.append(name)
        raws.append(getattr(contracts, name))
    if hasattr(contracts, "init"):
        if "init" not in loaded_contracts:
            loaded_contracts.append("init")
            raws.append(getattr(contracts, "init"))
    if default_contracts:
        for contract in default_contracts:
            if contract in loaded_contracts:
                continue
            loaded_contracts.append(contract)
            raws.append(getattr(contracts, contract))
    if hasattr(mod, "__contracts__"):
        cnames = getattr(mod, "__contracts__")
        if not isinstance(cnames, (list, tuple)):
            cnames = cnames.split(",")
        for cname in cnames:
            if cname in contracts:
                if cname in loaded_contracts:
                    continue
                loaded_contracts.append(cname)
                raws.append(getattr(contracts, cname))
    return raws


class Wrapper:
    def __init__(self, func: functools.partial, ref: str, name: str):
        """
        :param func: The contracted function to call
        :param ref: The reference to the function on the hub
        :param name: An alias for the function
        """
        self.__dict__.update(
            getattr(func, "__dict__", {})
        )  # do this first so we later overwrite any conflicts
        self.func = func
        self.ref = ref
        self.__name__ = name
        try:
            self.signature = inspect.signature(self.func)
        except ValueError:
            # inspect.signature raises a ValueError only when a signature could not be provided.
            # Some callables may not be introspectable in certain implementations of Python.
            # For example, in CPython, some built-in functions defined in C provide no metadata about their arguments.
            self.signature = None
        self._sig_errors = []
        self.__wrapped__ = func

    def __call__(self, *args, **kwargs):
        self.func(*args, **kwargs)

    def __repr__(self):
        return "<{} func={}.{}>".format(
            self.__class__.__name__, self.func.__module__, self.__name__
        )


class Contracted(Wrapper):
    """
    This class wraps functions that have a contract associated with them
    and executes the contract routines
    """

    def __init__(
        self,
        hub: "pop.hub.Hub",
        contracts: List["pop.hub.Sub"],
        func: functools.partial,
        ref: str,
        name: str,
        implicit_hub: bool = True,
        param_aliases: dict = None,
    ):
        """
        :param hub: The redistributed pop central hub
        :param contracts: Contracts functions to add to the sub
        :param func: The contracted function to call
        :param ref: The reference to the function on the hub
        :param name: An alias for the function
        :param implicit_hub: True if a hub should be implicitly injected into the "call" method
        :param param_aliases: A dictionary that maps parameters to a set of its aliases
        """
        super().__init__(func, ref, name)
        self.hub = hub
        self.contracts = contracts or []
        self.implicit_hub = implicit_hub
        self._load_contracts()
        self.param_aliases = param_aliases or {}

    def _get_contracts_by_type(self, contract_type: str = "pre") -> List[Wrapper]:
        """
        :param contract_type: One of "call", "pre", "post", or "sig"
        """
        matches = []
        fn_contract_name = f"{contract_type}_{self.__name__}"
        for contract in self.contracts:
            if hasattr(contract, fn_contract_name):
                matches.append(getattr(contract, fn_contract_name))
            if hasattr(contract, contract_type):
                matches.append(getattr(contract, contract_type))

        if contract_type == "post":
            matches.reverse()

        return matches

    def _load_contracts(self):
        # TODO:
        # if Contracted - only allow regular pre/post
        # if ContractedAsync - allow coroutines and functions
        # if ContractedAsyncGen - allow coroutines and functions

        self.contract_functions = {
            "pre": self._get_contracts_by_type("pre"),
            "call": self._get_contracts_by_type("call")[:1],
            "post": self._get_contracts_by_type("post"),
        }
        self._has_contracts = sum(len(l) for l in self.contract_functions.values()) > 0

    def __call__(self, *args, **kwargs):
        if self.implicit_hub:
            args = (self.hub,) + args

        if self.signature:
            handle_param_aliases(self.signature.parameters, kwargs)

        if not self._has_contracts:
            return self.func(*args, **kwargs)

        contract_context = ContractedContext(
            self.func, args, kwargs, self.signature, self.ref, self.__name__
        )

        for fn in self.contract_functions["pre"]:
            pre_ret = fn(contract_context)
            self.hub.pop.contract.process_pre_result(pre_ret, fn, self)
        if self.contract_functions["call"]:
            ret = self.contract_functions["call"][0](contract_context)
        else:
            ret = self.func(*contract_context.args, **contract_context.kwargs)
        for fn in self.contract_functions["post"]:
            contract_context.ret = ret
            post_ret = fn(contract_context)
            if post_ret is not None:
                ret = post_ret

        return ret

    def __getstate__(self):
        return dict(
            hub=self.hub,
            ref=self.ref,
            name=self.__name__,
            implicit_hub=self.implicit_hub,
            contracts=self.contracts,
            param_aliases=self.param_aliases,
        )

    def __setstate__(self, state):
        hub = state["hub"]
        ref = state["ref"]
        name = state["name"]
        func = hub[ref][name].func
        self.__init__(
            hub=hub,
            func=func,
            ref=ref,
            name=name,
            implicit_hub=state["implicit_hub"],
            contracts=state["contracts"],
            param_aliases=state["param_aliases"],
        )


class ContractedAsyncGen(Contracted):
    async def __call__(self, *args, **kwargs):
        if self.implicit_hub:
            args = (self.hub,) + args
        if not self._has_contracts:
            async for chunk in self.func(*args, **kwargs):
                yield chunk
            return
        contract_context = ContractedContext(
            self.func, args, kwargs, self.signature, self.ref, self.__name__
        )

        for fn in self.contract_functions["pre"]:
            pre_ret = fn(contract_context)
            if asyncio.iscoroutine(pre_ret):
                self.hub.pop.contract.process_pre_result(await pre_ret, fn, self)
        chunk = None
        if self.contract_functions["call"]:
            async for chunk in self.contract_functions["call"][0](contract_context):
                yield chunk
        else:
            async for chunk in self.func(
                *contract_context.args, **contract_context.kwargs
            ):
                yield chunk
        ret = chunk
        for fn in self.contract_functions["post"]:
            contract_context.ret = ret
            if isinstance(fn, ContractedAsync):
                post_ret = await fn(contract_context)
            else:
                post_ret = fn(contract_context)
            if post_ret is not None:
                ret = post_ret


class ContractedAsync(Contracted):
    async def __call__(self, *args, **kwargs):
        if self.implicit_hub:
            args = (self.hub,) + args
        if not self._has_contracts:
            return await self.func(*args, **kwargs)
        contract_context = ContractedContext(
            self.func, args, kwargs, self.signature, self.ref, self.__name__
        )

        for fn in self.contract_functions["pre"]:
            pre_ret = fn(contract_context)
            if asyncio.iscoroutine(pre_ret):
                self.hub.pop.contract.process_pre_result(await pre_ret, fn, self)
        if self.contract_functions["call"]:
            ret = await self.contract_functions["call"][0](contract_context)
        else:
            ret = await self.func(*contract_context.args, **contract_context.kwargs)
        for fn in self.contract_functions["post"]:
            contract_context.ret = ret
            if isinstance(fn, ContractedAsync):
                post_ret = await fn(contract_context)
            else:
                post_ret = fn(contract_context)
            if post_ret is not None:
                ret = post_ret

        return ret


def _order(contracts: List["pop.loader.LoadedMod"]) -> List["pop.loader.LoadedMod"]:
    """
    Take a list of contracts and put them in a determinate order
    """
    # These will hold our contracts, divided by whether their __order__ is positive, negative, or not specified.
    positive_ordered_contracts = []
    negative_ordered_contracts = []
    unordered_contracts = []
    seen_order = defaultdict(list)

    for contract in contracts:
        if not hasattr(contract, "__order__"):
            unordered_contracts.append(contract)
        else:
            order = int(contract.__order__)
            if -1 < order < 1:
                raise ValueError(
                    f"Contracts can only have an __order__ with a absolute value greater than or equal to 1"
                )

            seen_order[order].append(contract)

            if order >= 0:
                positive_ordered_contracts.append((order, contract))
            else:
                negative_ordered_contracts.append((order, contract))

    # Throw a warning if two contracts have the same order
    for order, contract_list in seen_order.items():
        if len(contract_list) > 1:
            warnings.warn(
                f"Multiple contracts share an order of '{order}': {', '.join([contract.__name__ for contract in contract_list])}",
                SyntaxWarning,
            )

    # Sort contracts with positive orders and negative orders
    positive_ordered_contracts.sort(key=lambda x: x[0])
    negative_ordered_contracts.sort(key=lambda x: x[0])

    # Contracts with positive orders come first
    determinate_contracts = [contract for _, contract in positive_ordered_contracts]

    # Contracts without an order come next
    determinate_contracts.extend(unordered_contracts)

    # Contracts with negative orders come last
    determinate_contracts.extend(contract for _, contract in negative_ordered_contracts)

    immutable_order = tuple(c._attrs["__name__"] for c in determinate_contracts)

    # Now that we have a determinate order for contracts, run their "__verify_order__" function if one exists
    for contract in determinate_contracts:
        if hasattr(contract, "__verify_order__"):
            result = contract.__verify_order__(immutable_order)

            if isinstance(result, tuple):
                result, comment = result
            else:
                comment = None

            if not result:
                raise ValueError(
                    f"'{contract.__name__}' failed to verify its order: {comment}"
                )

    return determinate_contracts


def create_contracted(
    hub: "pop.hub.Hub",
    contracts: List["pop.loader.LoadedMod"],
    func: functools.partial,
    ref: str,
    name: str,
    implicit_hub: bool = True,
) -> Contracted:
    """
    Dynamically create the correct Contracted type
    :param hub: The redistributed pop central hub
    :param contracts: Contracts functions to add to the sub
    :param func: The contracted function to call
    :param ref: The reference to the function on the hub
    :param name: The name of the module to get from the loader
    :param implicit_hub: True if a hub should be implicitly injected into the "call" method
    """

    if asyncio.iscoroutinefunction(func):
        return ContractedAsync(hub, contracts, func, ref, name, implicit_hub)
    elif inspect.isasyncgenfunction(func):
        return ContractedAsyncGen(hub, contracts, func, ref, name, implicit_hub)
    else:
        return Contracted(hub, contracts, func, ref, name, implicit_hub)


def handle_param_aliases(param_signature: dict, kwargs: dict):
    """
    Check for a function annotation with the pattern "alias=_____"
    If it exists, then exchange the parameter alias for the actual parameter name.
    This way, a caller can use parameter names that clash with python internals,
    but the function code can use a safe alternative.

    I.E.

    .. code-block:: python

        def my_func(hub, id_: "alias=id"):
            # This function can be called with hub._.my_func(id="") or hub._.my_func(id_="")
            # Either way, the "id_" parameter will be populated
            ...


    This can also be done with type-hinting:

    I.E.

    .. code-block:: python

        def my_func(hub, id_: (str, "alias=id")):
            # This function can be called with hub._.my_func(id="") or hub._.my_func(id_="")
            # Either way, the "id_" parameter will be populated
            ...
    """
    if not kwargs:
        return
    if not param_signature:
        return

    for param, signature in param_signature.items():
        # No need to check for an alias, the named parameter is already there
        if param in kwargs:
            continue
        match = re.findall(r"alias=(\w+)", str(signature.annotation))
        for alias in match:
            if alias in kwargs:
                kwargs[param] = kwargs.pop(alias)


class Partial:
    """
    A partial function that can be used for multiprocessing
    """

    def __init__(self, synchronous_function: Contracted, *args, **kwargs):
        self.func = synchronous_function
        self.args = args
        self.kwargs = kwargs

    def __call__(self):
        ret = self.func(*self.args, **self.kwargs)
        # We can't pickle a coroutine, so async functions need to finish here
        # if this is executed in a forked process, we can't guarantee a loop exists
        if asyncio.iscoroutine(ret):
            loop = asyncio.new_event_loop()
            try:
                while asyncio.iscoroutine(ret):
                    ret = loop.run_until_complete(ret)
            finally:
                loop.close()
        return ret

    def __getstate__(self):
        return {
            "func": self.func,
            "args": self.args,
            "kwargs": self.kwargs,
        }

    def __setstate__(self, state):
        self.func = state["func"]
        self.args = state["args"]
        self.kwargs = state["kwargs"]

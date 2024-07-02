from typing import Callable
from typing import Tuple

import pop.exc
from pop.contract import Contracted


def __init__(hub):
    # Configure this to be True in your plugin to make use of the feature
    hub.pop.contract.RAISE_ON_PRE_CONTRACT_FAILURE = False


def process_pre_result(
    hub, pre_ret: Tuple[bool, str] or bool, pre: Callable, cn: Contracted
):
    if isinstance(pre_ret, Tuple):
        pre_ret, msg = pre_ret
    else:
        msg = f"Pre contract '{pre.__name__}' failed for function '{cn.func.__name__}'"

    # If the return of "pre" is "False" then raise an error
    if pre_ret is False and hub.pop.contract.RAISE_ON_PRE_CONTRACT_FAILURE:
        raise pop.exc.PreContractFailed(msg)

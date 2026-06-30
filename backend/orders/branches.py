from enum import Enum
from typing import Optional

from config import (
    TERMINAL_ID_GROUP_MALYSHAVA,
    TERMINAL_ID_GROUP_SUH,
)


class BranchCode(str, Enum):
    MALYSHAVA = "malyshava"
    SUH = "suh"


TERMINAL_GROUP_BY_BRANCH: dict[BranchCode, Optional[str]] = {
    BranchCode.MALYSHAVA: TERMINAL_ID_GROUP_MALYSHAVA,
    BranchCode.SUH: TERMINAL_ID_GROUP_SUH,
}


def resolve_terminal_group_id(branch_code: BranchCode) -> str:
    terminal_group_id = TERMINAL_GROUP_BY_BRANCH.get(branch_code)

    if not terminal_group_id:
        raise ValueError(
            f"Для филиала {branch_code.value} не настроен терминал iiko."
        )

    return terminal_group_id

"""Handlers for groups management
"""
from typing import List


def is_authorized_for_group(authorized_groups: List[str], group: str) -> bool:
    """Check `authorized group` list have access to manage `group`
    """
    return "staff" in authorized_groups or f"{group}.staff" in authorized_groups

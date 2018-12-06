"""Handlers for groups management
"""
from typing import List


def is_authorized_for_group(authorized_groups: List[str], group: str) -> bool:
    """Check `authorized group` list have access to manage `group`
    """
    return "staff" in authorized_groups or f"{group}.staff" in authorized_groups


def is_root(authorized_groups: List[str]) -> bool:
    """Check staff is in group list
    """
    return "staff" in authorized_groups


def is_parent_group_staff(authorized_groups: List[str], group: str) -> bool:
    """Verify if group parent is in authorized_groups
    """
    parent_group = group.rsplit(".", 1)[0]
    return f"{parent_group}.staff" in authorized_groups


def is_authorized_for_group_create(authorized_groups: List[str], group: str) -> bool:
    """Only root staff or parent group staff can create group
    """
    return is_root(authorized_groups) or is_parent_group_staff(authorized_groups, group)

"""Small UI guards for ticket creation; the supervisor still handles routing."""

import re


def asks_to_create_ticket(message: str) -> bool:
    text = message.strip()
    if re.search(r"(不要|无需|暂不|先别).{0,8}(创建|新建|提交|开|建).{0,10}工单", text):
        return False
    if re.match(r"^(如何|怎么|怎样).{0,12}(创建|新建).{0,5}工单", text):
        return False
    return bool(re.search(r"(创建|新建|提交|开|建).{0,12}工单|工单.{0,6}(创建|新建|提交)", text))


def is_confirmation(message: str) -> bool:
    return message.strip() in {"确认", "确认创建", "确认建单", "确认创建工单"}


def is_cancellation(message: str) -> bool:
    return message.strip() in {"取消", "取消创建", "取消建单", "取消创建工单"}

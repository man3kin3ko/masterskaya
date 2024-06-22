from __future__ import annotations
from .schemas import OrderFormRequestSchema


def build_new_order_message(new_order: OrderFormRequestSchema, new_order_uuid: str, master_name: str) -> str:
    return (
        f'Привет {master_name}! Поступил новый заказ.\n\n'
        f'Контакт: {new_order.contact} ({new_order.soc_type.value}).\n\nМодель камеры {new_order.model}.\n\n'
        f'Описание проблемы: {new_order.problem}.\n\n'
        f'Ключ для доступа к ссылке: {new_order_uuid}.'
    )

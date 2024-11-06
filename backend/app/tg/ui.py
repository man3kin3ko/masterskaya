from telegram import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    )
from ..db import Status, SpareType
from dataclasses import dataclass


@dataclass(frozen=True)
class Routes:
    menu: str = "^\/menu\/$"
    spares: str = "^\/spares\/$"
    spares_subtype: str = "^\/spares\/(mechanical|electrical)\/$"
    spare: str = "^\/spare\/(mechanical|electrical)\/\d+\/$"
    spare_upload: str = "^\/spare\/(mechanical|electrical)\/\d+\/upload\/$"
    spare_download: str = "^\/spare\/(mechanical|electrical)\/\d+\/download\/$"

    orders: str = "^\/orders\/[0-9]{,256}\/{,1}$"
    order: str = "^\/order\/[0-9a-f\-]{36}\/$"
    order_change: str = "^\/order\/[0-9a-f\-]{36}\/[a-zA-Z\_]{,64}\/$"

    cameras: str = "^\/cameras\/$"


class Route:
    def __init__(self, uri):
        self.parts = uri.strip("/").split("/")

    def back(self):
        return f"/{self.route[0]}/{self.page - 1 if self.page > 1 else 1}"

    def next(self):
        return f"/{self.route[0]}/{self.page + 1}"



class InlineKeyboardUI():
    def __init__(self, rows):
        self.rows = rows
        self.route = None

    def from_route(self, route):
        self.route = route
        self.page = 1 # why??
        return self

    def set_route(self, route):
        self.route = route.lstrip("/").split("/")
        if (len(self.route) > 2):
            self.page = int(self.route[2])

    def create(self):
        return InlineKeyboardMarkup(self.rows)

    def next(self):
        return f"/{self.route[0]}/{self.page + 1}"

    def back(self):
        if self.route[0] == "order":
            return "/orders/"
        if not (self.route[0] == "spare" and len(route) <= 3):
            return f"/spares/"
        return f"/{self.route[0]}/{self.page - 1 if self.page > 1 else 1}"


class InlineKeyboardUIBuilder:
    def __init__(self, max_per_page):
        self.max_per_page = max_per_page
        self.reset()
        self._menu_btn = InlineKeyboardButton(text="Меню", callback_data="/menu/")

    def reset(self) -> None:
        self._product = InlineKeyboardUI([])

    def init(self, product):
        self._product = product

    @property
    def product(self) -> InlineKeyboardUI:
        assert len(self._product.rows[0]) <= self.max_per_page + 1
        product = self._product.create()
        self.reset()
        return product

    def accept_order(self, uniq_link):
        self.add_row([InlineKeyboardButton(
            "Принять заказ", 
            callback_data=f"/order/{uniq_link}/{Status.ACCEPTED.value}/"
            )])
    
    def add_button(self, text, callback):
        self.add_row([InlineKeyboardButton(text=text, callback_data=callback)])

    def add_row(self, row):
        self._product.rows.append(row)

    def add_route(self, route):
        self._product.set_route(route)

    def add_menu_btn(self):
        self._product.rows.append([self._menu_btn])

    def add_back_btn(self):
        self._product.rows.append([InlineKeyboardButton(text="⬅️", callback_data=self._product.back())])

    def add_pager(self):
        self._product.rows.append(
            [
                InlineKeyboardButton(text="⬅️", callback_data=self._product.back()),
                self._menu_btn,
                InlineKeyboardButton(text="➡️", callback_data=self._product.next()),
            ]
        )
    
    def make_menu(self):
        self.add_route("/menu")
        self.add_row(
                [InlineKeyboardButton(text="Мои заказы", callback_data=f"/orders/")]
            )
        self.add_row(
                [InlineKeyboardButton(text="Запчасти", callback_data=f"/spares/")]
            )

    def add_status_switch(self, uuid, current_status: Status):
        row  = [i for i in Status if i.name != current_status.name and i.name != Status.ORDERED.name]
        self.add_row(list(map(lambda i: InlineKeyboardButton(text=str(i), callback_data=f"/order/{uuid}/{i.value}/"), row)))
        
    def make_spares(self):
        self.add_route(f"/spares/")
        self.add_row(
                    [
                        InlineKeyboardButton(
                            text="Электроника",
                            callback_data=f"/spares/{SpareType.ELECTRIC.value}/",
                        )
                    ]
                )
        self.add_row(
                    [
                        InlineKeyboardButton(
                            text="Механика",
                            callback_data=f"/spares/{SpareType.MECHA.value}/",
                        )
                    ]
                )
        self.add_menu_btn()

    def add_file_toggle(self, categ_id):
        self.add_row([
            InlineKeyboardButton(
                text="Скачать",  
                callback_data=f"/spare/{categ_id}/download/",
                ),
            InlineKeyboardButton(
                text="Загрузить",  
                callback_data=f"/spare/{categ_id}/upload/",
                ),
        ])


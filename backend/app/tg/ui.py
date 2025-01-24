import re
from dataclasses import dataclass, fields
from telegram import (
    InlineKeyboardButton, 
    InlineKeyboardMarkup, 
    )
from app.db import Status
from app.utils import flatten_dicts

class Route():

    _registred = None
    
    def __init__(self, uri):
        self.uri = uri
        self.regex = None
        self.groups = []
        self.parts = []

    def parse(self):
        for i in fields(self):
            if i.name == "base":
                continue
            regex = re.compile(i.default)
            groups = re.findall(regex, self.uri)
            if groups:
                self.regex = regex
                self.groups = groups[0] if type(groups[0]) == type(tuple()) else tuple(groups)
                self.parts = self.uri.split("/")
                return self

    @property
    def match(self):
        return self.groups[0]

    @classmethod
    def from_uri(cls, uri):
        for i in cls.__subclasses__():
            if uri.startswith(str(i.base)):
                return i(uri).parse()
        raise Exception("No suitable subclass has found")

    def _swipe_page(self, negative=True):
        new_page_n = int(self.match) + (-1 * int(negative))
        if new_page_n <= 0: #werkzeug raises 404 error
            new_page_n = 1
        self.uri = self.base + f"page/{new_page_n}"

        return self

    def back(self):
        try:
            self._swipe_page()
        except (TypeError, ValueError):
            self.uri = "/".join(self.parts[:-2]) + "/"
            self.parts = self.parts[:-1]
        return self

    def next(self):
        self._swipe_page(negative=False)
        return self

    @classmethod
    def as_dict(cls):
        _fields = [(i.name, i.default) for i in fields(cls) if i.name != "base"]
        return dict(_fields)
    
    @classmethod
    @property
    def registred(cls):
        if cls._registred is None:
            cls._registred = flatten_dicts([i.as_dict() for i in cls.__subclasses__()])
        return cls._registred


@dataclass
class MenuRoutes(Route):
    base: str = "/menu/"
    menu: str = "^\/menu\/$"
    def __init__(self, uri):
        super().__init__(uri)


@dataclass
class SparesRoutes(Route):
    base = "/spare/"
    spares: str = "^\/spare\/{,1}$"
    spares_page: str = "^\/spare\/(mechanical|electrical)\/page\/([0-9]{,256})\/{,1}$"
    spare: str = "^\/spare\/(mechanical|electrical)\/item\/(\d+)\/$"
    spare_upload: str = "^\/spare\/(mechanical|electrical)\/item\/(\d+)\/upload\/$"
    spare_download: str = "^\/spare\/(mechanical|electrical)\/item\/(\d+)\/download\/$"
    def __init__(self, uri):
        super().__init__(uri)
        self.base += self.subtype + "/" if self.subtype else ""

    @property
    def at_page(self):
        return self.regex.pattern == self.spares_page

    @property
    def at_item(self):
        return self.regex.pattern == self.spare

    @property
    def subtype(self):
        return self.groups[0] if self.groups else ""
    
    @property
    def id(self):
        return self.groups[1]

    @property
    def at_entry(self):
        return self.regex.pattern == self.spares

    def next(self):
        if self.at_page:
            # использовать именованные группы
            self.uri = self.base + f"{self.subtype}/page/{int(self.id) + 1}"
            return self
        return super().back()

    def back(self):
        if self.at_entry:
            return Route.from_uri("/menu/")
        if self.at_item:
            self.uri = self.base + f"{self.subtype}/page/1"
            return self
        return super().back()


@dataclass
class OrdersRoutes(Route):
    base: str = "/order/"
    orders: str = "^\/order\/page\/([0-9]{,256})\/{,1}$"
    order: str = "^\/order\/item\/([0-9a-f\-]{36})\/$"
    order_change: str = "^\/order\/item\/([0-9a-f\-]{36})\/([a-zA-Z\_]{,64})\/$"
    def __init__(self, uri):
        super().__init__(uri)

    @property
    def at_item(self):
        return (self.regex.pattern == self.order_change or self.regex.pattern == self.order)

    @property
    def status(self):
        if self.regex.pattern == self.order_change:
            return Status(self.groups[1])

    @property
    def uuid(self):
        is_item = self.regex.pattern == self.order
        is_item_change = self.regex.pattern == self.order_change
        if is_item or is_item_change:
            return self.groups[0]
    
    def back(self):
        if self.at_item:
            self.uri = self.base + "page/1" # idk как тут запоминать страницу. присрать замыкания?
            return self
        return super().back()


class InlineKeyboardUI():
    def __init__(self, rows, route: Route = None):
        self.rows = rows
        self.route = route

    def create(self):
        return InlineKeyboardMarkup(self.rows)

    def next(self):
        return self.route.back().uri

    def back(self):
        return self.route.back().uri


class InlineKeyboardUIBuilder:
    def __init__(self, max_per_page, route:Route):
        self.route = route
        self._product = InlineKeyboardUI([], route)
        self.max_per_page = max_per_page
        self._menu_btn = InlineKeyboardButton(text="Меню", callback_data="/menu/")

    @classmethod
    def from_flask_update(self, max_per_page, uuid):
        builder = InlineKeyboardUIBuilder(max_per_page, Route.from_uri(f"/order/item/{uuid}/accepted/"))
        builder.add_row([InlineKeyboardButton(
            "Принять заказ", 
            callback_data=builder.route.uri
            )])
        return builder

    @property
    def product(self) -> InlineKeyboardUI:
        return self._product.create()

    def add_button(self, text, callback):
        self.add_row([InlineKeyboardButton(text=text, callback_data=callback)])

    def add_row(self, row):
        self._product.rows.append(row)

    def add_route(self, route: Route):
        self._product.route = route

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
        self.add_route(Route.from_uri("/menu/"))
        self.add_row(
                [InlineKeyboardButton(text="Мои заказы", callback_data=f"/order/page/1/")]
            )
        self.add_row(
                [InlineKeyboardButton(text="Запчасти", callback_data=f"/spare/")]
            )

    def add_status_switch(self, uuid, current_status: Status):
        row  = [i for i in Status if i.name != current_status.name and i.name != Status.ordered]
        self.add_row(list(map(lambda i: InlineKeyboardButton(text=str(i), callback_data=f"/order/item/{uuid}/{i.value}/"), row)))
        
    def make_spares(self):
        self.add_route(Route.from_uri("/spare/"))
        self.add_row(
                    [
                        InlineKeyboardButton(
                            text="Электроника",
                            callback_data=f"/spare/electrical/page/1",
                        )
                    ]
                )
        self.add_row(
                    [
                        InlineKeyboardButton(
                            text="Механика",
                            callback_data=f"/spare/mecha/page/1",
                        )
                    ]
                )
        self.add_back_btn()

    def add_file_toggle(self, categ_id):
        self.add_row([
            InlineKeyboardButton(
                text="Скачать",  
                callback_data=f"/spare/item/{categ_id}/download/",
                ),
            InlineKeyboardButton(
                text="Загрузить",  
                callback_data=f"/spare/item/{categ_id}/upload/",
                ),
        ])


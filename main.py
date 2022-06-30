"""Мессенджер на Python (клиент)."""
# -*- coding: utf-8 -*-

import tkinter as tk

from json import dumps
from json import loads
from math import ceil
from math import floor
from socket import AF_INET
from socket import SOCK_DGRAM
from socket import socket
from threading import Thread
from time import sleep
from tkinter import ttk


class Window:
    """Класс окна."""

    def __init__(self, tk_window: tk.Tk) -> None:
        """Инициализация окна.

        Аргументы:
            tk_window:  Окно Tkinter.
        """
        self.tk_window: tk.Tk = tk_window
        self.elements: dict = {}

    def place(self, id_: str, element, *args, **kwargs) -> None:
        """Размещает объект element.

        Аргументы:
            id_:        Уникальный идентификатор элемента.
            element:    Элемент, который необходимо разместить.
            *args:      Аргументы element.place().
            **kwargs:   Позиционные аргументы element.place().
        """
        if id_ in self.elements:
            raise ValueError

        self.elements[id_] = element
        element.place(*args, **kwargs)

    def pack(self, id_: str, element, *args, **kwargs) -> None:
        """Размещает объект element.

        Аргументы:
            id_:        Уникальный идентификатор элемента.
            element:    Элемент, который необходимо разместить.
            *args:      Аргументы element.pack().
            **kwargs:   Позиционные аргументы element.pack().
        """
        if id_ in self.elements:
            raise ValueError

        self.elements[id_] = element
        element.pack(*args, **kwargs)

    def __getattribute__(self, id_: str):
        """Получает элемент по его ID.

        Аргументы:
            id_:    Уникальный идентификатор элемента.

        Возвращаемое значение: Элемент.
        """
        if id_ in ["pack", "place", "tk_window", "elements"]:
            return object.__getattribute__(self, id_)

        return object.__getattribute__(self, "elements")[id_]


class MessengerClient:
    """Основной класс."""

    MAIN_BACKGROUND = "#3a3a3a"
    SELECT_FOREGROUND = "#555"
    MAIN_FOREGROUND = "#dfdfdf"
    SECOND_BACKGROUND = "#c9c9c9"
    THIRD_BACKGROUND = "#bfbfbf"
    MESSAGE_BACK_COLOR = "#c5fad5"
    MESSAGE_FORE_COLOR = "#444"
    MESSAGE_BACK_COLOR2 = "#eee"
    MESSAGE_FORE_COLOR2 = "#444"
    _RECEIVE_SLEEP_TIME = 1 / 60

    def __init__(self) -> None:
        """Инициализация класса."""
        self.root = None
        self.win: Window = Window(self.root)
        self._sock: socket = socket(AF_INET, SOCK_DGRAM)
        self._sock.connect(("127.0.0.1", 7505))
        self.__sended: list = []
        self.__received: list = []
        self._logins: dict = {}
        self._userid_selected: int = -1
        self.last_height: int = -1

        Thread(target=self.receive, daemon=True).start()

        self.main()

    @staticmethod
    def show_error(title: str, message: str) -> None:
        """Показывает ошибку.

        Аргументы:
            title:      Заголовок ошибки.
            message:    Описание ошибки.
        """
        title = f"ОШИБКА: {title}"
        ltitle = len(title)
        lmessage = len(message)
        mlen = max(ltitle, lmessage)
        dtitle = (mlen - ltitle) / 2
        dmessage = (mlen - lmessage) / 2
        print("-" * (mlen + 4))
        print(f"|{' ' * (floor(dtitle) + 1)}{title}\
{' ' * (ceil(dtitle) + 1)}|")
        print("-" * (mlen + 4))
        print(f"|{' ' * (floor(dmessage) + 1)}{message}\
{' ' * (ceil(dmessage) + 1)}|")
        print("-" * (mlen + 4))

    def send(self, message: str) -> None:
        """Отправляет сообщение message на сервер.

        Аргументы:
            message:    Сообщение.
        """
        self._sock.send(dumps(message).encode("utf8"))

    @staticmethod
    def create_round_rectangle(
        cnv,
        px1,
        py1,
        px2,
        py2,
        radius,
        ign1=False,
        ign2=False,
        **kwargs
    ) -> int:
        """Создаёт скруглённый прямоугольник.

        Аргументы:
            cnv:    Холст Tkinter.
            px1:    Левая точка прямоугольника.
            py1:    Верхняя точка прямоугольника.
            px2:    Правая точка прямоугольника.
            py2:    Нижняя точка прямоугольника.
            radius: Радиус скругления.
            kwargs: Дополнительные аргументы cnv.create_polygon().

        Возвращаемое значение: ID Скруглённого прямоугольника на холсте.
        """
        points = [
            px1 + radius, py1,
            px1 + radius, py1,
            px2 - radius, py1,
            px2 - radius, py1,
            px2, py1,
            px2, py1 + radius,
            px2, py1 + radius,
            px2, py2 - radius,
            px2, py2 - radius,
            *((px2, py2, px2, py2) if ign1 else (px2, py2)),
            px2 - radius, py2,
            px2 - radius, py2,
            px1 + radius, py2,
            px1 + radius, py2,
            *((px1, py2, px1, py2) if ign2 else (px1, py2)),
            px1, py2 - radius,
            px1, py2 - radius,
            px1, py1 + radius,
            px1, py1 + radius,
            px1, py1
        ]

        return cnv.create_polygon(points, **kwargs, smooth=True)

    def user_selected(self) -> None:
        """Обработчик события выбора пользователя.

        Аргументы:
            wid:    Виджет Listbox Tkinter.
        """
        try:
            listbox = self.win.userlist
        except KeyError:
            return

        sel = listbox.curselection()

        if len(sel) == 0:
            return

        inv_logins = {val: key for key, val in self._logins.items()}
        user_id = int(inv_logins[listbox.get(sel[0])[1:]])

        if user_id != self._userid_selected:
            self._userid_selected = user_id

            messages = []

            for smsg in self.__sended:
                if smsg[3] != self._userid_selected:
                    continue

                messages.append(smsg)

            for rmsg in self.__received:
                if rmsg[1] != self._userid_selected:
                    continue

                messages.append(rmsg)

            messages.sort(key=lambda message: message[0])

            cnv = self.win.messages
            cwh = cnv.winfo_width()
            chg = cnv.winfo_height()

            cnv.delete("all")

            offset = chg

            for msg in messages[::-1]:
                sended = msg[3] == self._userid_selected

                text = cnv.create_text(
                    cwh - 5 if sended else 5,
                    offset,
                    text=msg[2],
                    anchor=tk.NE if sended else tk.NW,
                    fill=self.MESSAGE_FORE_COLOR if sended else self.
                    MESSAGE_FORE_COLOR2,
                    font="Arial 16",
                    width=cwh - 20
                )
                text_bbox = cnv.bbox(text)

                diff = text_bbox[1] - text_bbox[3] - 20
                cnv.move(text, 0, diff)
                text_bbox = cnv.bbox(text)

                rect = self.create_round_rectangle(
                    cnv,
                    text_bbox[0] - 5,
                    text_bbox[1] - 5,
                    text_bbox[2] + 5,
                    text_bbox[3] + 5,
                    15,
                    fill=self.MESSAGE_BACK_COLOR if sended else self.
                    MESSAGE_BACK_COLOR2,
                    width=0,
                    ign1=sended,
                    ign2=not sended
                )
                cnv.tag_lower(rect)

                offset += diff

        cnv.configure(scrollregion=cnv.bbox("all"))

    def resize(self, event) -> None:
        """Обработчик изменения размера окна."""
        if event.height == self.last_height:
            return

        self.last_height = event.height

        try:

            listbox = self.win.userlist

            if len(listbox.curselection()) > 0:
                self._userid_selected = -1
                listbox.event_generate("<<ListboxSelect>>")
        except KeyError:
            pass

    def receive(self) -> None:
        """Получает сообщения от сервера."""
        while True:
            jdata = self._sock.recv(70000)
            data = loads(jdata.decode("utf8"))
            com = data[0]

            if com == "register_status":
                status = data[1]

                if status == 0:
                    self.send(["get_account_data"])
                elif status == 1:
                    self.show_error(
                        "Неверный логин",
                        "Указанный логин слишком короткий"
                    )
                elif status == 2:
                    self.show_error(
                        "Неверный логин",
                        "Указанный логин слишком длинный"
                    )
                elif status == 3:
                    self.show_error(
                        "Неверный пароль",
                        "Указанный пароль слишком короткий"
                    )
                elif status == 4:
                    self.show_error(
                        "Неверный логин",
                        "Аккаунт с указанным логином уже существует"
                    )
            elif com == "login_status":
                status = data[1]

                if status == 0:
                    self.send(["get_account_data"])
                elif status == 1:
                    self.show_error(
                        "Неверный логин",
                        "Указанный логин слишком короткий"
                    )
                elif status == 2:
                    self.show_error(
                        "Неверный логин",
                        "Указанный логин слишком длинный"
                    )
                elif status == 3:
                    self.show_error(
                        "Неверный пароль",
                        "Указанный пароль слишком короткий"
                    )
                elif status == 4:
                    self.show_error(
                        "Неверный логин",
                        "Аккаунта с указанным логином не существует"
                    )
                elif status == 5:
                    self.show_error(
                        "Неверный пароль",
                        "Пароль от аккаунта не подходит"
                    )
            elif com == "account_data":
                adata = data[1]
                self.__sended = adata[0]
                self.__received = adata[1]
                self._logins = adata[2]

                for element in self.win.elements.values():
                    element.destroy()

                frame = tk.Frame(background=self.MAIN_BACKGROUND)
                self.win.place(
                    "messages_frame",
                    frame,
                    relx=0.3,
                    relw=0.7,
                    relh=1
                )
                cnv = tk.Canvas(
                    frame,
                    background=self.MAIN_BACKGROUND,
                    bd=0,
                    highlightthickness=0
                )
                cnv_sbar = ttk.Scrollbar(frame)
                self.win.place(
                    "messages_scrollbar",
                    cnv_sbar,
                    relx=1,
                    anchor=tk.NE,
                    relh=1
                )
                cnv_sbar.configure(command=cnv.yview)
                cnv.configure(yscrollcommand=cnv_sbar.set)
                self.win.place(
                    "messages",
                    cnv,
                    relw=1,
                    relh=1,
                    x=20,
                    y=5,
                    w=-40,
                    h=-35
                )
                self.win.place(
                    "messages_input",
                    ttk.Entry(),
                    x=15,
                    relx=0.3,
                    rely=1,
                    anchor=tk.NW,
                    relw=0.7,
                    w=-85,
                    y=-24,
                    h=24
                )

                listbox = tk.Listbox(
                    bg=self.MAIN_BACKGROUND,
                    bd=0,
                    font="Arial 16 bold",
                    fg=self.MAIN_FOREGROUND,
                    selectbackground=self.SELECT_FOREGROUND,
                    selectmode=tk.SINGLE,
                    activestyle=tk.NONE,
                    highlightthickness=0
                )
                listbox.bind(
                    "<<ListboxSelect>>",
                    lambda _: self.user_selected()
                )
                self.root.bind("<Configure>", self.resize)
                self.win.place(
                    "userlist",
                    listbox,
                    relw=0.3,
                    relh=1,
                    anchor=tk.NW,
                    x=5,
                    y=5,
                    w=-10,
                    h=-10
                )
                scrollbar = ttk.Scrollbar(command=listbox.yview)
                self.win.place(
                    "userlist_scrollbar",
                    scrollbar,
                    relx=0.3,
                    anchor=tk.NW,
                    relh=1
                )
                listbox.config(yscrollcommand=scrollbar.set)

                for user in self._logins.values():
                    listbox.insert(tk.END, f" {user}")

                listbox.select_set(0)
                listbox.event_generate("<<ListboxSelect>>")

            sleep(self._RECEIVE_SLEEP_TIME)

    def main(self):
        """Основная функция клиента."""
        self.root = tk.Tk()
        self.root.wm_title("Messenger")
        self.root.wm_geometry("1000x600")
        self.win = Window(self.root)

        self.last_height = self.root.winfo_height()

        style = ttk.Style(self.root)
        style.theme_use("clam")
        self.root.configure(bg=self.MAIN_BACKGROUND)
        style.configure(
            "TLabel",
            background=self.MAIN_BACKGROUND,
            foreground=self.MAIN_FOREGROUND
        )
        style.configure(
            "TEntry",
            background=self.MAIN_BACKGROUND
        )
        style.configure(
            "TButton",
            background=self.SECOND_BACKGROUND,
            activebackground=self.THIRD_BACKGROUND
        )

        self.win.place(
            "loadscreen_registration",
            ttk.Label(text="Регистрация", font="Arial 24 bold"),
            relx=0.5,
            rely=0,
            anchor=tk.N,
            y=12
        )
        self.win.place(
            "loadscreen_registration_login",
            ttk.Label(text="Логин:", font="Arial 16 bold"),
            relx=0,
            rely=0.45,
            x=16,
            anchor=tk.W
        )
        self.win.place(
            "loadscreen_registration_password",
            ttk.Label(text="Пароль:", font="Arial 16 bold"),
            relx=0,
            rely=0.55,
            x=16,
            anchor=tk.W
        )
        self.win.place(
            "loadscreen_registration_login_field",
            ttk.Entry(font="Arial 12"),
            relx=1,
            rely=0.45,
            x=-16,
            anchor=tk.E
        )
        self.win.place(
            "loadscreen_registration_password_field",
            ttk.Entry(font="Arial 12"),
            relx=1,
            rely=0.55,
            x=-16,
            anchor=tk.E
        )
        self.win.place(
            "loadscreen_registration_button",
            ttk.Button(
                text="Зарегестрироваться",
                command=lambda: self.send([
                    "register",
                    self.win.loadscreen_registration_login_field.get(),
                    self.win.loadscreen_registration_password_field.get()
                ])
            ),
            relx=0,
            rely=1,
            anchor=tk.SW,
            y=-12,
            x=12
        )
        self.win.place(
            "loadscreen_login_button",
            ttk.Button(
                text="Войти",
                command=lambda: self.send([
                    "login",
                    self.win.loadscreen_registration_login_field.get(),
                    self.win.loadscreen_registration_password_field.get()
                ])
            ),
            relx=1,
            rely=1,
            anchor=tk.SE,
            y=-12,
            x=-12
        )

        self.root.mainloop()


if __name__ == "__main__":
    MessengerClient()

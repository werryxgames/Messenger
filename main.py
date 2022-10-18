"""Мессенджер на Python (клиент)."""
# -*- coding: utf-8 -*-

import tkinter as tk

from json import dumps
from json import loads
from math import ceil
from math import floor
from os import path as opath
from os import system
from socket import AF_INET
from socket import SOCK_DGRAM
from socket import socket
from threading import Thread
from time import sleep
from tkinter import ttk

from aes_crypto import acrypt

KEY_EXTRA = "LX@$wmd3l8Yt9zxj9WH8yp@DOzNrDk2^flJzzNU!%oYy3EUoXabyGF~k%5TiJBH*"
KEY_LOGIN_FILE = "rW9M8%KphnA*Jt1rCNG*8ANo51$h*8TRI&c@mPnD)8$*EMUzxq0Kr(B5M~qd\
C)QM"


def absolute(path):
    """Возвращает абсолютный путь к path."""
    return opath.join(opath.dirname(opath.realpath(__file__)), path)


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

    def clear(self) -> None:
        """Очищает все элементы."""
        for child in self.tk_window.winfo_children():
            child.destroy()

        self.elements = {}

    def __getattribute__(self, id_: str):
        """Получает элемент по его ID.

        Аргументы:
            id_:    Уникальный идентификатор элемента.

        Возвращаемое значение: Элемент.
        """
        if id_ in ["pack", "place", "tk_window", "elements", "clear"]:
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
    FRAME_BG_COLOR = "#333"
    PANEL_BACKGROUND = "#222"
    _RECEIVE_SLEEP_TIME = 1 / 60
    _IDLE_SLEEP_TIME = 1 / 3

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
        self._is_on_main_tab: bool = False
        self.__temp_messages: list = []
        self.__key = None
        self.__aes = None
        self.destroyed = False
        self.__queued_requests = []
        self.__last_login = None
        self.__last_password = None

        Thread(target=self.receive, daemon=True).start()
        Thread(target=self.send_idle, daemon=True).start()

        self.main()

        if not self.destroyed:
            self._sock.send(b"\x05\x03\xff\x01")

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

    def __encode_message(self, message) -> bytes:
        """Превращает объекты, преобразоваемые в JSON в байты."""
        if self.__key is None and not self.destroyed:
            self._sock.send(b"\x05\x03\xff\x01")
            self.__queued_requests.append(message)
            return None

        return self.__aes.encrypt(dumps(
            message,
            separators=(",", ":"),
            ensure_ascii=False
        ))

    def __decode_message(self, message: bytes):
        """Превращает байты в объекты, преобразоваемые в JSON."""
        if self.__key is None:
            self.__key = message.decode("ascii")
            self.__aes = acrypt(KEY_EXTRA + self.__key)

            for req in self.__queued_requests:
                self.send(req)

            return False

        return loads(self.__aes.decrypt(message))

    def send(self, message) -> None:
        """Отправляет сообщение message на сервер.

        Аргументы:
            message:    Сообщение.
        """
        msg = self.__encode_message(message)

        if msg is not None:
            self._sock.send(msg)

    def send_register(self, login, password):
        """Присылает сообщение регистрации на сервер."""
        self.__last_login = login
        self.__last_password = password
        self.send(["register", login, password])

    def send_login(self, login, password):
        """Присылает сообщение входа в аккаунт на сервер."""
        self.__last_login = login
        self.__last_password = password
        self.send(["login", login, password])

    def remember_login(self):
        """Записывает логин и пароль для дальнейшего автоматического входа."""
        if self.__last_login is None or self.__last_password is None:
            return False

        login = str(self.__last_login)
        password = str(self.__last_password)

        with open(absolute(".logindata"), "wb") as lfile:
            lfile.write(
                acrypt(KEY_LOGIN_FILE).encrypt("\n".join([login, password]))
            )

        return True

    def restore_login(self):
        """Восстанавливает предыдущий введённый логин и пароль."""
        if self.__last_login is not None and self.__last_password is not None:
            return [self.__last_login, self.__last_password]

        try:
            with open(absolute(".logindata"), "rb") as lfile:
                data = acrypt(KEY_LOGIN_FILE).decrypt(lfile.read()).split("\n")
        except FileNotFoundError:
            return None

        return data

    def forget_login(self):
        """Выходит из аккаунта."""
        system(f'rm {absolute(".logindata")}')
        self.__aes = None
        self.__key = None
        self._is_on_main_tab = False
        self._logins = {}
        self.__sended = []
        self.__received = []
        self.login_tab()

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

        if user_id == self._userid_selected:
            return

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

        for msg in self.__temp_messages[::-1]:
            if msg[1] != self._userid_selected:
                continue

            text = cnv.create_text(
                cwh - 5,
                offset,
                text=msg[0],
                anchor=tk.NE,
                fill=self.MESSAGE_FORE_COLOR,
                font="Arial 16",
                width=cwh - 20
            )
            bbox_text = cnv.bbox(text)

            diff = bbox_text[1] - bbox_text[3] - 20
            cnv.move(text, 0, diff)
            text2 = cnv.create_text(
                cwh - 5,
                cnv.bbox(text)[3],
                text="Отправлено",
                anchor=tk.NE,
                fill=self.MESSAGE_FORE_COLOR,
                font="Arial 10",
                width=cwh - 20
            )
            bbox_text = cnv.bbox(text)
            bbox_text2 = cnv.bbox(text2)

            text_bbox = [
                min(bbox_text[0], bbox_text2[0]),
                bbox_text[1],
                bbox_text[2],
                bbox_text2[3]
            ]

            rect = self.create_round_rectangle(
                cnv,
                text_bbox[0] - 5,
                text_bbox[1] - 5,
                text_bbox[2] + 5,
                text_bbox[3] + 5,
                15,
                fill=self.MESSAGE_BACK_COLOR,
                width=0,
                ign1=True
            )
            cnv.tag_lower(rect)

            offset += diff

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
            bbox_text = cnv.bbox(text)

            diff = bbox_text[1] - bbox_text[3] - 20

            if sended:
                text2 = cnv.create_text(
                    cwh - 5,
                    cnv.bbox(text)[3],
                    text=["Доставлено", "Получено", "Прочитано"][msg[4]],
                    anchor=tk.NE,
                    fill=self.MESSAGE_FORE_COLOR,
                    font="Arial 10",
                    width=cwh - 20
                )
                bbox = cnv.bbox(text2)
                diff += bbox[1] - bbox[3]

            cnv.move(text, 0, diff)

            if sended:
                cnv.move(text2, 0, diff)

            if sended:
                bbox_text = cnv.bbox(text)
                bbox_text2 = cnv.bbox(text2)

                text_bbox = [
                    min(bbox_text[0], bbox_text2[0]),
                    bbox_text[1],
                    bbox_text[2],
                    bbox_text2[3]
                ]
            else:
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

    def send_message(self, message: str) -> None:
        """Отправляет сообщение на сервер.

        Аргументы:
            message:    Сообщение.
        """
        if self._userid_selected == -1:
            return

        message = message[:65535]

        self.win.messages_input.delete(0, tk.END)
        self.__temp_messages.append([message, self._userid_selected])

        listbox = self.win.userlist

        if self._userid_selected != -1:
            listbox.select_set(
                list(
                    self._logins.keys()
                ).index(str(self._userid_selected))
            )
            self._userid_selected = -1
        else:
            listbox.select_set(0)

        listbox.event_generate("<<ListboxSelect>>")

        self.send(["send_message", message, self._userid_selected])

    def add_user(self, username: str) -> None:
        """Добавляет пользователя по имени.

        Аргументы:
            username:   Имя пользователя.
        """
        for uid, username2 in enumerate(self._logins.values()):
            if username == username2:
                listbox = self.win.userlist
                listbox.select_clear(0, tk.END)
                listbox.select_set(uid)
                listbox.event_generate("<<ListboxSelect>>")
                return

        self.send(["find_user", username])

    def receive(self) -> None:
        """Получает сообщения от сервера."""
        while True:
            try:
                jdata = self._sock.recv(70000)
            except ConnectionResetError:
                self.login_tab()
                self.show_error(
                    "Сервер отключён",
                    "Сервер принудительно разорвал подключение"
                )

            data = self.__decode_message(jdata)

            if data is False:
                continue

            com = data[0]

            if com == "register_status":
                status = data[1]

                if status == 0:
                    self.remember_login()
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
                    self.remember_login()
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

                if status != 0:
                    self.login_tab()
            elif com == "account_data":
                adata = data[1]
                self.__sended = adata[0]
                self.__received = adata[1]
                self._logins = adata[2]

                main_tab = self._is_on_main_tab

                self._is_on_main_tab = True

                if not main_tab:
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
                    top_panel = ttk.Frame(frame, style="Panel.TFrame")
                    self.win.place(
                        "top_panel",
                        top_panel,
                        h=35,
                        relw=1

                    )
                    self.win.place(
                        "top_panel_logout",
                        ttk.Button(
                            top_panel,
                            text="Выйти",
                            command=self.forget_login
                        ),
                        anchor=tk.NE,
                        relx=1,
                        x=-3,
                        w=50,
                        h=29,
                        y=3
                    )
                    cnv_sbar = ttk.Scrollbar(frame)
                    self.win.place(
                        "messages_scrollbar",
                        cnv_sbar,
                        y=35,
                        relx=1,
                        anchor=tk.NE,
                        relh=1,
                        h=-60
                    )
                    cnv_sbar.configure(command=cnv.yview)
                    cnv.configure(yscrollcommand=cnv_sbar.set)
                    self.win.place(
                        "messages",
                        cnv,
                        relw=1,
                        relh=1,
                        x=20,
                        y=35,
                        w=-40,
                        h=-5
                    )
                    msg_input = ttk.Entry(font="Arial 16")
                    self.win.place(
                        "messages_input",
                        msg_input,
                        x=15,
                        relx=0.3,
                        rely=1,
                        relw=0.7,
                        anchor=tk.SW,
                        w=-95,
                        h=30
                    )
                    msg_input.bind("<Return>", lambda _: self.send_message(
                        self.win.messages_input.get()
                    ))
                    self.win.place(
                        "message_send_btn",
                        ttk.Button(
                            text="Отправить",
                            command=lambda: self.send_message(
                                self.win.messages_input.get()
                            )
                        ),
                        relx=1,
                        rely=1,
                        anchor=tk.SE,
                        h=30
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
                        "add_user_name",
                        ttk.Entry(font="Arial 16"),
                        x=5,
                        y=5,
                        h=30,
                        relw=0.3,
                        w=-40,
                    )
                    self.win.place(
                        "add_user_button",
                        ttk.Button(text="+", command=lambda:
                                        self.add_user(
                                            self.win.add_user_name.get())
                                   ),
                        relx=0.3,
                        x=-35,
                        w=30,
                        y=5,
                        h=30
                    )
                    self.win.place(
                        "userlist",
                        listbox,
                        relw=0.3,
                        relh=1,
                        anchor=tk.NW,
                        x=5,
                        y=40,
                        w=-10,
                        h=-45
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
                else:
                    listbox = self.win.userlist
                    listbox.delete(0, tk.END)

                    for i, temp_msg in enumerate(self.__temp_messages):
                        if temp_msg[0] == self.__sended[-1][2]:
                            self.__temp_messages = self.__temp_messages[i + 1:]
                            break

                for user in self._logins.values():
                    listbox.insert(tk.END, f" {user}")

                if self._userid_selected != -1:
                    listbox.select_set(
                        list(
                            self._logins.keys()
                        ).index(str(self._userid_selected))
                    )
                    self._userid_selected = -1
                else:
                    listbox.select_set(0)

                listbox.event_generate("<<ListboxSelect>>")
            elif com == "find_user_result":
                self.win.add_user_name.delete(0, tk.END)

                if data[1] is False:
                    self.show_error(
                        "Не найдено",
                        "Не удалось найти указанного пользователя"
                    )
                else:
                    arr = data[1]

                    self._logins[str(arr[0])] = arr[1]
                    listbox = self.win.userlist
                    listbox.insert(tk.END, f" {arr[1]}")
                    listbox.select_clear(0)
                    listbox.select_set(len(self._logins) - 1)
                    listbox.event_generate("<<ListboxSelect>>")
            elif com == "not_logged":
                if self._userid_selected == -1:
                    self.show_error(
                        "Требуется вход",
                        "Для совершения этой операции требуется вход в аккаунт"
                    )
                else:
                    self.login_tab()
                    self.show_error(
                        "Вы вышли из аккаунта",
                        "Требуется заново войти в аккаунт для совершения этой \
операции"
                    )

            sleep(self._RECEIVE_SLEEP_TIME)

    def send_idle(self) -> None:
        """Отправляет сообщение серверу о том, что клиент до сих пор открыт."""
        while True:
            if self.__key is not None and self._is_on_main_tab:
                self.send(["client_alive"])

            sleep(self._IDLE_SLEEP_TIME)

    def login_tab(self, clear=True) -> None:
        """Перемещает на начальную вкладку."""
        self.__sended = []
        self.__received = []
        self._logins = {}
        self._userid_selected = -1
        self._is_on_main_tab = False
        self.__temp_messages = []
        self.__key = None
        self.__aes = None

        if clear:
            self.win.clear()

        self.win.place(
            "loadscreen_background",
            ttk.Frame(),
            relx=0.5,
            rely=0.5,
            w=400,
            h=240,
            anchor=tk.CENTER,
        )

        self.win.place(
            "loadscreen_registration",
            ttk.Label(
                text="Регистрация и вход",
                font="Arial 24 bold",
                background=self.FRAME_BG_COLOR
            ),
            relx=0.5,
            rely=0.5,
            anchor=tk.N,
            y=-88
        )
        self.win.place(
            "loadscreen_registration_login",
            ttk.Label(
                text="Логин:",
                font="Arial 16 bold",
                background=self.FRAME_BG_COLOR
            ),
            relx=0.5,
            rely=0.5,
            x=-160,
            y=-20,
            anchor=tk.W
        )
        self.win.place(
            "loadscreen_registration_password",
            ttk.Label(
                text="Пароль:",
                font="Arial 16 bold",
                background=self.FRAME_BG_COLOR
            ),
            relx=0.5,
            rely=0.5,
            x=-160,
            y=20,
            anchor=tk.W
        )
        self.win.place(
            "loadscreen_registration_login_field",
            ttk.Entry(font="Arial 12"),
            relx=0.5,
            rely=0.5,
            x=160,
            y=-20,
            anchor=tk.E
        )
        self.win.place(
            "loadscreen_registration_password_field",
            ttk.Entry(font="Arial 12", show="•"),
            relx=0.5,
            rely=0.5,
            x=160,
            y=20,
            anchor=tk.E
        )
        self.win.place(
            "loadscreen_registration_button",
            ttk.Button(
                text="Зарегестрироваться",
                command=lambda: self.send_register(
                    self.win.loadscreen_registration_login_field.get(),
                    self.win.loadscreen_registration_password_field.get()
                )
            ),
            relx=0.5,
            rely=0.5,
            anchor=tk.SW,
            y=88,
            x=-160
        )
        self.win.place(
            "loadscreen_login_button",
            ttk.Button(
                text="Войти",
                command=lambda: self.send_login(
                    self.win.loadscreen_registration_login_field.get(),
                    self.win.loadscreen_registration_password_field.get()
                )
            ),
            relx=0.5,
            rely=0.5,
            anchor=tk.SE,
            y=88,
            x=160
        )

    def on_destroy(self):
        """Обработчик выхода из приложения."""
        if not self.destroyed and self.__key is not None:
            self.send(["disconnect"])

        self.destroyed = True
        self.root.destroy()

    def main(self):
        """Основная функция клиента."""
        self.root = tk.Tk()
        self.root.wm_title("Messenger")
        self.root.wm_geometry("1000x600")
        self.root.minsize(500, 340)
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
        style.configure(
            "TFrame",
            background=self.FRAME_BG_COLOR,
            borderwidth=0,
            highlightthickness=0,
            relief=tk.SUNKEN
        )
        style.configure(
            "Panel.TFrame",
            background=self.PANEL_BACKGROUND,
            borderwidth=0,
            highlightthickness=0,
            relief=tk.SUNKEN
        )

        self.root.protocol("WM_DELETE_WINDOW", self.on_destroy)

        data = self.restore_login()

        if data is None:
            self.login_tab(False)
        else:
            self.win.place(
                "autologin.label",
                ttk.Label(self.root, font="Arial 24 bold", text="Вход в аккаунт..."),
                relx=0.5,
                rely=0.5,
                anchor=tk.CENTER
            )
            self.send(["login", data[0], data[1]])

        self.root.mainloop()


if __name__ == "__main__":
    MessengerClient()

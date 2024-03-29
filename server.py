"""Модуль сервера."""
from base64 import b64encode
from hashlib import sha256
from json import dumps
from json import loads
from os import path
from random import choice
from socket import AF_INET
from socket import SOCK_DGRAM
from socket import socket
from sqlite3 import connect
from string import ascii_letters
from string import digits
from threading import Thread
from time import sleep
from time import time

from aes_crypto import acrypt
from bcrypt import kdf

PASSWORD_EXTRA_SALT = "Pu~w9cC+RV)Bfjnd1oSbLQhjwGP)mJ$R^%+DHp(u)LP@AgMq)dl&0T\
(V$Thope)Q"
KEY_EXTRA = "LX@$wmd3l8Yt9zxj9WH8yp@DOzNrDk2^flJzzNU!%oYy3EUoXabyGF~k%5TiJBH*"
IDLE_MAX_TIME = 10
IDLE_SLEEP_TIME = 1

clients = {}


def absolute(path_: str) -> str:
    """Возвращает абсолютный путь из относительного."""
    return path.normpath(path.join(
        path.dirname(path.realpath(__file__)),
        path_
    ))


def encrypt_password(user_id: int, password: str) -> str:
    """Шифрует пароль.

    Аргументы:
        user_id:    ID пользователя.
        password:   Пароль пользователя.

    Возвращаемое значение:  Зашифрованный пароль.
    """
    user_id = str((user_id + 1) ** 3)
    hashed_password = b64encode(kdf(
        password=sha256(
            password.encode("utf8")
        ).digest() + PASSWORD_EXTRA_SALT.encode("utf8"),
        salt=user_id.encode("utf8"),
        desired_key_bytes=24,
        rounds=64
    )).decode("utf8").replace("=", "_")
    return hashed_password


class Database:
    """Класс базы данных."""

    def __init__(self, filepath: str) -> None:
        """Инициализация базы данных.

        Аргументы:
            filepath:   Путь к базе данных.
        """
        self.__con = connect(filepath)
        self.__cur = self.__con.cursor()

    def sql(
        self,
        sql_text: str,
        format_=None,
        noresult: bool = False
    ):
        """Выполняет SQL код.

        Аргументы:
            sql_text:   SQL код.
            format_:    Заменители '?' в SQL коде.
            noresult:   Если включено, то результатом будет булевое значение.

        Возвращаемое значение:
            bool:   Если включено noresult, возвращает True, если результат
                        выполнения SQL кода пустой, иначе False.
            list:   Массив с результатами.
            tuple:  Единственный результат.
        """
        code = ""
        results = []

        if format_ is None:
            format_ = []
        else:
            format_ = format_[::-1]

        try:
            sql_text = sql_text[:sql_text.index("--")]
        except ValueError:
            pass

        for line in sql_text.split("\n"):
            stripped_line = line.strip()

            if len(stripped_line) == 0:
                continue

            code += stripped_line

            if stripped_line.endswith(";"):
                formats = [format_.pop() for _ in range(len(format_))]

                cursor = self.__cur.execute(code, tuple(formats))
                results.append(cursor.fetchall())
                code = ""

        self.__con.commit()

        if noresult:
            return all(len(result) == 0 for result in results)

        if len(results) == 1:
            return results[0]

        return results

    def reset_database(self) -> bool:
        """Сбрасывает базу данных к начальному состоянию.

        Возвращаемое значение: True, если удалось сбросить, иначе False.
        """
        return self.sql("""
            DROP TABLE IF EXISTS users;
            DROP TABLE IF EXISTS direct_messages;

            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                name VARCHAR(16) NOT NULL,
                password CHAR(32) NOT NULL
            );

            CREATE TABLE direct_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                sender INTEGER NOT NULL,
                content TEXT NOT NULL,
                receiver INTEGER NOT NULL,
                read TINYINT NOT NULL DEFAULT 0
            );
        """, noresult=True)

    def create_account(self, name: str, password: str):
        """Создаёт аккаунт.

        Аргументы:
            name:       Логин аккаунта.
            password:   Пароль от аккаунта.

        Возвращаемое значение:  Статус выполнения, id в случае успеха.
        """
        if len(name) < 1:
            return 1  # ERR_SHORT_NAME
        if len(name) > 16:
            return 2  # ERR_LONG_NAME

        if len(password) < 6:
            return 3  # ERR_SHORT_PASSWORD

        if not self.sql("SELECT * FROM users WHERE name = ?;", [name], True):
            return 4  # ERR_ACCOUNT_EXISTS

        count = self.sql("SELECT COUNT(*) FROM users;")[0][0] + 1
        hashed_password = encrypt_password(count, password)

        self.sql(
            "INSERT INTO users (name, password) VALUES (?, ?);",
            [name, hashed_password]
        )

        # SUCCESSFULL
        return [
            0,
            self.sql("SELECT id FROM users WHERE name = ?;", [name])[0][0]
        ]

    def login_account(self, name: str, password: str):
        """Входит в аккаунт.

        Аргументы:
            name:       Логин аккаунта.
            password:   Пароль от аккаунта.

        Возвращаемое значение:  Статус выполнения, id в случае успеха.
        """
        if len(name) < 1:
            return 1  # ERR_SHORT_NAME
        if len(name) > 16:
            return 2  # ERR_LONG_NAME

        if len(password) < 6:
            return 3  # ERR_SHORT_PASSWORD

        result = self.sql("SELECT id FROM users WHERE name = ?;", [name])

        if not result:
            return 4  # ERR_ACCOUNT_NOT_EXISTS

        result = result[0][0]

        hashed_password = encrypt_password(result, password)

        if self.sql(
            "SELECT * FROM users WHERE name = ? AND password = ?;",
            [name, hashed_password],
            True
        ):
            return 5  # ERR_INCORRECT_PASSWORD

        # SUCCESSFULL
        return [
            0,
            self.sql("SELECT id FROM users WHERE name = ?;", [name])[0][0]
        ]

    def get_account_data(self, name: str) -> (tuple, list):
        """Получает данные аккаунта.

        Аргументы:
            name:   Логин аккаунта.

        Возвращаемое значение:
            [
                Отправленные и полученные сообщения,
                ID пользователей, чей статус сообщений был изменён.
            ].
        """
        account_id = self.sql("SELECT id FROM users WHERE name = ?;", [name])

        if not account_id:
            return ()

        account_id = account_id[0][0]

        sended = self.sql(
            "SELECT * FROM direct_messages WHERE sender = ?;",
            [account_id]
        )
        received = self.sql(
            "SELECT * FROM direct_messages WHERE receiver = ?;",
            [account_id]
        )

        usernames = []
        usernames_logins = {}

        for smsg in sended:
            if smsg[3] not in usernames:
                usernames.append(smsg[3])

        for rmsg in received:
            if rmsg[1] not in usernames:
                usernames.append(rmsg[1])

        for uname in usernames:
            usernames_logins[uname] = self.sql(
                "SELECT name FROM users WHERE id = ?;",
                [uname]
            )[0][0]

        status_changed = self.sql("""
            SELECT sender FROM direct_messages WHERE receiver = ? AND read = 0;
        """, [account_id])

        st_changed = []

        for id_ in status_changed:
            if id_[0] not in st_changed:
                st_changed.append(id_[0])

        if len(st_changed) > 0:
            self.sql("""
                UPDATE direct_messages \
                SET read = 1 \
                WHERE receiver = ? AND read = 0;
            """, [account_id])

        return ((sended, received, usernames_logins), st_changed)

    def send_message(self, login: str, receiver: int, message: str) -> bool:
        """Создаёт запись в базе данных о сообщении."""
        sender_id = self.sql(
            "SELECT id FROM users WHERE name = ?;",
            [login]
        )
        exists_receiver = not self.sql(
            "SELECT id FROM users WHERE id = ?;",
            [receiver],
            noresult=True
        )

        if len(sender_id) == 0:
            return False

        if not exists_receiver:
            return False

        sender_id = sender_id[0][0]

        result = self.sql("""
            INSERT INTO direct_messages (sender, receiver, content)
            VALUES (?, ?, ?);
        """, [sender_id, receiver, message], noresult=True)

        self.sql("""
            UPDATE direct_messages \
            SET read = 2 \
            WHERE receiver = ? AND sender = ? AND (read = 0 OR read = 1);
        """, [sender_id, receiver])

        return result

    def find_user(self, username: str):
        """Ищет пользователя по username.

        Аргументы:
            username:   Имя пользователя.

        Возвращаемое значение:
            False:          Пользователь не найден.
            list[int, str]: ID пользователя и его имя.
        """
        result = self.sql("SELECT id FROM users WHERE name = ?;", [username])

        if len(result) == 0:
            return False

        return [result[0][0], username]

    def close(self) -> None:
        """Закрывает базу данных."""
        self.__con.close()


class NetworkedClient:
    """Класс клиента."""

    _instances = []

    def __init__(self, sock: socket, addr, key: str) -> None:
        self.sock: socket = sock
        self.addr = addr
        self.login = None
        self.id_ = None
        self.__password = None
        self.__key = key
        self.__aes = acrypt(KEY_EXTRA + self.__key)
        self._instances.append(self)

    def __encode_message(self, message) -> bytes:
        """Превращает объекты, преобразоваемые в JSON в байты."""
        return self.__aes.encrypt(dumps(
            message,
            separators=(",", ":"),
            ensure_ascii=False
        ))

    def __decode_message(self, message: bytes):
        """Превращает байты в объекты, преобразоваемые в JSON."""
        return loads(self.__aes.decrypt(message))

    def send(self, message: list) -> None:
        """Отправляет сообщение клиенту.

        Аргументы:
            message:    Сообщение.
        """
        print("Отправлено клиенту:", message)
        encoded = self.__encode_message(message)
        self.sock.sendto(encoded, self.addr)

    def send_account_data(self) -> None:
        """Отправляет данные об аккаунте."""
        if self.login is None:
            return

        adata = dtb.get_account_data(self.login)

        self.send(["account_data", adata[0]])

        for receiver in adata[1]:
            for inst in self._instances:
                if inst.id_ == receiver:
                    inst.send_account_data()

    def receive(self, jdata: bytes) -> bool:
        """Получает сообщение от клиента.

        Аргументы:
            jdata:  Данные от клиента.

        Возвращаемое значаени: Надо ли обновлять таймер сообщений?
        """
        data = self.__decode_message(jdata)

        if data == ["client_alive"]:
            return True

        print("Получено от клиента:", data)

        com = data[0]
        args = data[1:]

        if com == "register":
            result = dtb.create_account(*args[:2])

            if isinstance(result, list):
                status = result[0]
                self.id_ = result[1]
                self.send(["register_status", status])

                if status == 0:
                    self.login, self.__password = args[:2]
        elif com == "login":
            result = dtb.login_account(*args[:2])

            if isinstance(result, list):
                status = result[0]
                self.id_ = result[1]
                self.send(["login_status", status])

                if status == 0:
                    self.login, self.__password = args[:2]
        elif com == "disconnect":
            self.close()
            return False
        elif not (self.login is None and self.__password is None):
            if com == "get_account_data":
                self.send_account_data()
            elif com == "send_message":
                msg = args[0][:65535]
                dtb.send_message(self.login, args[1], msg)

                self.send_account_data()

                for instance in self._instances:
                    if args[1] == instance.login:
                        instance.send_account_data()
                        break
            elif com == "find_user":
                if args[0] == self.login:
                    self.send(["find_user_result", False])
                else:
                    self.send(["find_user_result", dtb.find_user(args[0])])
            else:
                return False
        elif com in ["get_account_data", "send_message", "find_user"]:
            self.send(["not_logged"])
            return False
        else:
            return False

        return True

    def close(self) -> None:
        """Закрывает соединение с клиентом."""
        del clients[self.addr]


dtb = Database(absolute("messenger.db"))


def check_idle() -> None:
    """Отключает неактивных клиентов.

    Аргументы:
        clients:    Словарь всех клиентов.
    """
    while True:
        inactive_clients = []

        for client in clients.values():
            if client[1] < time() - IDLE_MAX_TIME:
                inactive_clients.append(client[0])

        for client in inactive_clients:
            client.close()

        sleep(IDLE_SLEEP_TIME)


def main() -> None:
    """Основная функция."""
    sock = socket(AF_INET, SOCK_DGRAM)
    sock.bind(("0.0.0.0", 7505))

    print("Сервер запущен")

    Thread(target=check_idle, daemon=True).start()

    with sock:
        while True:
            try:
                adrdata = sock.recvfrom(70000)
            except (ConnectionResetError, ConnectionAbortedError):
                continue

            data = adrdata[0]
            addr = adrdata[1]
            key = None
            print("<", data)

            if addr not in clients:
                key = "".join(
                    [choice(ascii_letters + digits) for _ in range(64)]
                             )
                clients[addr] = [
                    NetworkedClient(sock, addr, key),
                    time() - IDLE_MAX_TIME + 5
                ]

                if data == b"\x05\x03\xff\x01":
                    key = key.encode("ascii")
                    sock.sendto(key, addr)
                    print(">", key)
                    key = None
            else:
                try:
                    if clients[addr][0].receive(data):
                        clients[addr][1] = time()
                except BaseException as exc:
                    clients[addr][0].close()
                    print(exc)

    dtb.close()


if __name__ == "__main__":
    # dtb.reset_database()
    # print(len(dtb.create_account("Werryx", "123456")) > 1)
    # print(len(dtb.create_account("Werland", "123456")) > 1)
    # print(len(dtb.create_account("zhbesluk", "123456")) > 1)
    # print(len(dtb.create_account("WTest", "123456")) > 1)
    # print(dtb.sql("""
    #     INSERT INTO direct_messages (sender, receiver, content) VALUES
    #         (2, 1, "Привет, я Werland"),
    #         (2, 1, ?),
    #         (1, 2, "Я - Werryx"),
    #         (2, 1, "Как дела?"),
    #         (3, 1, "Помнишь?"),
    #         (1, 2, "Нормально"),
    #         (4, 1, "TEST");
    # """, [f"А ты?{' ОЧЕНЬ ДЛИННАЯ СТРОКА!' * 20}"], noresult=True))
    # print(dtb.sql("SELECT * FROM direct_messages;"))

    main()

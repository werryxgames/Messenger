"""Модуль сервера."""
from base64 import b64encode
from hashlib import sha256
from json import dumps
from json import loads
from os import path
from socket import AF_INET
from socket import SOCK_DGRAM
from socket import socket
from sqlite3 import connect
from typing import Optional
from typing import Union

from bcrypt import kdf

PASSWORD_EXTRA_SALT = "Pu~w9cC+RV)Bfjnd1oSbLQhjwGP)mJ$R^%+DHp(u)LP@AgMq)dl&0T\
(V$Thope)Q"


def absolute(path_):
    """Возвращает абсолютный путь из относительного."""
    return path.join(path.dirname(path.realpath(__file__)), path_)


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
        format_: Optional[list] = None,
        noresult: bool = False
    ) -> Union[bool, list, tuple]:
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

    def create_account(self, name: str, password: str) -> int:
        """Создаёт аккаунт.

        Аргументы:
            name:       Логин аккаунта.
            password:   Пароль от аккаунта.

        Возвращаемое значение:  Статус выполнения.
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

        return 0  # SUCCESSFULL

    def login_account(self, name: str, password: str) -> int:
        """Входит в аккаунт.

        Аргументы:
            name:       Логин аккаунта.
            password:   Пароль от аккаунта.

        Возвращаемое значение:  Статус выполнения.
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

        return 0

    def get_account_data(self, name: str) -> tuple:
        """Получает данные аккаунта.

        Аргументы:
            name:   Логин аккаунта.

        Возвращаемое значение:  Отправленные и полученные сообщения.
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

        print(usernames)
        for uname in usernames:
            usernames_logins[uname] = self.sql(
                "SELECT name FROM users WHERE id = ?;",
                [uname]
            )[0][0]

        return (sended, received, usernames_logins)

    def close(self):
        """Закрывает базу данных."""
        self.__con.close()


class NetworkedClient:
    """Класс клиента."""

    def __init__(self, sock: socket, addr: tuple[str, int]) -> None:
        self.sock: socket = sock
        self.addr: tuple[str, int] = addr
        self.login: Optional[str] = None
        self.password: Optional[str] = None

    def send(self, message: Union[list, dict]) -> None:
        """Отправляет сообщение клиенту.

        Аргументы:
            message:    Сообщение.
        """
        print("Отправлено клиенту:", message)
        self.sock.sendto(dumps(message).encode("utf8"), self.addr)

    def receive(self, jdata: bytes) -> None:
        """Получает сообщение от клиента.

        Аргументы:
            jdata:  Данные от клиента.
        """
        data = loads(jdata.decode("utf8"))

        print("Получено от клиента:", data)

        com = data[0]
        args = data[1:]

        if com == "register":
            status = dtb.create_account(*args[:2])
            self.send(["register_status", status])

            if status == 0:
                self.login, self.password = args[:2]
        elif com == "login":
            status = dtb.login_account(*args[:2])
            self.send(["login_status", status])

            if status == 0:
                self.login, self.password = args[:2]
        elif not (self.login is None and self.password is None):
            if com == "get_account_data":
                self.send(["account_data", dtb.get_account_data(self.login)])


dtb = Database(absolute("messenger.db"))


def main():
    """Основная функция."""
    clients = {}

    sock = socket(AF_INET, SOCK_DGRAM)
    sock.bind(("0.0.0.0", 7505))

    print("Сервер запущен")

    with sock:
        while True:
            try:
                adrdata = sock.recvfrom(1024)
            except (ConnectionResetError, ConnectionAbortedError):
                pass

            data = adrdata[0]
            addr = adrdata[1]

            if addr not in clients:
                clients[addr] = NetworkedClient(sock, addr)

            clients[addr].receive(data)

    dtb.close()


if __name__ == "__main__":
    dtb.reset_database()
    print(dtb.create_account("Werryx", "123456") == 0)
    print(dtb.create_account("Werland", "123456") == 0)
    print(dtb.create_account("zhbesluk", "123456") == 0)
    print(dtb.sql("""
        INSERT INTO direct_messages (sender, receiver, content) VALUES
            (2, 1, "Привет, я Werland"),
            (2, 1, "А ты?"),
            (1, 2, "Я - Werryx"),
            (2, 1, "Как дела?"),
            (3, 1, "Помнишь?"),
            (1, 2, "Нормально");
    """, noresult=True))
    print(dtb.sql("SELECT * FROM direct_messages;"))
    # dtb.close()

    main()

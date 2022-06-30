"""Тестирование сервера."""
from os import path
from sqlite3 import OperationalError
from sqlite3 import ProgrammingError
from string import ascii_letters
from random import choice, randint

from pytest import mark

import server


@mark.parametrize("path_, expected_result", [
    ("tests", "Messenger/tests"),
    (path.join("tests", "test_server.py"), "Messenger/tests/test_server.py"),
    ("", "Messenger"),
    (".", "Messenger")
])
def test_absolute(path_, expected_result):
    """Тесты для server.absolute()."""
    absolute = server.absolute(path_)
    absolute = absolute.replace(path.join("1", "2")[1:-1], "/")

    assert absolute.endswith(expected_result)


def test_absolute_start():
    """Тест на начало server.absolute()."""
    absolute = server.absolute("")
    calc_path = path.realpath(server.__file__)

    print(absolute, calc_path)

    assert calc_path.startswith(absolute)


@mark.parametrize("user_id, password, expected_result", [
    (1, "12345678", "6cJMGewh28PtKwQO57uFdg+y95COWn5L"),
    (1, "123456", "sSVdrVm2acZwlKZDOp4/J5e+PyyLqIg7"),
    (10, "123456", "zK1w8dDAWUS8rUBJ1IsAInGWiE4a8uMe"),
    (
        10 ** 1000,
        "VEry @HArd!p$ aS %s W0\tRd..",
        "4BhuSTu3axpHMx5WgmwNaTtqIlNRHws5"
    ),
    (1, "", "xrGszhfG1+EBRu0hX27lKHeRgAYXD0Os"),
    (0, "", "d80vzAqybe6Su312ek6LRPtkZQ+C1RCE"),
    (-123, "", "FkbwhKiixTahBHF7qiDwcoiQOntEnoJs"),
    (
        32,
        "FkbwhKiixTahBHF7qiDwcoiQOntEnoJs",
        "7H0vAwyzgYLxClEof7JbR0uhbpR24I5l"
    )
])
def test_encrypt_password(user_id, password, expected_result):
    """Тесты для server.encrypt_password()."""
    result = server.encrypt_password(user_id, password)

    assert len(result) == 32
    assert result == expected_result


def test_closed_database():
    """Тест с выполнением SQL в закрытой базе данных."""
    dtb = server.Database(":memory:")
    dtb.close()

    try:
        dtb.sql("CREATE TABLE test;")
        assert False
    except ProgrammingError:
        assert True


def test_sql():
    """Тест с SQL кодом."""
    values = (123456, "Hello")

    dtb = server.Database(":memory:")

    assert dtb.sql("""
        CREATE TABLE test (
            test_param INTEGER,
            test_param2 VARCHAR(10) NOT NULL
        );
    """, noresult=True)

    assert dtb.sql("""
        INSERT INTO test (test_param, test_param2)
        VALUES (?, ?);
    """, list(values), noresult=True)

    result = dtb.sql("SELECT * FROM test;")

    dtb.close()

    assert result == [values]


def test_reset_database():
    """Тест для server.Database.reset_database()."""
    dtb = server.Database(":memory:")
    dtb.reset_database()

    suc = False

    try:
        result = dtb.sql("DROP TABLE users;", noresult=True)
        dtb.close()

        suc = result
    except OperationalError:
        dtb.close()

    assert suc


@mark.parametrize("login, password, expected_result, add_data", [
    ("", "", 1, []),
    ("a" * 17, "", 2, []),
    ("Normal", "", 3, []),
    ("Test", "12345678", 4, [True]),
    ("Account", "Pass12345678", 0, [
        False,
        "Account",
        "7oyKAYIflTsuISbDt2Yb+SNVVvCiFOem"
    ])
])
def test_create_account(login, password, expected_result, add_data):
    """Тесты для server.Database.create_account()."""
    dtb = server.Database(":memory:")
    dtb.reset_database()

    if len(add_data) > 0 and add_data[0]:
        dtb.create_account(login, password)

    assert dtb.create_account(login, password) == expected_result

    if len(add_data) == 3:
        result = dtb.sql(
            "SELECT * FROM users WHERE name = ? AND password = ?;",
            [*add_data[1:]]
        )

        dtb.close()

        assert result == [(1, *add_data[1:])]


@mark.parametrize("login, password, expected_result, add_data", [
    ("", "", 1, []),
    ("a" * 17, "", 2, []),
    ("Normal", "", 3, []),
    ("Test", "12345678", 4, []),
    ("Account", "Pass12345678", 5, [
        "Account",
        "IncPass12345678"
    ]),
    ("Account", "Pass12345678", 0, [
        "Account",
        "Pass12345678"
    ]),
    ("Account", "Pass12345678", 4, [
        "Account2",
        "Pass12345678"
    ]),
    ("Account", "Pass12345678", 4, [
        "User123",
        "123412341234"
    ])
])
def test_login_account(login, password, expected_result, add_data):
    """Тесты для server.Database.create_account()."""
    dtb = server.Database(":memory:")
    dtb.reset_database()

    if len(add_data) == 2:
        dtb.create_account(*add_data)

    login_result = dtb.login_account(login, password)

    dtb.close()

    assert login_result == expected_result


@mark.parametrize("name", [
    "", "Account", "Тестовый аккаунт"
])
def test_get_account_data_not_exists(name):
    """server.Database.get_account_data() с несуществующими аккаунтами."""
    dtb = server.Database(":memory:")
    dtb.reset_database()

    result = dtb.get_account_data(name)

    dtb.close()

    assert result == ()


@mark.parametrize("name, password, x_users, x_messages, expected_result", [
    ("Account", "12345678", [
        ["Account2", "12345678"],
        ["TestAcc", "87654321"]
    ], [
        [1, 2, "2, я 1."],
        [1, 3, "Привет, Test, я Account."],
        [3, 1, "Очень приятно."],
        [3, 1, "Я TestAccount."],
        [2, 1, "Понял."],
        [1, 2, "Тест завершён."],
        [1, 3, "Ура."]
    ],
        ([
            (1, 1, "2, я 1.", 2, 0),
            (2, 1, "Привет, Test, я Account.", 3, 0),
            (6, 1, "Тест завершён.", 2, 0),
            (7, 1, "Ура.", 3, 0)
        ], [
            (3, 3, "Очень приятно.", 1, 0),
            (4, 3, "Я TestAccount.", 1, 0),
            (5, 2, "Понял.", 1, 0)
        ], {2: "Account2", 3: "TestAcc"})
    )
])
def test_get_account_data_exists(
    name,
    password,
    x_users,
    x_messages,
    expected_result
):
    """Тесты для server.Database.get_account_data()."""
    dtb = server.Database(":memory:")
    dtb.reset_database()

    dtb.create_account(name, password)

    for login, password_ in x_users:
        dtb.create_account(login, password_)

    for sender, receiver, text in x_messages:
        assert dtb.sql("INSERT INTO direct_messages (sender, receiver, content) \
            VALUES (?, ?, ?);", [sender, receiver, text], noresult=True)

    result = dtb.get_account_data(name)

    dtb.close()

    print(result)
    print("\n\n" + str(expected_result))

    assert result == expected_result


@mark.parametrize("message, expected_result", [
    ([], b"[]"),
    (["array"], b"[\"array\"]"),
    ({"dict": "ionary"}, b"{\"dict\":\"ionary\"}"),
    (["array", "many", "elements"], b"[\"array\",\"many\",\"elements\"]"),
    ({"dict": "ionary", "ma": "ny", "ele": "ments"},
        b"{\"dict\":\"ionary\",\"ma\":\"ny\",\"ele\":\"ments\"}"),
    (["Русский"], "[\"Русский\"]".encode("utf8")),
    ({"Рус": "ский"}, "{\"Рус\":\"ский\"}".encode("utf8")),
    (["Русский", "язык", "поддерживается"],
        "[\"Русский\",\"язык\",\"поддерживается\"]".encode("utf8")),
    ({"Рус": "ский", "я": "зык", "под": "держивается"},
        "{\"Рус\":\"ский\",\"я\":\"зык\",\"под\":\"держивается\"}".encode(
            "utf8"
        ))
])
def test_encode_message(message, expected_result):
    """Тесты для server.NetworkedClient.encode_message()."""
    assert server.NetworkedClient.encode_message(message) == expected_result


@mark.parametrize("expected_result, message", [
    ([], b"[]"),
    (["array"], b"[\"array\"]"),
    ({"dict": "ionary"}, b"{\"dict\":\"ionary\"}"),
    (["array", "many", "elements"], b"[\"array\",\"many\",\"elements\"]"),
    ({"dict": "ionary", "ma": "ny", "ele": "ments"},
        b"{\"dict\":\"ionary\",\"ma\":\"ny\",\"ele\":\"ments\"}"),
    (["Русский"], "[\"Русский\"]".encode("utf8")),
    ({"Рус": "ский"}, "{\"Рус\":\"ский\"}".encode("utf8")),
    (["Русский", "язык", "поддерживается"],
        "[\"Русский\",\"язык\",\"поддерживается\"]".encode("utf8")),
    ({"Рус": "ский", "я": "зык", "под": "держивается"},
        "{\"Рус\":\"ский\",\"я\":\"зык\",\"под\":\"держивается\"}".encode(
            "utf8"
        ))
])
def test_decode_message(expected_result, message):
    """Тесты для server.NetworkedClient.decode_message()."""
    assert server.NetworkedClient.decode_message(message) == expected_result


def random_encode_decode_generate():
    test_letters = ascii_letters
    r_letters = "ёйцукенгшщзхъфывапролджэячсмитьбю"
    test_letters += r_letters + r_letters.upper()
    test_letters += "1234567890"

    is_dict = randint(0, 1)
    length = randint(1, 100)
    words_length = (0, 50)
    result = None

    if is_dict:
        result = {}

        for _ in range(length):
            result[
                "".join(
                    [
                        choice(test_letters)
                        for _ in range(randint(*words_length))
                    ]
                )
            ] = "".join(
                    [
                        choice(test_letters)
                        for _ in range(randint(*words_length))
                    ]
                )
    else:
        result = []

        for _ in range(length):
            result.append(
                "".join(
                    [
                        choice(test_letters)
                        for _ in range(randint(*words_length))
                    ]
                )
            )


@mark.parametrize("message", [
    random_encode_decode_generate() for _ in range(100)
])
def test_random_encode_decode(message):
    """Рандомные тесты для server.NetworkedClient.en/decode_message()."""
    assert server.NetworkedClient.decode_message(
        server.NetworkedClient.encode_message(message)
    ) == message

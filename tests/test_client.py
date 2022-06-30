"""Тестирование клиента."""
from contextlib import redirect_stdout
from io import StringIO
from pytest import mark

import main


@mark.parametrize("title, message, expected_result", [
    ("", "", 12),
    ("Тестовая ошибка", "", 27),
    ("", "Описание ошибки", 19),
    ("Заголовок ошибки", "Описание ошибки", 28),
    ("Заголовок", "Описание ошибки..", 21),
    ("Заголовок", "Описание ошибки длинее заголовка", 36),
    ("Title" * 1000, ("Description." * 10000)[:12008], 12012)
])
def test_show_error(title, message, expected_result):
    """Тесты для main.MessengerClient.show_error()."""
    file = StringIO()

    with redirect_stdout(file):
        main.MessengerClient.show_error(title, message)

    lines = file.getvalue().splitlines()

    print("\n".join(lines))
    print(len(lines[0]), expected_result)

    assert lines[0] == lines[2] == lines[4]
    assert "ОШИБКА: " in lines[1]
    assert lines[1].startswith("| ") and lines[1].endswith(" |")
    assert lines[3].startswith("| ") and lines[3].endswith(" |")
    assert all(char == "-" for char in lines[0])
    assert len(lines[0]) == len(lines[1]) == len(lines[3])
    assert len(lines[0]) == expected_result

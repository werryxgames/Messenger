import io
import pytest

from contextlib import redirect_stdout

import main


@pytest.mark.parametrize("title, message, expected_result", [
    ("", "", 12),  # Пустые параметры
    ("Тестовая ошибка", "", 27),  # Только заголовок
    ("", "Описание ошибки", 19),  # Только описание
    ("Заголовок ошибки", "Описание ошибки", 28),  # Заголовок длиннее описания
    ("Заголовок", "Описание ошибки..", 21),  # Описания длиной заголовка (+ 'ОШИБКА: ')
    ("Заголовок", "Описание ошибки длинее заголовка", 36),  # Описание длинне заголовка
    ("Title" * 1000, ("Description." * 10000)[:12008], 12012)  # Очень длинный заголовок и описание
])
def test_show_error(title, message, expected_result):
    file = io.StringIO()

    with redirect_stdout(file):
        main.MessengerClient.show_error(title, message)

    lines = file.getvalue().splitlines()

    print("\n".join(lines))

    assert lines[0] == lines[2] == lines[4]
    assert "ОШИБКА: " in lines[1]
    assert lines[1].startswith("| ") and lines[1].endswith(" |")
    assert lines[3].startswith("| ") and lines[3].endswith(" |")
    assert all(char == "-" for char in lines[0])
    assert len(lines[0]) == len(lines[1]) == len(lines[3])
    assert len(lines[0]) == expected_result

import io

from contextlib import redirect_stdout

import main

file = io.StringIO()


def test_show_error():
    with redirect_stdout(file):
        main.MessengerClient.show_error("Тест", "Тестовая ошибка")

    assert file.getvalue() == """\
-------------------
|  ОШИБКА: Тест   |
-------------------
| Тестовая ошибка |
-------------------
"""

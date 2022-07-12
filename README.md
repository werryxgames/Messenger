# Messenger
Разделы:

[Главное](#главное)

[Обучение](#обучение)

[Код](#код)

# Главное
## Что такое Messenger?
**Messenger** - бесплатный мессенджер с открытым исходным кодом для обмена мгновенными сообщениями

**Messenger** написан на языке програмирования [Python](https://python.org)

## Установка
### Установка Python
Установите [Python](https://python.org/download)

Работают ли определённые версии Python:
- [x] 3.10 - Все основные тесты происходят на этой версии
- [x] 3.9 - Версия поддерживается **Messenger** и тестируется в *Github*
- [x] 3.8 - Версия поддерживается **Messenger** и тестируется в *Github*
- [x] 3.7 - Версия не поддерживается, но пока что есть возможность запустить **Messenger** на ней
- [x] 3.6 - Версия не поддерживается, но пока что есть возможность запустить **Messenger** на ней
- [ ] 2.7 - Версия не поддерживается

**Остальные версии не тестировались**

### Скачивание репозитория
#### Скачивание из терминала
Если у вас установлен `git`, то выполните команду:
`git clone https://github.com/werryxgames/Messenger.git`

В таком случае **Messenger** скачается в текущую директорию

#### Скачивание из Github
Также вы можете скачать **Messenger** при помощи интерфейса *Github*

Нажмите на кнопку `Code`, а затем на `Download ZIP`

Необходимо распаковать скачанный архив в нужную директорию

*Теперь вы можете удалить скачанный архив*

### Завершение установки
Теперь вы можете создать ярлыки со следующими командами на рабочий стол:
```cmd
python "путь_к_файлу_server.py"
python "путь_к_файлу_main.py"
```

## Обновление Messenger
**Рекомендуется обновлять версию только из релизов**

Прочитайте, написано ли в релизе про *изменение формата хранения данных*. Если да, то **необходимо будет удалить все данные**, затем проделайте шаги, как в [*Скачивание репозитория*](#скачивание-репозитория)

Если написано, что *формат хранения данных не изменён*, или ничего не написано, проделайте шаги, как в [*Скачивание из Github*](#скачивание-из-github), но распакуйте только файлы `server.py` и `main.py`

# Обучение
## Основы
**Messenger** состоит из двух частей: **сервера** и **клиента**

Сервер хранит все данные и обрабатывает запросы от клиентов

Клиент показывает информацию от сервера в графическом виде

Чтобы запустить сервер, напишите
```cmd
python "путь_к_файлу_server.py"
```

Вы должны увидеть надпись `Сервер запущен`, иначе создайте проблему на вкладке [*Issues*](https://github.com/werryxgames/Messenger/issues)

**Перед надписью `Сервер запущен` может появиться дополнительная информация (`True`, `False` (несколько раз) и список с сообщениями)**. Это значит, что база данных сброшена до первоначального состояния. После этого рекомендуется выключить сервер и сделать то, что написано в [*Отключение сброса базы данных*](#отключение-сброса-базы-данных)

## Отключение сброса базы данных
Чтобы отключить сброс базы данных, необходимо зайти в файл `server.py` (пролистать в конец) и убрать все строки между этими **(оставьте сами строки, удалите все строки, на месте которых "...")**:
```python
if __name__ == "__main__":
    ...
    main()
```

# Примеры
## Аккаунты
**Вам понадобиться [включить сервер](#основы)**

Чтобы зайти в **Messenger** в первый раз, надо создать аккаунт. Для этого введите *логин* и *пароль* в соответствующие поля. Если всё правильно, то вы должны увидеть, как появится основной интерфейс **Messenger**\`а

Если интерфейс не появился, посмотрите в консоли, там должно была появиться ошибка на подобии следующей:
```
----------------------------
| ОШИБКА: Заголовок ошибки |
----------------------------
|     Описание ошибки      |
----------------------------
```

## Сообщения
Чтобы отправить сообщения, выберите получателя в списке слева, напишите текст сообщения справа внизу и нажмите 'Enter', или кнопку 'Отправить'

Внизу вашего сообщения написан его *статус*

Статусы сообщений:
1. Отправлено - Сообщение отправлено, но ещё не получено сервером
2. Доставлено - Сообщение доставлено на сервер, но ещё не получено получателем
3. Получено - Сообщение получено получателем, но он ещё не ответил
4. Прочитано - Сообщение получено получателем, который написал что-то после вашего сообщения

# Код
Код проверяется при помощи `flake8` и `pytest` *(тесты в папке tests)*:
```cmd
flake8 . --exclude venv,__pycache__,.git,.github
python -m pytest tests
```

## Функции и классы
### server.py - Модуль сервера
```python
absolute(path_: str) -> str  # Возвращает абсолютный путь из относительного

encrypt_password(user_id: int, password: str) -> str  # Шифрует пароль
    """Аргументы:
        user_id:    ID пользователя (используется как соль)
        password:   Пароль пользователя
    Возвращаемое значение:  Зашифрованный пароль
    """


class Database:  # Класс базы данных
    __init__(self, filepath: str) -> None  # Инициализация базы данных
        """Аргументы:
            filepath:   Путь к базе данных
        """

        self.__con  # Подключение к базе данных
        self.__cur  # Курсор базы данных для выполнения SQL

    sql(self, sql_text: str, format_: list[str | int | float, ...] = None, noresult: bool = False) -> bool | list | tuple  # Выполняет SQL код
        """Аргументы:
            sql_text:   SQL код
            format_:    Заменители '?' в SQL коде
            noresult:   Если включено, то результатом будет булевое значение
        Возвращаемое значение:
            bool:   Если включено noresult, возвращает True, если результат выполнения SQL кода пустой, иначе False
            list:   Массив с результатами
            tuple:  Единственный результат
        """

    reset_database(self) -> bool  # Сбрасывает базу данных к начальному состоянию
        """Возвращаемое значение: True, если удалось сбросить, иначе False"""

    create_account(self, name: str, password: str) -> int | list[int, list[int, ...]]  # Создаёт аккаунт
        """Аргументы:
            name:       Логин аккаунта
            password:   Пароль от аккаунта
        Возвращаемое значение:  Статус выполнения, id в случае успеха
        """

    login_account(self, name: str, password: str) -> int | list[int, list[int, ...]]  # Входит в аккаунт
        """Аргументы:
            name:       Логин аккаунта
            password:   Пароль от аккаунта
        Возвращаемое значение:  Статус выполнения, id в случае успеха
        """

    get_account_data(self, name: str) -> tuple[tuple[list[list[int, int, str, int, int], ...], list[list[int, int, str, int, int], ...]], list[int, ...]]  # Получает данные аккаунта
        """Аргументы:
            name:   Логин аккаунта
        Возвращаемое значение:
            [
                Отправленные и полученные сообщения,
                ID пользователей, чей статус сообщений был изменён
            ]
        """

    send_message(self, login: str, receiver: int, message: str) -> bool  # Создаёт запись в базе данных о сообщении

    close(self) -> None  # Закрывает базу данных


class NetworkedClient:  # Класс клиента
    _instances  # Все подключённые клиенты

    __init__(self, sock: socket.socket, addr: tuple[str, int]) -> None  # Инициализация клиента
        # sock - Сокет клиента
        # addr - Адрес клиента
        # _login - Логин клиента
        # id_ - ID клиента
        # __password - Пароль клиента

    encode_message(message: list | dict) -> bytes  # Превращает объекты, преобразоваемые в JSON в байты

    decode_message(message: bytes) -> list | dict  # Превращает байты в объекты, преобразоваемые в JSON

    send(self, message: list) -> None  # Отправляет сообщение клиенту
        """Аргументы:
            message:    Сообщение
        """

    send_account_data(self) -> None  # Отправляет данные об аккаунте

    receive(self, jdata: bytes) -> None  # Получает сообщение от клиента
        """Аргументы:
            jdata:  Данные от клиента
        """


main() -> None  # Основная функция
```

### main.py - Мессенджер на Python (клиент)
```python
class Window:  # Класс окна
    __init__(self, tk_window: tkinter.Tk) -> None  # Инициализация окна
        """Аргументы:
            tk_window:  Окно Tkinter
        """

    place(self, id_: str, element, *args, **kwargs) -> None  # Размещает объект element
        """Аргументы:
            id_:        Уникальный идентификатор элемента
            element:    Элемент, который необходимо разместить
            *args:      Аргументы element.place()
            **kwargs:   Позиционные аргументы element.place()
        """

    pack(self, id_: str, element, *args, **kwargs) -> None  # Размещает объект element
        """Аргументы:
            id_:        Уникальный идентификатор элемента
            element:    Элемент, который необходимо разместить
            *args:      Аргументы element.pack()
            **kwargs:   Позиционные аргументы element.pack()
        """

    __getattribute__(self, id_: str)  # Получает элемент по его ID
        """Аргументы:
            id_:    Уникальный идентификатор элемента

        Возвращаемое значение: Элемент
        """


class MessengerClient:  # Основной класс
    MAIN_BACKGROUND  # Основной фон
    SELECT_FOREGROUND  # Фон/цвет выбора
    MAIN_FOREGROUND  # Основной цвет
    SECOND_BACKGROUND  # Второй фон
    THIRD_BACKGROUND  # Третий фон
    MESSAGE_BACK_COLOR  # Фон сообщений пользователя
    MESSAGE_FORE_COLOR  # Цвет сообщений пользователя
    MESSAGE_BACK_COLOR2  # Фон других сообщений
    MESSAGE_FORE_COLOR2  # Цвет других сообщений
    _RECEIVE_SLEEP_TIME  # Задержка между получением сообщений от сервера

    __init__(self) -> None  # Инициализация класса
        self.root: tk.Tk  # Основное окно Tkinter
        self.win: Window  # Окно Window
        self._sock: socket.socket  # Сокет сервера
        self.__sended: list[list[int, int, str, int, int], ...]  # Все отправленные сообщения
        self.__received: list[list[int, int, str, int, int], ...]  # Все полученные сообщения
        self._logins: dict{int: str}  # Логины пользователей
        self._userid_selected: int  # ID выбранного пользователя
        self.last_height: int  # Последняя высота окна
        self._is_on_main_tab: bool  # На главной ли вкладке Messenger?
        self.__temp_messages: list[list[str, int], ...]  # Сообщения со статусом "Отправлено"

    show_error(title: str, message: str) -> None  # Показывает ошибку
        """Аргументы:
            title:      Заголовок ошибки
            message:    Описание ошибки
        """

    encode_message(message) -> bytes  # Превращает объекты, преобразоваемые в JSON в байты

    decode_message(message: bytes)  # Превращает байты в объекты, преобразоваемые в JSON

    send(self, message) -> None  # Отправляет сообщение message на сервер
        """Аргументы:
            message:    Сообщение
        """

    create_round_rectangle(
        cnv,
        px1,
        py1,
        px2,
        py2,
        radius,
        ign1=False,
        ign2=False,
        **kwargs
    ) -> int  # Создаёт скруглённый прямоугольник
        """Аргументы:
            cnv:    Холст Tkinter
            px1:    Левая точка прямоугольника
            py1:    Верхняя точка прямоугольника
            px2:    Правая точка прямоугольника
            py2:    Нижняя точка прямоугольника
            radius: Радиус скругления
            kwargs: Дополнительные аргументы tkinter.Canvas.create_polygon()

        Возвращаемое значение: ID Скруглённого прямоугольника на холсте
        """

    user_selected(self) -> None  # Обработчик события выбора пользователя
        """Аргументы:
            wid:    Виджет Listbox Tkinter
        """

    resize(self, event) -> None  # Обработчик изменения размера окна

    send_message(self, message: str) -> None  # Отправляет сообщение на сервер
        """Аргументы:
            message:    Сообщение
        """

    add_user(self, username: str) -> None  # Добавляет пользователя по имени
        """Аргументы:
            username:   Имя пользователя
        """

    receive(self) -> None  # Получает сообщения от сервера

    main(self)  # Основная функция клиента
```

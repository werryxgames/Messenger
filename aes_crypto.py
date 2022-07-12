"""Модуль для AES шифрования и дешифрования."""
from base64 import b64encode, b64decode
from hashlib import sha256
from Crypto.Cipher import AES
from Crypto import Random
from Crypto.Util.Padding import pad, unpad


class acrypt:
    """Класс для AES шифрования."""

    def __init__(self, key):
        """Инициализация класса."""
        self.block_size = AES.block_size
        self.__key = sha256(key.encode()).digest()

    def encrypt(self, rawdata):
        """Шифрует rawdata."""
        raw = rawdata + (
            self.block_size - len(rawdata) % self.block_size
        ) * chr(self.block_size - len(rawdata) % self.block_size)
        ivb = Random.new().read(AES.block_size)
        cipher = AES.new(self.__key, AES.MODE_CBC, ivb)
        return b64encode(ivb + cipher.encrypt(pad(
            raw.encode(),
            AES.block_size
        )))

    def decrypt(self, encrypted):
        """Расшифровывает encrypted."""
        enc = b64decode(encrypted)
        ivb = enc[:AES.block_size]
        cipher = AES.new(self.__key, AES.MODE_CBC, ivb)
        dec = unpad(cipher.decrypt(enc[AES.block_size:]), AES.block_size)
        return dec[:-ord(dec[len(dec) - 1:])].decode("utf8")

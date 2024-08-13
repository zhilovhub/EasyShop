from cryptography.fernet import Fernet
from common_utils.singleton import singleton


@singleton
class TokenEncryptor:
    """Is used to encrypt and decrypt bot tokens"""

    def __init__(self, secret_key: bytes) -> None:
        self.fernet = Fernet(key=secret_key)

    def encrypt_token(self, bot_token: str) -> str:
        """Encrypts the bot token"""
        return self.fernet.encrypt(bot_token.encode()).decode()

    def decrypt_token(self, bot_token: str | bytes) -> str:
        """Decrypts the bot token"""
        return self.fernet.decrypt(bot_token).decode()


if __name__ == "__main__":
    key = Fernet.generate_key().decode()  # to generate 32 url-safe base64-encoded bytes key
    print(key)

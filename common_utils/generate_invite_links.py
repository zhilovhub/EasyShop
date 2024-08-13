from string import ascii_letters

from random import choice


def generate_admin_invite_link(bot_username: str, length: int = 15) -> (str, str):
    letters = ascii_letters
    random_hash = "".join(choice(letters) for _ in range(length))
    link = f"t.me/{bot_username}?start=admin_{random_hash}"
    return random_hash, link

import random
import string


def generate_article():
    characters = string.ascii_letters + string.digits
    article = ''.join(random.choice(characters) for _ in range(5))
    return article
class KwargsException(Exception):
    """Is used to get detailed information about exception with params

    example: raise KwargsException(a=12, b=None, c=[1, 2, 3])
    """

    def __init__(self, **kwargs):
        if "bot_token" in kwargs:  # hide bot token
            bot_token = kwargs["bot_token"]
            kwargs["bot_token"] = bot_token[:5] + "*" * (len(bot_token) - 5)

        str_kwargs = ", ".join(map(lambda x: f"{x[0]}={x[1]}", kwargs.items()))
        super().__init__(str_kwargs)

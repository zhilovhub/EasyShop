from typing import Any, Optional, Dict

from aiohttp import web
from aiohttp.abc import Application

from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import TokenBasedRequestHandler

from common_utils.config import cryptography_settings
from common_utils.token_encryptor import TokenEncryptor


class EncryptedTokenBasedRequestHandler(TokenBasedRequestHandler):
    def __init__(
            self,
            dispatcher: Dispatcher,
            handle_in_background: bool = True,
            bot_settings: Optional[Dict[str, Any]] = None,
            **data: Any
    ) -> None:
        """
        Handler that supports multiple bots the context will be resolved
        from path variable 'encrypted_bot_token'

        :param dispatcher: instance of :class:`aiogram.dispatcher.dispatcher.Dispatcher`
        :param handle_in_background: immediately responds to the Telegram instead of
            a waiting end of handler process
        :param bot_settings: kwargs that will be passed to new Bot instance
        """
        super().__init__(dispatcher, handle_in_background, bot_settings, **data)
        self.token_encryptor: TokenEncryptor = TokenEncryptor(cryptography_settings.TOKEN_SECRET_KEY)

    def register(self, app: Application, /, path: str, **kwargs: Any) -> None:
        """
        Validate path, register route and shutdown callback

        :param app: instance of aiohttp Application
        :param path: route path
        :param kwargs:
        """
        if "{encrypted_bot_token}" not in path:
            raise ValueError("Path should contains '{encrypted_bot_token}' substring")
        super(TokenBasedRequestHandler, self).register(app, path=path, **kwargs)

    async def resolve_bot(self, request: web.Request) -> Bot:
        """
        Get bot encrypted token from a path and create or get from cache Bot instance

        :param request:
        :return:
        """
        encrypted_token = request.match_info["encrypted_bot_token"]
        token = self.token_encryptor.decrypt_token(bot_token=encrypted_token)

        if encrypted_token not in self.bots:
            self.bots[encrypted_token] = Bot(token=token, **self.bot_settings)
        return self.bots[encrypted_token]

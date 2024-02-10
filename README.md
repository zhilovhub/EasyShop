# EasyShop
p.s название пока временное, просто для определенности :)

## Работа с БД
Вместо ручного создания таблиц с помощью metadata.create_all(...) всё
происходит с помощью утилиты alembic <br/>
Установка alembic <br/>
pip install alembic

1. Нужно создать файл .env в корне проекта и задать значение переменной
SQLALCHEMY_URL
2. alembic revision --autogenerate -m "your_comment" - создание миграции, если
были изменения в структуре БД. В папке migrations/versions создатся новая ревизия.
ЕЕ НУЖНО ОБЯЗАТЕЛЬНО ПРОВЕРИТЬ НА НАЛИЧИЕ СИНТАКСИЧЕСКИХ ОШИБОК и исправить, если таковы ошибки будут
3. alembic upgrade 5273e9d542b9 (тут должна быть интересующая вас ревизия) для обновления БД до структуры, 
соответствующей ревизии с переданным номером. Можно писать alembic upgrade head
для обновления до последней ревизии

## Back-end
Для запуска необходимо в корневой директории прокета прописать команду <br/>
<code>uvicorn api.main:app --reload</code><br/>
Методы апи можно посмотреть тут (при запуске на локалхосте): <b>127.0.0.1/docs</b>

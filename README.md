# EzShop - правила и стиль разработки

- [Старт в разработке](#старт-в-разработке)
  - [Подключение к репозиторию GitLab из GitHub](#подключение-к-репозиторию-gitlab-из-github)
  - [Подключение к репозиторию GitLab из пустого проекта](#подключение-к-репозиторию-gitlab-из-пустого-проекта)
- [Совместная разработка](#Совместная-разработка)
  - [Ветки](#ветки)
  - [Старт разработки новой фичи](#старт-разработки-новой-фичи)
  - [Регулярные действия при разработке фичи](#регулярные-действия-при-разработке-фичи)
  - [Создание Pull Request](#создание-pull-request)
- [Стиль разработки](#стиль-разработки)
  - [Окончание разработки](#окончание-разработки)
  - [Получили уведомление о Pull Request](#получили-уведомление-о-pull-request)
  - [Оформление Pull Request](#оформление-pull-request)
  - [Проверка Pull Request](#проверка-pull-request)
  - [Документирование кода](#документирование-кода)
  - [Негласные правила нашего стиля](#негласные-правила-нашего-стиля)
  - [Обработка исключений](#обработка-исключений)
  - [Вызов исключений](#вызов-исключений)
  - [Логирование](#логирование)
  - [Декораторы и аннотации к функциям](#декораторы-и-аннотации-к-функциям)
  - [Модули](#модули)
- [Telegram Mini Apps и Frontend](#telegram-mini-apps-и-frontend)
- [Окружения и ссылки для разработчиков](#окружения-и-ссылки-для-разработчиков)

# Старт в разработке
## Подключение к репозиторию GitLab из GitHub
1. Открыть в локалке свой проект
2. Вбить `git remote -v`
3. Удалить все старые remote: `git remote remove <name>`
4. Зайти в [настройки профиля](https://gitlab.ezbots.ru/-/user_settings/ssh_keys)
   (**User Settings -> SSH Keys**)
5. Создать пару SSH ключей по [инструкции](https://docs.gitlab.com/17.2/ee/user/ssh.html#generate-an-ssh-key-pair)
6. Зайти в проект, скопировать SSH ссылку с **Git Clone**
7. На локальном устройстве в проекте `git remote add origin <ssh_project_link>`
8. Готово ✅

## Подключение к репозиторию GitLab из пустого проекта
1. Открыть в локалке свой проект
2. На локальном устройстве в проекте `git init`
3. На локальном устройстве в проекте `git checkout -b <new_branch_random_name>`
4. Зайти в [настройки профиля](https://gitlab.ezbots.ru/-/user_settings/ssh_keys)
   (**User Settings -> SSH Keys**)
5. Создать пару SSH ключей по [инструкции](https://docs.gitlab.com/17.2/ee/user/ssh.html#generate-an-ssh-key-pair)
6. Зайти в проект, скопировать SSH ссылку с **Git Clone**
7. На локальном устройстве в проекте `git remote add origin <ssh_project_link>`
8. На локальном устройстве в проекте `git fetch --all`
9. На локальком устройстве в проекте `git pull origin master_debug`
10. Решаем конфликты, если существуют
11. На локальном устройстве в проекте `git push --set-upstream origin <new_branch_random_name>` (имя ветки из пункта 3)
12. Готово ✅

# Совместная разработка
## Ветки
При разработке мы **не трогаем релизную версию пользователей**.  
Чтобы изолированно разрабатывать, у нас существуют три вида веток:
1. `master_release` - **запрещенная** для пушей ветка. В нее попадает оттестированное из `master_debug`
2. `master_debug` - в нее делаем [Pull Requests](https://docs.gitlab.com/ee/user/project/merge_requests/creating_merge_requests.html)
3. **Остальные ветки** - ветки, создающиеся другими разработчиками для разработки фичей

## Старт разработки новой фичи
1. `git checkout master_debug` - откатываемся к главной дебажной ветке
2. `git pull origin master_debug` - подтягиваем самые свежие изменения
3. `git checkout -b <new_branch_name>` - создаём новую ветку от `master_debug`
4. `git push -u origin master_debug` - отправляем новую ветку на GitLab

## Регулярные действия при разработке фичи
- ❗️ **ВАЖНО:** ❗️При работе в своей ветке каждый день первым делом делать следующие две команды:
  - `git fetch --all`
  - `git rebase origin/master_debug`

## Создание Pull Request
- Перед тем, как создать Pull Request, выполняем:
  - `git fetch --all`
  - `git rebase origin/master_debug`
- Создаём Pull Request
  1. target-ветка: `master_debug`
  2. **В описании пишем основные файлы**, на которые нужно обратить внимание
  3. Отмечаем галочками:
     - `squash commits`
     - `Delete source branch`

# Стиль разработки
## Окончание разработки
- Всегда, когда заканчиваете разработку фичи:
  1. Убедиться, что у вас нет **ни одного нарушения PEP8** (скоро в CI/CD будет автоматическая проверка на это)
  2. Создать `Pull Request`
  3. **Уведомить в беседе** (несмотря на то, что приходят уведомления)

## Получили уведомление о Pull Request
- **Проверяете самостоятельно сразу** без каких-либо напоминаний. Это обязанность каждого разработчика

## Оформление Pull Request
- [Здесь](#создание-pull-request) я писал, как его создавать с технической точки зрения. Теперь поговорим
**об описании** `Pull Request`
- При создании `Pull Request` учтите, что зачастую у Вас очень много изменений, который затрагивают
разные части кода. Для нас **важно** сделать процесс проверки максимально быстрым эффективным. 
- Для этого:
  1. **В описании Pull Request *кратко (одним предложением) объяснять*, на что стоит обратить внимание**

## Проверка Pull Request
- При проверке мы обращаем внимание на:
    1. ***Чистоту кода***
    2. Выполнение всех заявленных задач
    3. Логику кода

## Документирование кода
Всегда при написании функции, класса, документируем с помощью `docstring`  
Итого:
1. **Каждую функцию и класс помечаем хотя бы одной строчкой**
2. **Сложные участки кода комментируем отдельно с помощью решетки**
   - Пример: [пояснение ожидаемого результата](https://gitlab.ezbots.ru/zhilovhub/EasyShop/-/blob/master_debug/bot/middlewaries/subscription_middleware.py#L31)
3. **❗️ Самое важное:** в документации прописываем **все** исключения, которые функция может выбросить
   - Пример: [документирование исключений](https://gitlab.ezbots.ru/zhilovhub/EasyShop/-/blame/master_debug/database/models/bot_model.py?ref_type=heads#L192-199)

## Негласные правила нашего стиля
1. Не нарушать **PEP8**
2. Соблюдать **структурность импортов** ([пример](https://gitlab.ezbots.ru/zhilovhub/EasyShop/-/blob/master_debug/bot/handlers/admin_bot_menu_handlers.py#L1-67))
   - Все должно быть лесенкой. Это порядок и отсуствие хаоса
3. Соблюдать **структурность вместе взятых переменных и функций** ([пример](https://gitlab.ezbots.ru/zhilovhub/EasyShop/-/blob/master_debug/database/config.py?ref_type=heads#L29-48))
4. Если что-то повторяется **минимум 2 раза** - выносим в отдельную функцию
5. Названия функциям, которые работают **только в рамках одного файла или класса**, даем с префиксом `_`
   ([пример](https://gitlab.ezbots.ru/zhilovhub/EasyShop/-/blame/master_debug/bot/post_message/post_message_callback_handler.py?ref_type=heads#L885))
6. Не оканчивать последние предложения точками (в текстах для пользователей)
7. В длинных **вызовах** строки переносим следующим образом:
   - **Было:**
     - ```python 
       await query.message.answer(MessageTexts.BOT_CHANNELS_LIST_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username), reply_markup=await InlineChannelsListPublishKeyboard.get_keyboard(custom_bot.bot_id, callback_data.pid, callback_data.msg_id))
   - **Стало:**
     - ```python 
       await query.message.answer(
                MessageTexts.BOT_CHANNELS_LIST_MESSAGE.value.format((await Bot(custom_bot.token).get_me()).username),
                reply_markup=await InlineChannelsListPublishKeyboard.get_keyboard(
                    custom_bot.bot_id,
                    callback_data.pid,
                    callback_data.msg_id
                )
            )
       ```
8. В длинных **объявлениях функции** строки переносим следующим образом:
   - **Было:**
     - ```python 
       async def send_post_message(bot_from_send: Bot | BotSchema, to_chat_id: int, post_message_schema: PostMessageSchema, media_files: list[PostMessageMediaFileSchema], post_action_type: PostActionType, message: Message = None, is_delayed: bool = True) -> None:
   - **Стало:**
     - ```python 
       async def send_post_message(
            bot_from_send: Bot | BotSchema,
            to_chat_id: int,
            post_message_schema: PostMessageSchema,
            media_files: list[PostMessageMediaFileSchema],
            post_action_type: PostActionType,
            message: Message = None,
            is_delayed: bool = True
       ) -> None:
       ```


## Обработка исключений
- В разделе [Документирование кода](#документирование-кода) было упомянуто **документирование исключений**
   - Используя **горячие клавиши** среды разработки (например, `Ctrl Q` в `PyCharm`), всегда проверяем, что выбрасывает
    функция. И ***обрабатываем все исключения***

## Вызов исключений
- Когда создаем **свою ошибку**, наследуемся от класса [KwargsException](https://gitlab.ezbots.ru/zhilovhub/EasyShop/-/blame/master_debug/database/exceptions/exceptions.py?ref_type=heads#L1)
- При выбросе этого исключения наполняем его **контекстом**
  - ```python
    class MyException(KwargsException):
        """Raised when something happens"""
    
    raise MyException(user_id=user_id, bot_id=data.bot_id)  # you can pass whatever you want

## Логирование
- Всегда стараемся заполнить **контекст** как можно бОльшим количеством информации
  ([как заполнять контекст](https://gitlab.ezbots.ru/zhilovhub/EasyShop/-/blame/master_debug/logs/config.py#L24))
- Есть 4 типа логгеров: `logger`, `db_logger`, `api_logger`, `custom_bot_logger`
  - Каждый применяем только там, где он действительно нужен
- **Формат логгирования**:
  - `f'main_context=<main_context_value>: <action> <type> <object>'`
  - Пример:
    - ```python
      self.logger.debug(
            f"bot_id={new_mailing.bot_id}: added mailing {mailing_id} -> {new_mailing}",
            extra=extra_params(bot_id=new_mailing.bot_id, mailing_id=mailing_id)
        )

## Декораторы и аннотации к функциям
- Каждую БДшную функцию помечаем декоратором `validate_call(validate_return=True)`
- В каждой функции **аннотируем** все аргументы и результат
  - Пример: 
    - ```python
        @validate_call(validate_return=True)
        async def example_db_function(a: int, b: SomeClass) -> SomeClass | None:
            pass

## Модули
- Главные модули:
  1. `bot`
  2. `api`
  3. `custom_bots`
  4. `common_utils`

- Все, что относится только к одному модулю, внутрь этого модуля и вписываем
- Если что-то общее, прописываем в `common_utils`
- `bot, api, custom_bots` **не должны зависеть друг от друга никак**

# Окружения и ссылки для разработчиков
1. **Релизный бот**
   - *Бот*: [@ezShopOfficial_bot](https://t.me/ezShopOfficial_bot)
   - *Документация АPI*: https://ezbots.ru/api/docs
   - *Веб-Аппа*: https://ezbots.ru/
   - *МультиБоты*: https://ezbots.ru:8443/<label>/webhook/bot/
   - *База данных*: секрет
   - ***Лейбл***: `release`
2. **Дебажный бот**
   - *Бот*: [@ezshopdebug_bot](https://t.me/ezshopdebug_bot)
   - *Документация АPI*: https://ezbots.ru:2024/docs
   - *Веб-Аппа*: https://ezbots.ru:228/
   - *МультиБоты*: https://ezbots.ru:88/<label>/webhook/bot/ (redirect to `4444`)
   - *База данных*: секрет
   - ***Лейбл***: `debug` 
3. **Бот Ильи**
   - *Бот*: [@experiment12423_bot](https://t.me/experiment12423_bot)
   - *Документация АPI*: https://ezbots.ru:1535/docs
   - *Веб-Аппа*: https://ezbots.ru:1534/
   - *МультиБоты*: https://ezbots.ru:88/<label>/webhook/bot/ (redirect to `4447`)
   - *База данных*: `postgres:wweof@92.118.114.106:7000/dev_ezshop`
   - ***Лейбл***: `debug` 
4. **Бот Вовы**
   - *Бот*: [@EasyShop_test_bot](https://t.me/EasyShop_test_bot)
   - *Документация АPI*: https://ezbots.ru:1533/docs
   - *Веб-Аппа*: https://ezbots.ru:1532/
   - *МультиБоты*: https://ezbots.ru:88/<label>/webhook/bot/ (redirect to `4446`)
   - *База данных*: `postgres:oe_233@92.118.114.106:7001/dev_ezshop`
   - ***Лейбл***: `debug` 
5. **Бот Арсена**
   - *Бот*: [@ArsenixBotForTestsbot](https://t.me/ArsenixBotForTestsbot)
   - *Документация АPI*: https://ezbots.ru:1531/docs
   - *Веб-Аппа*: https://ezbots.ru:1530/
   - *МультиБоты*: https://ezbots.ru:88/<label>/webhook/bot/ (redirect to `4445`)
   - *База данных*: `postgres:oe_233@92.118.114.106:7002/dev_ezshop`
   - ***Лейбл***: `debug` 
6. **Бот Кирилла**
   - *Бот*: [@karfogent_GG_bot](https://t.me/https://t.me/karfogent_GG_bot)
   - *Документация АPI*: https://ezbots.ru:1537/docs
   - *Веб-Аппа*: https://ezbots.ru:1536/
   - *МультиБоты*: https://ezbots.ru:88/<label>/webhook/bot/ (redirect to `4448`)
   - *База данных*: `postgres:loq23@92.118.114.106:7003/dev_ezshop`
   - ***Лейбл***: `debug` 
   
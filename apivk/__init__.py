import re
import aiohttp
import json
import asyncio
from requests import get
# from os.path import exists
from typing import Tuple, List

# TODO: example program
if __name__ == '__main__':
    # if exists('bot.py'):
    print('You cannot run this module.')
    # else:
    #     with open('bot.py', 'w') as file:
    #         file.write("import main\n"
    #                    "\n"
    #                    "api = main.API(\"token\")\n"
    #                    "# default version - 5.103, if you need another - add parameter v=version (int)\n"
    #                    "\n\n"
    #                    "@api.MessageHandler('/test')\n"
    #                    "async def test(msg: main.Message):\n"
    #                    "    await msg.reply('test!')")
    quit()


# class APIError(Exception):
#     def __init__(self, *args):
#         super().__init__(self, *args)


class API:

    def __init__(self, token: str, v=5.103):
        class _requester:
            def __init__(self, att, api: API):
                self.att = att
                self.api = api

            def __getattr__(self, item, _token=False):
                _r = f'{self.att}.{item}?'

                def form(_args, _r):
                    for _k, _v in _args.items():
                        _r += str(_k) + '=' + str(_v) + '&'
                    return _r[:-1]

                return lambda _r=_r, _token=_token, **_kwargs: self.api.request(form(_kwargs, _r), token=_token)

        # проверка работоспособности токена
        # TODO: проверка прав токена & проверка прав в зависимости от используемых методов (future)
        with get(f'https://api.vk.com/method/utils.getServerTime?access_token={token}&v={v}') as _req:
            assert 'error' not in json.loads(_req.text)

        with get(f'https://api.vk.com/method/groups.getById?access_token={token}&v={v}') as _req:
            self.__id = json.loads(_req.text)['response'][0]['id']
        self.__token = token
        self.__v = v
        self.__hcom = {}  # словарь команда:метод
        self.__attrwrapper = _requester

    @staticmethod
    async def __request(_url: str):
        async with aiohttp.ClientSession() as _session:
            async with _session.get(_url) as _response:
                try:
                    return json.loads(await _response.text())
                except json.decoder.JSONDecodeError as e:
                    print('FAILED:', e, 'RESPONSE:', await _response.text())

    async def request(self, __t, token=False):
        return await self.__request("https://api.vk.com/method/" +
                                    __t + f'{"&access_token=" + self.__token if not token else "&access_token=" + str(token)}&v={self.__v}')

    # декоратор для методов сообщений
    def MessageHandler(self, *args, arg=0, _all=False):
        if callable(args[0]) or  (not isinstance(args[0], list) and not isinstance(args[0], str)):
            raise TypeError("You must add commands in list or one command (String) to positional arguments")

        # if not isinstance(args[0], list) and not isinstance(args[0], str):
        #     raise TypeError("You must add commands in list or one command (String) to positional arguments")

        def binder(f):
            # assert callable(f) or asyncio.iscoroutinefunction(f)
            # проверка на асинхронность функции обработки сообщения
            assert asyncio.iscoroutinefunction(f)
            if isinstance(args[0], list):
                print([args[0].pop(_i[0]) for _i in enumerate([_j for _j in args[0] if _j in self.__hcom.keys()])])
                for _i in args[0]:
                    self.__hcom.update({_i: (f, arg)})
            else:
                # self.__hcom.update({args[0]: (f, arg, asyncio.iscoroutinefunction(f))}) if args[0] not in
                # self.__hcom else None
                self.__hcom.update({args[0]: (f, arg)}) if args[0] not in self.__hcom else None
            return lambda: print('This method is used in apivk')

        return binder

    # TODO: Обработка событий
    def __EventHandler(self, _event: str):
        pass

    # Метод получения адреса сервера LongPoll
    async def __getLongPoll(self) -> (str, int):
        while True:
            _response = await self.__request(
                f'https://api.vk.com/method/groups.getLongPollServer?access_token={self.__token}&group_id={self.__id}&v={self.__v}')
            if "error" in _response:
                print('ERR:', _response)
                await asyncio.sleep(5)
                continue
            _response = _response['response']
            return f'{_response["server"]}?act=a_check&key={_response["key"]}&', _response['ts']

    # Метод запуска асинхронного цикла
    # TODO: Адаптация к новым версиям API
    async def __main(self, loop):
        _last = None
        _s, _ts = await self.__getLongPoll()
        while True:
            # TODO: debug prints
            print(_s + 'ts=' + str(_ts))
            _resp = await self.__request(str(_s + 'wait=25&ts=' + str(_ts)))
            if "failed" in _resp:
                _s, _ts = await self.__getLongPoll()
                await asyncio.sleep(2)
                continue
            for upd in _resp['updates']:
                print(upd)
                if upd is not _last:
                    _last = upd
                    if upd['type'] == 'message_new':
                        if 'text' in upd['object']['message']:
                            # ветка в случае отсутствия аргументов в сообщении
                            # TODO: !!! blank message handling
                            if ' ' not in str(upd['object']['message']['text']):
                                if str(upd['object']['message']['text']) in self.__hcom:
                                    if self.__hcom[upd['object']['message']['text']][1] == 0:
                                        loop.create_task(self.__hcom[upd['object']['message']['text']][0](
                                            Message(upd['object']['message'], self)))
                                    else:
                                        loop.create_task(self.__hcom[upd['object']['message']['text']][0](
                                            Message(upd['object']['message'], self), []))
                            else:
                                _message = str(upd['object']['message']['text'])
                                # удаление пуша (если есть)
                                _message = re.sub(r'\[club\d+\|.*\]', '', _message).strip().split(' ')
                                if _message[0] in self.__hcom:
                                    if self.__hcom[_message[0]][1] == 0:
                                        # loop.create_task(self.__hcom[upd['object']['message']['text']][0](
                                        #     Message(upd['object']['message'], self)))
                                        # Добавление в Event Loop метода-обертки сообщения, передача объекта Message
                                        loop.create_task(self.__hcom[_message[0]][0](
                                            Message(upd['object']['message'], self)))
                                    else:
                                        pass
                                        # ветка в случае ивента, не являющегося message_new
                                        # TODO: another events handling
                                        # loop.create_task()
            # print(_resp)
            # print(_ts)
            _ts = str(int(_ts) + 1)

    def launch(self):
        _loop = asyncio.get_event_loop()
        _loop.run_until_complete(self.__main(_loop))

    def __getattr__(self, item):
        return self.__attrwrapper(item, self)


class Message:
    def __init__(self, data, api: API, args: List[Tuple[int, str]] = None):
        self.__data = data
        self.__apiobj = api
        self.args = args if args is not None else []
        self.text = data['text']
        self.user_id = data['from_id']
        self.peer = data['peer_id']
        self.ischat = True if self.peer >= 2000000000 else False
        self.id = data['id']

    # метод ответа на сообщение
    async def reply(self, text: str, forward=False, **kwargs) -> int or dict:
        _kw = ''
        # добавление доп. параметров
        if len(kwargs) != 0:
            _kw += '&'
            for k, v in kwargs.items():
                _kw += str(k) + '=' + str(v) + '&'
            _kw = _kw[:-1]  # удаление последнего символа &
        _r = await self.__apiobj.request(f'messages.send?'
                                         f'message={text}&{f"reply_to={self.id}&" if forward else ""}'
                                         f'{"user_id=" + str(self.user_id) if self.peer < 2000000000 else "chat_id=" + str(self.peer - 2000000000)}&'
                                         f'random_id=0{_kw}')
        # возврат id сообщения в случае удачи
        return int(_r['response']) if len(_r) == 1 and 'response' in _r else _r

    async def read(self):
        # метод markAsRead работает исключительно для личных бесед
        if not self.peer >= 2000000000:
            await self.__apiobj.request(f'messages.markAsRead?peer_id={self.peer}')
        else:
            print('message with id', self.id, 'is in the conversation')

    # получение любых параметров объекта Message
    def __getattr__(self, item):
        return self.__data[item] if item in self.__data else None

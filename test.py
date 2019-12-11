import apivk
import asyncio
import requests

a = apivk.API('d0c5d732eb3b313690df015972727e9881ecb48045dfe0c9dff0bbef92c6d68445031b0c80b7814e1d835', v=5.103)


@a.MessageHandler(['/ban', '/бан'])
async def ban(msg: apivk.Message):
    await msg.read()
    print('asdas', msg.args)


@a.MessageHandler('/прикол')
async def prikol(msg: apivk.Message):
    print(msg.text)
    print(msg.peer_id)
    print(msg.peer)
    print(await msg.reply('Рина я тебя люблю.', keyboard='{"one_time":true,"buttons":[[{"action":{"type":"text","payload":"{\\"button\\": \\"1\\"}","label":"ебать блять"},"color":"default"}],[{"action":{"type":"text","payload":"{\\"button\\": \\"1\\"}","label":"ахахахаха"},"color":"primary"}],[{"action":{"type":"text","payload":"{\\"button\\": \\"1\\"}","label":"КРОВЬ"},"color":"negative"}]]}'))

a.launch()
import time # time.time() для времени. Используется для промежутков бонуса, бизнеса и др
import random
import logging
import asyncio
import io

from telethon import types
from .. import loader, utils

TLG_JOHNNY = 419089999
TLG_GAY = 944645249
GAY = 0 #You a gay?

stats = {}

@loader.tds
class AutoLesyaMod(loader.Module):
	"""Account Dispatcher"""
	strings = {"name": "Account Dispatcher"}

	async def client_ready(self, client):
		await client.send_message(lesya, "Профиль")

	async def parseprofile(self, text):
		global stats
		stats["has"] = True
		id_format = "ID: "
		id_str = text.find(id_format)
		id_start = id_str + len(id_format)
		id_end = text.find("\n", id_start)
		stats["id"] = text[id_start:id_end]
		await client.send_message(lesya, "ID - "+str(stats.get("id")))

	async def gaycmd(self, message):
		"""Изменение руководителя"""
		global GAY
		if GAY:
			GAY = 1
			await utils.answer(message, "@makcvvv - <code>Властелин очка</code>\n@karlend - <code>Братик</code>")
		else:
			GAY = 0
			await utils.answer(message, "@makcvvv - <code>Братик</code>\n@karlend - <code>Властелин очка</code>")

	async def receive(self, message): # Сообщение от бота
		text = message.text.lower()
		if not text:
			return
		# Инфа из профиля
		if "ваш профиль" in text: # Инфа по профилю привет
			await self.parseprofile(text)

	async def receivechat(self, message): # сообщения в канале с ботом
		text = message.text.lower()
		user_id = message.from_id or 0

		if (text == "Я гей"):
			if user_id == TLG_GAY:
				if not stats.get("has"):
					return
				await utils.answer(message, "Я тоже "+str(stats.get("id")))
				return
      
	async def watcher(self, message):
		if not isinstance(message, types.Message):
			return
		if not message.text:
			return
		if message.from_id == self._me.id:
			return
		chat_id = utils.get_chat_id(message)
		if chat_id == lesya:
			await self.receive(message)
		elif chat_id == lesya_chat:
			asyncio.ensure_future(self.receivechat(message))

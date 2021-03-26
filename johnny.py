# requires: captcha-solver

import time  # time.time() для времени. Используется для промежутков бонуса, бизнеса и др
import random
import logging
import asyncio
import io

from math import floor
from datetime import timedelta

from telethon import types
from captcha_solver import CaptchaSolver
from .. import loader, utils

logger = logging.getLogger("AutoLesya")

lesya = 757724042  # ID бота
lesya_chat = 1462806544

TLG_JOHNNY = 419089999

times = {
	"bonus": 0,
	"vip_bonus": 0,
	"premium_bonus": 0,
	"premium_money": 0,

	"work": 0,
	"fight": 0,

	"opencase": 0,

	"pet_bitcoin": 0,
	"pet_stimulator": 0,
	"pet_food": 0,
	"pet_cases": 0,

	"clan_war": 0,
	"clan_war_upgrade": 0,
	"clan_heist": 0,

	"trade": 0,
	"cup": 0,
	"casino": 0
}

cooldowns = {
	"bonus": 60,

	"work": 10,
	"fight": 5,

	"opencase": 60,

	"trade": 5,
	"cup": 5,
	"casino": 5,

	"etc": 10,
}

cooldowns_hints = {
	"bonus": "🔔 Бонус",
	
	"work": "👔 Работа",
	"fight": "🤺 Бои",

	"opencase": "🧳 Между открытием кейсов",

	"trade": "🔧 Авто-трейд",
	"cup": "🥤 Авто-стакан",
	"casino": "🎰 Авто-сазино",

	"etc": "📝 Остальное"
}

stats = {}

formats = {
	"bonus": ("бонус будет доступен", "бонус станет доступен", "сможете получить бонус", "сможете получить v.i.p бонус", "сможете получить premium бонус"),
	"bonus_money": "получить валюту можно будет только через",

	"work": "вы сможете работать через",
	"work_new": "💡 доступна новая работа!",

	"id": "🔎 id: ",

	"banned": "вы заблокированы на"
}

settings_tip = {
	"fight": "🤺 Бой",
	"job": "👔 Работа",
	"bonus": "🔔 Бонус",

	"opencase": "🧳 Открытие кейсов",

	"pet_bitcoin": "🅱️ Сбор биткоинов перед покупкой",
	"pet_stimulator": "💊 Стимулятор питомцев",
	"pet_food": "🥫 Корм питомцев",
	"pet_cases": "💼 Множитель кейсов питомцев",
	#"pet_helper": "📑 Расчёт лучшего питомца",

	"clan_war": "⚔️ Клановые войны",
	"clan_heist": "🔫 Ограбление",
	"clanbuy": "💸 Закуп для ограбления",

	"auto_trade": "🔧 Трейд на всё",
	"auto_cup": "🥤 Стакан на всё",
	"auto_casino": "🎰 Казино на всё"
}

settings = {}


def convert(str_):
	arr = str_.split(":")
	last = len(arr)
	try:
		if last == 4:  # D:H:M:S
			return int(arr[0][:2]) * 86400 + int(arr[1][:2]) * 3600 + int(arr[2][:2]) * 60 + int(arr[3][:2])
		elif last == 3:  # H:M:S
			return int(arr[0][:2]) * 3600 + int(arr[1][:2]) * 60 + int(arr[2][:2])
		elif last == 2:
			return int(arr[0][:2]) * 60 + int(arr[1][:2])
		else:
			return int(arr[0][:2])
	except ValueError:
		logger.error(f"CONVERT ERROR WHILE PARSING {str_!r}")
		return -1

def timetostr(tmp):
	if tmp <= 0:
		return "Готово"
	return str(timedelta(seconds=floor(tmp)))


@loader.tds
class AutoLesyaMod(loader.Module):
	"""Автоматизация LesyaBot"""
	strings = {"name": "LesyaBot"}

	def gen_time(self, mode="etc"):
		time = cooldowns.get(mode) or 10
		return random.randint(0, time)

	async def send_bot(self, text):
		# await asyncio.sleep(random.randint(0, self.db_get("cooldown_time", 10)))
		await self._client.send_message(lesya, text)

	async def send_group(self, text):
		await self._client.send_message(lesya_chat, text)

	def set_time(self, time_name, entry):
		global times
		times[time_name] = entry
		self.db_set("time_" + time_name, entry)

	def bot_loaddb(self):
		# Подгрузка времени
		global times
		for time_name in times:
			last = self.db_get("time_" + time_name, 0)
			times[time_name] = last
		# Настройки из lsettings
		global settings
		for cmd in settings_tip:
			has = self.db_get(cmd)
			settings[cmd] = has
		# Настройки куллдаунов
		global cooldowns
		for mode in cooldowns:
			wait = self.db_get("cooldown_" + mode)
			if wait is None:
				continue
			cooldowns[mode] = wait
	
	def solver(self, data):
		logger.info("Получаю ключ")
		key = self.db_get("api_token")
		logger.info("Получил ключ")
		func = CaptchaSolver("rucaptcha", api_key=key).solve_captcha
		logger.info("Создал функцию")
		return func(data)

	async def client_ready(self, client, db):
		self._me = await client.get_me()
		self._client = client
		self._db = db
		self.bot_loaddb()
		await self.send_bot("Профиль")
		await asyncio.sleep(1)
		asyncio.ensure_future(self.timer())

	async def setcaptchatokencmd(self, message):
		"""Указать токен RuCaptcha"""
		api_token = utils.get_args_raw(message)
		self.db_set("api_token", api_token)
		await utils.answer(message, "<b>Есть!</b>")

	async def getcaptchatokencmd(self, message):
		"""Получить токен RuCaptcha"""
		token = self.db_get("api_token", "Не установлен")
		await utils.answer(message, token)

	def set_cooldown(self, mode, seconds):
		global cooldowns
		cooldowns[mode] = seconds
		self.db_set("cooldown_" + mode, seconds)

	async def lcooldowncmd(self, message):
		"""Указать время задержки между командами"""
		text = utils.get_args_raw(message)
		if not text:
			reply = "<b>⌛ Инфомация о заддержках</b>"
			for cd in cooldowns:
				name = cooldowns_hints.get(cd) or "Unknown"
				wait = cooldowns.get(cd) or 0
				reply = reply + "\n<b>" + name + "</b> ( <code>" + cd + "</code> ) - " + timetostr(wait)

			reply = reply + "\n\n<b>💬 Для установки введите</b> <code>.lcooldown type time</code>"
			await message.edit(reply)
			return
		args = text.rsplit(" ", 1)
		mode = args[0]
		if len(args) != 2 or not mode in cooldowns:
			await message.edit("<b>Неверный формат! .lcooldown type seconds</b>")
			return
		time = args[1]
		try:
			cd_time = int(time)
		except ValueError:
			await message.edit("<b>Ошибка, укажите время в секундах (без суффикса \"s\", просто число вторым аргументом)</b>")
			return
		if cd_time < 0:
			await message.edit("<b>Время должно быть равно 0 или больше</b>")
			return
		self.set_cooldown(mode, cd_time)
		await message.edit("<b>Есть!</b>")

	def settings_set(self, name, var):
		global settings
		settings[name] = var
		self.db_set(name, var)

	async def lsettingscmd(self, message):
		"""Настройки LesyaBot"""
		text = utils.get_args_raw(message)
		reply = ""
		if not text or not settings_tip.get(text):
			reply = "⚙️ <b>Доступные настройки:</b>"
			for cmd in settings_tip:
				enabled = self.db_get(cmd) and "♿️" or ""
				description = settings_tip[cmd]
				reply = reply + "\n" + enabled + description + " - <code>" + cmd + "</code>"

			reply = reply + "\n\n" + "<b>♿ - Индикатор, что функция активна\nФункции с припиской</b>\n\n<b>Для включения/отвключения введите</b> <code>.lsettings var_name</code>"
		else:
			description = settings_tip.get(text)
			should = not settings.get(text)
			reply = description + " - <b>" + (should and "Включено" or "Отключено") + "</b>"
			self.settings_set(text, should)
			
		await message.edit(reply)

	async def solvecmd(self, message):
		"""Тестовая команда для проверка решения капчи"""
		await message.edit("Ждём ответа...")
		x = await self.solve_captcha(await message.get_reply_message())
		await message.edit(("Ответ: "+str(x)) if x else "<b>Укажите ключ с помощью .setcaptchatoken</b>")

	async def lesyainfocmd(self, message):
		"""Инофрмация о скрипте и инфе, какую собрал"""
		if times.get("banned", None):
			now = time.time()
			wait = times.get("banned") - now
			await message.edit("<b>Я в бане\nОсталось: " + timetostr(wait) + "</b>")
			return
		elif not stats.get("has", None):
			await message.edit("<b>Информация не найдена</b>")
			return

		now = time.time()
		text = "<b>Инфа в Бот Леся</b>" + "\n" \
			"☺️ Мой айди - <code>" + str(stats.get("id")) + "</code>\n" \
			"🤔 Статус: " + (stats.get("premium") and "Premium" or stats.get("vip") and "VIP" or "Игрок") + "\n" \
			"👨‍👦‍👦 Клан: " + (stats.get("clan") and "Есть" or "Нету") + "\n" \
			"💻 Фермы: " + (stats.get("bitcoin") and "Есть" or "Нету") + "\n\n" \
			"<b>Инфа по таймингам</b>" + "\n" \
			"💰 Бонус: " + timetostr(times.get("bonus") - now) + "\n"
		if stats.get("vip"):
			text = text + "💳 Вип бонус: " + timetostr(times.get("vip_bonus") - now) + "\n"
		if stats.get("premium"):
			text = text + "💸 Премиум бонус: " + timetostr(times.get("premium_bonus") - now) + "\n"
			text = text + "🤑 Премиум валюта: " + timetostr(times.get("premium_money") - now) + "\n"
		if times.get("work") > 0:
			text = text + "🛠️ Работа: " + timetostr(times.get("work") - now) + "\n"
		battle = times.get("fight") - now
		if battle < 10**50:
			text = text + "🤺 Бои: " + timetostr(battle) + "\n"
		if settings.get("pet_stimulator"):
			text = text + "💊 Стимуляторы: " + timetostr(times.get("pet_stimulator") - now) + "\n"
		if settings.get("pet_food"):
			text = text + "🥫 Корм: " + \
				timetostr(times.get("pet_food") - now) + "\n"
		if settings.get("pet_cases"):
			text = text + "💼 Множитель кейсов: " + timetostr(times.get("pet_cases") - now) + "\n"
		if settings.get("opencase"):
			text = text + "🧳 Открытие кейса: " + timetostr(times.get("opencase") - now) + "\n"
		if settings.get("clan_war"):
			text = text + "⚔️ Клановая война: " + timetostr(times.get("clan_war") - now) + "\n"
			if times.get("clan_war_upgrade") != 0:
				text = text + "🦽 Апгрейд питомцев: " + timetostr(times.get("clan_war_upgrade") - now) + "\n"
		if settings.get("clan_heist"):
			text = text + "🔫 Ограбление: " + timetostr(times.get("clan_heist") - now) + "\n"
		if self.db_get("api_token") == None:
			text = text + "⚠️ <b>Токен капчи не указан</b>"
		await message.edit(text)

	async def solve_captcha(self, message):
		if not self.solver:
			logger.info("no self.solver")
			return
		logger.info("creating io data")
		file_loc = io.BytesIO()
		logger.info("downloading file")
		logger.info(message)
		await message.download_media(file_loc)
		logger.info("geting value from file")
		bytes_ = file_loc.getvalue()
		logger.info("solving with self.solver")
		return self.solver(bytes_)

	async def parseprofile(self, text):
		global stats
		stats["has"] = True
		id_format = formats.get("id")
		id_str = text.find(id_format)
		id_start = id_str + len(id_format)
		id_end = text.find("\n", id_start)
		stats["id"] = text[id_start:id_end] or "null"
		stats["premium"] = "статус: premium" in text
		stats["vip"] = "статус: v.i.p" in text or "статус: premium" in text
		stats["work"] = "работа:" in text
		stats["clan"] = "клан:" in text
		stats["bitcoin"] = "ферма:" in text
		logger.info("Got profile")

	def parsebonus(self, text):
		logger.info("parsing bonus")
		logger.info(text)
		global times
		vip = "v.i.p" in text
		premium = "premium" in text
		bonus_type = vip and "vip_bonus" or premium and "premium_bonus" or "bonus"
		now = time.time()

		timestr = text.rsplit(" ", 2)
		if ":" not in (timestr[-1]):
			timestr.pop(-1)
		need = convert(timestr[-1])
		self.set_time(bonus_type, now + need + 30)
		logger.info("before bonus need to wait " + str(need))

	def parsemoneybonus(self, text):
		logger.info("parsing money bonus")
		logger.info(text)
		global times
		now = time.time()

		timestr = text.rsplit(" ", 2)
		if ":" not in (timestr[-1]):
			timestr.pop(-1)
		need = convert(timestr[-1])
		self.set_time("premium_money", now + need + 30)
		logger.info("before money bonus need to wait " + str(need))

	def parsejob(self, text):  # время для работы
		global times
		now = time.time()

		line = text.split("\n")[1]
		timestr = line.rsplit(" ", 1)[1]
		need = convert(timestr)
		self.set_time("work", now + need + self.gen_time("work"))
		logger.info("before work need to wait " + str(need))

	def parse_last_entry(self, text):
		last = "1"
		lines = text.split("\n")
		for line in lines:
			dot = line.find(".")
			if line[:1] == "🔹" and dot != -1:
				last = line[2:dot]
		return str(last)

	def parsenewjob(self, text):
		last = self.parse_last_entry(text)
		asyncio.ensure_future(self.send_bot("Работа " + last))
		

	def parsefights(self, text):
		global times
		if not "лечение питомцев" in text:
			return False
		logger.info("Tring to parse fight time")
		lines = text.split("\n")
		times_ = []
		for _ in range(len(lines)):
			if "лечение питомцев" in lines[0]:
				lines.pop(0)
				break
			lines.pop(0)
		for line in lines:
			if ":" in line:
				timestr = line.rsplit(" ", 1)[1]
				if ":" in timestr:
					val = convert(timestr)
					times_.append(val if val else 0)
		logger.info("Calculated fight time")
		self.set_time("fight", time.time() + max(times_) + 2 + self.gen_time("fight"))
		return len(times_) > 0

	def get_bitcoins(self):
		now = time.time()
		if not settings.get("pet_bitcoin") or times.get("pet_bitcoin") > now:
			return
		self.set_time("pet_bitcoin", now + 60 * 61)
		asyncio.ensure_future(self.send_bot("Ферма"))

	def war_parsepoints(self, text):
		text = text.lower()
		lines = text.split("\n")
		max_upgrade = 16
		pets = {}
		points = 0
		for line in lines:
			logger.info(line)
			if "доступно очков способностей:" in line:
				logger.info("found line")
				pos = line.find(":")
				points = line[pos + 2:]
				logger.info(points)
				points = int(points)
			elif "💎" in line and "/" in line:
				start = line.find("⭐")
				end = line.find("/")
				has = line[start+1:end]
				has = int(has)
				pets[len(pets) + 1] = has
		test = []
		for pet in pets:
			has = pets[pet]
			pet = str(pet)
			if has == max_upgrade:
				continue
			for up_id in range(max_upgrade - has):
				if points <= 0:
					break
				upgrade = has + up_id + 1
				to_send = "Кв улучшить " + pet + " " + str(upgrade)
				points -= 1
				test.append(to_send)
		return test
	
	async def war_usepoints(self, text):
		info = self.war_parsepoints(text)
		for st in info:
			await self.send_bot(st)

	async def war_testcmd(self, message):
		"""Сброс куллдауна кв"""
		self.set_time("clan_war_upgrade", 1)
		await message.edit("Запускаю тест")

	def case_parse(self, text):
		has = {}
		lines = text.split("\n")

		amount_pattern = "(x"
		pattern_len = len(amount_pattern)

		for line in lines:
			if not "🔹" in line or not "." in text:
				continue
			if line[0] != "🔹":
				continue
			start = line.find(amount_pattern)
			if start == -1:
				continue
			dot = line.find(".")
			id = line[2:dot]
			amount = line[start+pattern_len:-1]
			try:
				amount = int(amount)
			except ValueError:
				continue
			return id

	def solving_captcha(self, bool):
		global stats
		stats["captcha"] = bool

	def pets_parse(self, text):
		allow = {
			"0": True,
			"1": True,
			"2": True,
			"3": True,
			"4": True,
			"5": True,
			"6": True,
			"7": True,
			"8": True,
			"9": True,
		}
		arr = stats.get("pets_parsed") or []

		text = text.replace("🔟", "10")
		text = text.replace("⃣", "")
		lines = text.split("\n")
		for line in lines:
			if not "|" in line:
				continue
			pet_id = ""
			for i in range(4):
				char = line[i]
				if allow.get(char):
					pet_id = pet_id + char
			hp_start = line.find("❤️")
			hp_end = line.find("|", hp_start)
			hp = line[hp_start+2:hp_end-1]
			dmg = 0
			if "💢" in line:
				dmg_start = line.find("💢")
				dmg_end = line.find("|", dmg_start)
				if dmg_end == -1:
					dmg = line[dmg_start+2:]
				else:
					dmg = line[dmg_start+2:dmg_end]
			mgc = 0
			if "🧿" in line:
				mgc_start = line.find("🧿")
				mgc_end = line.find("|", mgc_start)
				if mgc_end == -1:
					mgc = line[mgc_start+2:]
				else:
					mgc = line[mgc_start+2:mgc_end]
			arr.append({"ID": pet_id, "HP": int(hp), "DMG": floor(int(dmg) + int(mgc) * 1.1)})
		arr.sort(key=lambda x: x.get("DMG"), reverse=True)
		return arr

	async def lpetscmd(self, message):
		global stats
		if not stats.get("has"):
			asyncio.ensure_future(message.edit("Нету инфы о профиле"))
			return
		stats["pets_waiting"] = message
		stats["pets_parsed"] = None
		asyncio.ensure_future(message.edit("Жду инфу от бота"))
		asyncio.ensure_future(self.send_bot("Питомцы"))

	async def receive(self, message):  # Сообщение от бота
		global times
		global stats
		text = message.text.lower()
		now = time.time()
		if not text:
			return
		if "[💎] premium" in text:
			text = text.replace("[💎] ", "")
		# Инфа из профиля
		if "ваш профиль" in text:  # Инфа по профилю привет
			await self.parseprofile(text)

		if formats.get("banned") in text and not times.get("banned", None):
			logger.info("banned. Getting time")
			skip = len(formats.get("banned"))
			lines = text.split("\n")
			line = lines[0]
			reason = lines[1]
			need = convert(line[2+skip+1:])
			self.set_time("banned", now + need + 60)
			logger.info("Got ban time. Waiting " + str(need))
			await self._client.send_message(lesya_chat, "#ban\n<b>🚫 Я улетел в бан. Вернусь через " + timetostr(need) + "</b>\n" + reason)
			return

		# решение капчи
		if "для продолжения введите, пожалуйста, код с картинки" in text:
			self.solving_captcha(True)
			logger.info("Solving captcha from bot")
			code = await self.solve_captcha(message)
			logger.info("Sending captcha response")
			asyncio.ensure_future(message.reply(code))
			logger.info("Sending captcha response done")
			self.solving_captcha(False)
			logger.info("AFTER CAPTCHA-IF")

		# Ещё не получил инфу
		if not stats.get("has"):
			return
		# Расчёт действий

		# Модуль работы
		# Время работы
		if formats.get("work") in text:
			logger.info("Parsing job")
			self.parsejob(text)
		elif ", рабочий день закончен" in text:
			times["work"] = now + self.gen_time("work")

			# Автоповышение
		if stats.get("work"):
			if formats.get("work_new") in text:
				logger.info("Parsing new job")
				stats["new_job"] = True
				await self.send_bot("Уволиться")
				await self.send_bot("Работа")
			elif stats.get("new_job") and "можете устроиться на одну из работ:" in text:
				logger.info("looking job list")
				self.parsenewjob(text)
			elif stats.get("new_job") and ", профессии" in text:
				logger.info("looking job in job list")
				stats["new_job"] = None
				self.parsenewjob(text)
			elif ", вы нигде не работаете" in text:
				stats["new_job"] = True
				await self.send_bot("Работа")

		# Сбор инфы о петах
		if stats.get("pets_waiting"):
			msg = stats.get("pets_waiting")
			if ", у вас нет питомцев" in text:
				asyncio.ensure_future(msg.edit("Питомцев нету"))
				stats["pets_waiting"] = None
				stats["pets_parsed"] = None
			elif ", страница " in text:
				line = text.split("\n")[0]
				page_info = line.rsplit(" ", 1)[1]
				page_info = page_info.split("/")
				cur_page = page_info[0]
				if cur_page == page_info[1][:-1]: # Инфа собрана
					arr = stats.get("pets_parsed")
					reply = "<b>🐾 Топ питомцы</b>"
					for info in arr:
						reply = reply + "\n" + "🆔 " + info.get("ID") + " | ❤️ " + str(info.get("HP")) + " | 🔫 " + str(info.get("DMG"))
					asyncio.ensure_future(msg.edit(reply))
					stats["pets_waiting"] = None
					stats["pets_parsed"] = None
				else:
					arr = self.pets_parse(text)
					stats["pets_parsed"] = arr
					asyncio.ensure_future(self.send_bot("Питомцы " + str(int(cur_page) + 1)))

				

		# Бонус
		for btext in formats.get("bonus"):
			if btext in text:
				self.parsebonus(text)
				logger.info("Parsing bonus")

		# Автовалюта премиума
		if formats.get("bonus_money") in text:
			times["bonus_money"] = now + 5
			self.parsemoneybonus(text)
			logger.info("Parsing money bonus")

		# Автозакуп для ограблений
		if stats.get("need_to_buy") and ", предметы для ограбления:" in text:
			msg = stats.get("need_to_buy")
			stats["need_to_buy"] = None
			lines = text.split("\n")
			for line in lines:
				dot = line.find(".")
				if line[:1] == "🔸" and dot != -1:
					await self.send_bot("Предметы " + line[2:dot])
			await msg.reply("Ограбление")
		elif stats.get("need_to_buy") and ", этот раздел доступен только участникам клана" in text:
			msg = stats.get("need_to_buy")
			stats["need_to_buy"] = None
			await msg.reply("Дурак, меня в клане нету")

		# Автобой питомцев
		if "ваши питомцы проиграли" in text or "ваши питомцы победили" in text:  # Продолжение боя
			if not self.parsefights(text[1:]):
				times["fight"] = now + self.gen_time("fight")
				logger.info("Gonna start new fight soon")
		elif ", вы напали на игрока" in text or ", текущий бой:" in text or ", Вашим питомцам требуется отдых" in text:
			self.set_time("fight", now + 60 * 10)
			logger.info("There is battle/waiting. Gonna wait 10 min before the fight")
		elif ", наберите питомцев в отряд с помощью команды" in text or ", для проведения битвы нужны питомцы" in text:
			times["fight"] = now + 10**100
			logger.info("I don't have pets. No sense for fighting")
		elif ", теперь в вашем отряде" in text:
			times["fight"] = now + self.gen_time("fight")

		if settings.get("clan_heist"):
			if ", информация об ограблении" in text: # Основное сообщение
				if "выбран план: плана нет" in text:
					lines = text.split("\n")
					last = lines[-1]
					timestr = last.rsplit(" ", 1)[1]
					if timestr and ":" in timestr:
						wait = convert(timestr)
						self.set_time("clan_heist", now + wait)
					asyncio.ensure_future(self.send_group("Ограбление план 1"))
					asyncio.ensure_future(self.send_group("Ограбление план 1"))
				elif "ожидание начала..." in text:
					asyncio.ensure_future(self.send_bot("Ограбление старт"))
				else:
					lines = text.split("\n")
					last = lines[-1]
					timestr = last.rsplit(" ", 1)[1]
					if timestr and ":" in timestr:
						wait = convert(timestr)
						self.set_time("clan_heist", now + wait + 60)
			elif ", доступные ограбления:"  in text: # Выбор ограбления
				last = self.parse_last_entry(text) # Ищет возможные ограбления
				asyncio.ensure_future(self.send_bot("Ограбление " + last)) # Начинает последнее ограбление
			elif ", вы начали ограбление" in text and "доступные способы прохождения" in text: # Выбор плана
				lines = text.split("\n")
				for ltext in lines:
					if "время на подготовку:" in text:
						timestr = ltext.rsplit(" ", 1)[1]
						if timestr and ":" in timestr:
							wait = convert(timestr)
							self.set_time("clan_heist", now + wait + 60)
				asyncio.ensure_future(self.send_group("Ограбление план 1"))
			elif ", ограбление началось!" in text or ", ограбление уже началось" in text: # После ограбление старт / Когда уже идёт, а ты прописал старт
				line = text.split("\n")[1]
				timestr = line.rsplit(" ", 1)[1]
				if timestr and ":" in timestr:
					wait = convert(timestr)
					self.set_time("clan_heist", now + wait + 60)

		if settings.get("clan_war"):
			if ", клановая война не запущена" in text:
				asyncio.ensure_future(self.send_bot("Кв старт"))
				self.set_time("clan_war", now + 60)
			elif ", вы начали поиск противника!" in text:
				self.set_time("clan_war", now + 1800)
			elif ", война кланов начата!" in text: # Подготовка или уже сражение
				if "до конца отборочного этапа:" in text: # Идёт сбор питомцев с боёв. Нужно сделать автораспределение очков
					line = text.split("\n")[-1]
					timestr = line.rsplit(" ", 1)[1]
					if timestr and ":" in timestr:
						wait = convert(timestr)
						self.set_time("clan_war", now + wait + 60)
				elif "финальная битва через:" in text:
					line = text.split("\n")[-2]
					timestr = line.rsplit(" ", 1)[1]
					if timestr and ":" in timestr:
						wait = convert(timestr)
						self.set_time("clan_war", now + wait + 60)
						upgrade = times.get("clan_war_upgrade")
						if now > upgrade and upgrade != 0:
							if (wait - 600) > 0:
								self.set_time("clan_war_upgrade", now + wait - 600)
							else:
								self.set_time("clan_war_upgrade", 0)
							if "доступно очков способностей:" in text:
								await self.war_usepoints(text)
						elif (now + wait - 600) > 0:
							self.set_time("clan_war_upgrade", now + wait - 600)
				elif "конец войны через:" in text: # Финальное ожидание
					line = text.split("\n")[-2] # Вторая строка с конца - конец войны
					timestr = line.rsplit(" ", 1)[1]
					if timestr and ":" in timestr:
						wait = convert(timestr)
						self.set_time("clan_war", now + wait + 60)

		if settings.get("opencase"):
			if ", чтобы открывать несколько кейсов за раз, завершите исследование" in text: # На пустышках максимум можно 1, без указания количества
				logger.info("Не могу открыть максимум кейсов. Убираю число")
				stats["opencase_limit"] = True
				times["opencase"] = now + self.gen_time("opencase")
			elif ", неверный номер кейса" in text: # Закончился этот кейс
				if "📦 ваши кейсы:" in text:
					stats["opencase"] = self.case_parse(text)
				else:
					stats["opencase"] = None
			elif "📦 ваши кейсы:" in text:
				# Нужно спарсить кейсы
				times["opencase"] = now + self.gen_time("opencase")
				stats["opencase"] = self.case_parse(text)
			elif ", вам выпал" in text and " предмет" in text: # Вам выпало 4 предмета (3 объединено):
				self.set_time("opencase", now + self.gen_time("opencase"))
			elif ("📦 вам выпал" in text and " кейс" in text) or (", ваш" in text and " приз" in text and "кейсов" in text): # вам пыпал(о) 1(1) кейс(ов) / ваш (VIP/Прем) приз (на сегодня) — 1(00) (донат) кейс(ов)
				if not stats.get("opencase"):
					stats["opencase"] = 1

		# Сбор денег в банк при автотрейде/автостакане
		if settings.get("auto_trade"):
			if "✅ вы заработали +" in text:
				times["trade"] = now + self.gen_time("trade") + 1
				asyncio.ensure_future(self.send_bot("Банк положить все"))
			elif "❌  вы потеряли" in text:
				times["trade"] = now + self.gen_time("trade")

		if settings.get("auto_cup"):
			if ", правильно! приз " in text or ", верно! приз " in text or ", вы угадали! приз " in text:
				times["cup"] = now + self.gen_time("cup") + 1
				asyncio.ensure_future(self.send_bot("Банк положить все"))
			elif ", неверно, это был " in text and "-й стаканчик" in text:
				times["cup"] = now + self.gen_time("cup")
				# rel
		
		if settings.get("auto_casino"):
			if ", вы проиграли" in text:
				times["casino"] = now + self.gen_time("casino")
			elif ", вы выиграли" in text:
				asyncio.ensure_future(self.send_bot("Банк положить все"))
				times["casino"] = now + self.gen_time("casino") + 1

	async def receivechat(self, message):  # сообщения в канале с ботом
		global stats
		text = message.text.lower()
		user_id = message.from_id or 0

		if times.get("banned", None):
			if (text == "!бан"):
				now = time.time()
				wait = times.get("banned") - now
				await utils.answer(message, "Осталось " + timetostr(wait))
			return

		if (", вы выбрали план №" in text) and stats.get("clanbuy") and user_id == lesya and stats.get("clan"):
			stats["need_to_buy"] = message
			await self.send_bot("Предметы")

		if (text == "!закуп"):
			if user_id != TLG_JOHNNY:
				await utils.answer(message, "Пошёл нахер. Хать фу")
				return

			stats["need_to_buy"] = message
			await self.send_bot("Предметы")
		elif (text == "!пинг"):
			await utils.answer(message, "Жив, цел, орёл\nМой айди - " + stats.get("id"))

	async def timer(self):
		while True:
			if not self in self.allmodules.modules:
				logger.fatal("AutoLesya unloaded. Breaking timer.")
				break
			global stats
			global times
			now = time.time()
			if times.get("banned", None):
				if now > times.get("banned"):
					self.set_time("banned", 0)
					await self.send_bot("Профиль")
				await asyncio.sleep(1)
				continue

			if stats.get("captcha"):
				continue

			if not stats.get("has"):
				await self.send_bot("Профиль")
				logger.info("no stats")
				await asyncio.sleep(1)
				continue

			stats["info"] = True

			# Работа
			if settings.get("work") and now > times.get("work"):
				logger.info("Time to Work")
				times["work"] = now + 30
				asyncio.ensure_future(self.send_bot("Работать"))


			# Бонусы
			if settings.get("bonus"):
				if now > times.get("bonus"):
					logger.info("Getting bonus")
					times["bonus"] = now + 600
					asyncio.ensure_future(self.send_bot("Бонус"))
				if stats.get("vip") and now > times.get("vip_bonus"):
					logger.info("Getting vip bonus")
					times["vip_bonus"] = now + 600
					asyncio.ensure_future(self.send_bot("Вип бонус"))
				if stats.get("premium") and now > times.get("premium_bonus"):
					logger.info("Getting premium bonus")
					times["premium_bonus"] = now + 600
					asyncio.ensure_future(self.send_bot("Премиум бонус"))
				if stats.get("premium") and now > times.get("premium_money"):
					logger.info("Getting premium money")
					times["premium_money"] = now + 600
					asyncio.ensure_future(self.send_bot("Премиум валюта"))

			# Автозакуп для питомцев
			if settings.get("pet_stimulator") and now > times.get("pet_stimulator"):
				self.set_time("pet_stimulator", now + 60 * 60 * 24)
				self.get_bitcoins()
				asyncio.ensure_future(self.send_bot("Зоотовары 6"))

			if settings.get("pet_food") and now > times.get("pet_food"):
				self.set_time("pet_food", now + 60 * 60 * 24)
				self.get_bitcoins()
				asyncio.ensure_future(self.send_bot("Зоотовары 7"))

			if settings.get("pet_cases") and now > times.get("pet_cases"):
				self.set_time("pet_cases", now + 60 * 60 * 24)
				self.get_bitcoins()
				asyncio.ensure_future(self.send_bot("Зоотовары 8"))

			# Автобой
			if settings.get("fight") and now > times.get("fight"):
				times["fight"] = now + 30
				logger.info("Starting new battle")
				asyncio.ensure_future(self.send_bot("Бой"))

			if settings.get("clan_heist") and now > times.get("clan_heist"):
				times["clan_heist"] = now + 600
				asyncio.ensure_future(self.send_bot("Ограбление"))

			if settings.get("clan_war"):
				upgrade = times.get("clan_war_upgrade")
				if now > upgrade and upgrade != 0:
					asyncio.ensure_future(self.send_bot("Кв"))
				elif now > times.get("clan_war"):
					times["clan_war"] = now + 600
					asyncio.ensure_future(self.send_bot("КВ"))

			# Автооткрытие кейсов
			if settings.get("opencase") and now > times.get("opencase") and stats.get("opencase"):
				case = stats.get("opencase")
				times["opencase"] = now + self.gen_time("opencase")
				if stats.get("opencase_limit"):
					asyncio.ensure_future(self.send_bot("Кейс открыть " + str(case)))
				else:
					asyncio.ensure_future(self.send_bot("Кейс открыть " + str(case) + " 10"))

			# Если есть апгрейд города - метод поднятия денег и вывода в топ и себя и клана
			if settings.get("auto_trade") and now > times.get("trade"):
				times["trade"] = now + 5
				side = random.randint(0, 1) == 1 and "вверх" or "вниз"
				asyncio.ensure_future(self.send_bot("Трейд " + side + " все"))

			if settings.get("auto_cup") and now > times.get("cup"):
				times["cup"] = now + 5
				side = str(random.randint(1, 3))
				asyncio.ensure_future(self.send_bot("Стаканчик " + side + " все"))

			if settings.get("auto_casino") and now > times.get("casino"):
				times["casino"] = now + 5
				asyncio.ensure_future(self.send_bot("Казино все"))
			await asyncio.sleep(1)

	async def watcher(self, message):
		if not isinstance(message, types.Message):
			return
		if not message.text:
			return
		if message.from_id == self._me.id:
			return
		chat_id = utils.get_chat_id(message)
		if chat_id == lesya and not times.get("banned", None):
			await self.receive(message)
		elif chat_id == lesya_chat:
			asyncio.ensure_future(self.receivechat(message))

	def db_set(self, key, value):
		self._db.set(__name__, key, value)

	def db_get(self, key, default=None):
		return self._db.get(__name__, key, default)

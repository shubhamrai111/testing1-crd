import json, discord, websockets, requests
from bs4 import BeautifulSoup
from unidecode import unidecode
from datetime import datetime
import aiohttp, asyncio, re, threading

total_question = 0
google_question = "https://google.com/search?q="
order = ["１", "２", "３", "４", "５", "６", "７", "８", "９", "０"]
ignore_options = ["the", "of", "in", "&", "on", "for", "or", "it", "to", "at", "and", "?", "#", "!",
"a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
"name", "does", "do", "is", "am", "are", "have", "has", "been", "did", "was", "not", "least", "never", "don't", "haven't", "didn't", "wasn't", "except", "wouldn't", "itsn't",
"were", "had", "will", "would", "shall", "can", "should", "could", "may", "might", "need", "come", "comes", "means",
"what", "who", "which", "whom", "why", "how", "when", "where", "=", "de",
"of", "on", "these", "that", "this", "those", "there", "their", "at", "between", "from", "since", "for",
"they", "and", "the", "a", "an", "with", "as", "by", "in", "to", "into", "also", "but",
"i", "my", "me", "we", "our", "you", "your", "he", "his", "him", "himself", "them", "themselves", "it", "its", "myself", "she", "her", "yourselves",
"&", ".", "?", ",", "matched", "paired", "pair", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0"
]
replace_options = {"1": "one", "2": "two", "3": "three", "4": "four", "5": "five",
"6": "six", "7": "seven", "8": "eight", "9": "nine", "10": "ten"}
negative_words = {" not ", " least ", " never ", " incorrect ", " incorrectly ", " none ", " cannot ", " can't ", " didn't "}


class WebSocket(object):
	
	def __init__(self, client):
		self.client = client
		self.icon_url = "https://media.discordapp.net/attachments/840293855555092541/969343263276404836/Screenshot_2022-04-29-02-15-17-18.jpg"
		self.prize_pool = 500 # default prize pool of the quiz
		self.question_ids = []
		self.correct_answer_ids = []
		self.show_winners = False
		self.answer_pattern = []
		self.ws = None
		self.is_ws_opened = False
		
	async def send_hook(self, content = "", embed = None):
		"""Send message with Discord channel Webhook."""
		web_url = "https://discord.com/api/webhooks/969984365138427904/vRwvPmW94NAgpv4BwyeynGiGB-mo-Y7vc_XNPDM8wV40mE6-3vdLPWT2X-5waxg1EsVi"
		async with aiohttp.ClientSession() as session:
			webhook = discord.Webhook.from_url(web_url, adapter=discord.AsyncWebhookAdapter(session))
			await webhook.send(content = content, embed = embed, username = "Display Trivia", avatar_url = self.icon_url)
			
	async def close_ws(self):
		"""Close Websocket."""
		if not self.ws:
			await self.send_hook("**Websocket Already Closed!**")
		else:
			if self.ws.closed:
				return await self.send_hook("**Websocket Already Closed!**")
			await self.ws.close()
			await self.send_hook("**Websocket Closed!**")

	
	async def rating_search_one(self, question_url, options):
		"""Get Google search results through rating."""
		r = requests.get(question_url)
		res = str(r.text).lower()
		count_options = {}
		for option in options:
			_option = replace_options.get(option)
			option = _option if _option else option
			count_option = res.count(option.lower())
			count_options[option] = count_option
		max_count = max(list(count_options.values()))
		min_count = min(list(count_options.values()))
		#min_max_count = min_count if not_question else max_count
		embed = discord.Embed(title=f"__Search Results -{order[0]}__", color = discord.Colour.random())
		embed.set_footer(text = "Display Trivia")
		embed.timestamp = datetime.utcnow()
		description = ""
		for index, option in enumerate(count_options):
			if max_count != 0 and count_options[option] == max_count:
				description += f"{order[index]}. {option} : {count_options[option]} ✅\n"
			else:
				description += f"{order[index]}. {option} : {count_options[option]}\n"
		embed.description = description
		await self.send_hook(embed = embed)
	
	async def rating_search_two(self, question_url, choices):
		"""Get 2nd Google search results through rating."""
		r = requests.get(question_url)
		res = str(r.text).lower()
		count_options = {}
		for choice in choices:
			option = ""
			count_option = 0
			options = tuple(choice.split(" "))
			for opt in options:
				_option = replace_options.get(opt)
				opt = _option if _option else opt
				count = 0 if opt.lower() in ignore_options else res.count(opt.lower())
				count_option += count
				option += f"{opt}({count}) "
			count_options[option] = count_option
		max_count = max(list(count_options.values()))
		min_count = min(list(count_options.values()))
		#min_max_count = min_count if not_question else max_count
		embed = discord.Embed(title=f"__Search Results -{order[1]}__", color = discord.Colour.random())
		embed.set_footer(text = "Display Trivia")
		embed.timestamp = datetime.utcnow()
		description = ""
		for index, option in enumerate(count_options):
			if max_count != 0 and count_options[option] == max_count:
				description += f"{order[index]}. {option}: {count_options[option]} ✅\n"
			else:
				description += f"{order[index]}. {option}: {count_options[option]}\n"
		embed.description = description
		if max_count != 0: await self.send_hook(embed = embed)
	
	async def direct_search_result(self, question_url, options):
		"""Get Direct google search results."""
		r = requests.get(question_url)
		soup = BeautifulSoup(r.text , "html.parser")
		response = soup.find("div" , class_='BNeawe')
		result = str(response.text)
		embed = discord.Embed(
			description = result,
			color = discord.Colour.random(),
			timestamp = datetime.utcnow()
			)
		embed.set_footer(text="Search with Google")
		option_found = False
		for index, option in enumerate(options):
			if option.lower().strip() in result.lower():
				embed.title = f"__Option {order[index]}. {option}__"
				embed.description = re.sub(f'{option.strip()}', f'**__{option}__**', result, flags = re.IGNORECASE)
				option_found = True
		if not option_found:
			embed.title = f"__Direct Search Result !__"
		await self.send_hook(embed = embed)
	
	async def get_sub_protocol(self):
		"""Login display social and take the auth token."""
		login_url = "https://api.tsuprod.com/api/v1/user/login"
		data = json.dumps({
			"login": "sakhman2001@gmail.com",
			"password": "Subrata@2001",
			"client_version": "2.4.0.3(154)"
		})
		headers = {
			"Host": "api.tsuprod.com",
			"content-type": "application/json; charset=UTF-8",
			"accept-encoding": "gzip",
			"user-agent": "okhttp/4.9.1",
			"app_version": "2.4.0.3"
		}
		async with aiohttp.ClientSession() as session:
			response = await session.post(url = login_url, headers = headers, data = data)
			if response.status != 200:
				await self.send_hook("**Getting username or password is wrong. Please update your username or password if you changed.**")
				raise "Username or password is wrong."
			data = await response.json()
			auth_token = data["data"]["auth_token"]
			return auth_token

	async def connect_ws(self):
		sub_protocol = await self.get_sub_protocol()
		socket_url = "wss://trivia-websockets.tsuprod.com/"
		headers = {
			"Upgrade": "websocket",
			"Connection": "Upgrade",
			"Sec-WebSocket-Version": "13",
			"Sec-WebSocket-Extensions": "permessage-deflate",
			"Host": "trivia-websockets.tsuprod.com",
			"Accept-Encoding": "gzip",
			"User-Agent": "okhttp/4.9.1"
		}
		send_data = False
		connect = False
		self.ws = await websockets.connect(socket_url, subprotocols = [sub_protocol], extra_headers = headers)
		async for message in self.ws:
			message_data = json.loads(message)
			if message_data.get("status") == "Connected":
				print("Websocket Connected!")
				await self.send_hook("**Websocket Connecting...**")
				
			if message_data.get("type") == "games_list":
				game_id = message_data["data"][0]["id"]
				if not send_data:
					await self.ws.send(json.dumps({"action": "subscribe", "data": {"game_id": game_id}}))
					send_data, connect = True, True
					print(message_data)
					await self.send_hook("**Websocket Successfully Conncted!**")
			else:
				if not connect:
					await self.send_hook("**Game is not Live!**")
					return await self.close_ws()
				
			if message_data.get("t") == "poll":
				pass

			elif message_data.get("type") == "poll":
				pass

			elif message_data.get("t") == "trivium":
				global total_question, google_question
				question_id = message_data["q"][0]["id"]
				if question_id not in self.question_ids:
					self.question_ids.append(question_id)
					prize_pool = message_data["j"]
					total_question = message_data["max_q"]
					question_number = message_data["q"][0]["nth"]
					question = message_data["q"][0]["q"]
					options = [unidecode(option["a"]) for option in message_data["q"][0]["a"]]
					raw_question = str(question).replace(" ", "+")
					google_question = "https://google.com/search?q=" + raw_question
					u_options = "+or+".join(options)
					raw_options = str(u_options).replace(" ", "+")
					search_with_all = "https://google.com/search?q=" + raw_question + "+" + raw_options
					not_question = True if " not " in question.lower() else False
					is_not = "(Not Question)" if not_question else ""
					
					embed = discord.Embed(color = discord.Colour.random())
					embed.title = f"Question {question_number} out of {total_question} {is_not}"
					embed.description = f"[{question}]({google_question})\n\n[Search with all options]({search_with_all})"
					for index, option in enumerate(options):
						embed.add_field(name = f"Option - {order[index]}", value = f"[{option.strip()}]({google_question + '+' + str(option).strip().replace(' ', '+')})", inline = False)
					embed.set_footer(text = "Display Trivia")
					embed.set_thumbnail(url = self.icon_url)
					embed.timestamp = datetime.utcnow()
					await self.send_hook(embed = embed)
					
					target_list = [
							self.rating_search_one(google_question, options),
							self.rating_search_two(google_question, options),
							self.direct_search_result(google_question, options),
						]
							#self.direct_search_result(search_with_all, choices)
					for target in target_list:
						thread = threading.Thread(target = lambda: asyncio.run(target))
						thread.start()
					
			elif message_data.get("t") == "results":
				total_players, total_ratio = 0, 0
				check_result = False
				for index, data in enumerate(message_data["q"][0]["a"]):
					if data["c"]:
						check_result = True
						self.answer_pattern.append(str(index+1))
						ans_num = order[index]
						answer = data["a_c"]
						answer_id = data["id"]
						advance_players = data["t"]
						advance_ratio = float(data["p"])
					total_players += data["t"]
					total_ratio += float(data["p"])
				if check_result and answer_id not in self.correct_answer_ids:
					self.correct_answer_ids.append(answer_id)
					eliminate_players = total_players - advance_players
					eliminate_ratio = float("{:.2f}".format(total_ratio - advance_ratio))
					question_number = message_data["q"][0]["nth"]
					question = message_data["q"][0]["q_c"]
					ans = 0 if advance_players == 0 else (self.prize_pool)/(advance_players)
					payout = float("{:.2f}".format(ans))
					
					embed = discord.Embed(color = discord.Colour.random())
					embed.title = f"Question {question_number} out of {total_question}"
					embed.description = f"[{question}]({google_question})"
					embed.add_field(name = "Correct Answer :-", value = f"Option {ans_num}. {answer}", inline = False)
					embed.add_field(name = "Status :-",
						value = f"Advancing Players : {advance_players} ({advance_ratio}%)\nEliminated Players : {eliminate_players} ({eliminate_ratio}%)\nCurrent Payout : ${payout}",
						inline = False
						)
					embed.set_thumbnail(url = self.icon_url)
					embed.set_footer(text = "Display Trivia")
					embed.timestamp = datetime.utcnow()
					await self.send_hook(embed = embed)
					
			elif message_data.get("game_type") == "trivium":
				if not self.show_winners:
					self.show_winners = True
					prize_pool = message_data["prize_pool"]
					num_winners = message_data["num_winners"]
					share = message_data["share"]
					
					embed = discord.Embed(title = "__Game Summary !__",
						description = f"● Payout : ${share}\n● Total Winners : {num_winners}\n● Prize Money : ${prize_pool}",
						color = discord.Colour.random(),
						)
					embed.set_thumbnail(url = self.icon_url)
					embed.set_footer(text = "Display Trivia")
					embed.timestamp = datetime.utcnow()
					await self.send_hook(embed = embed)
					await self.close_ws()

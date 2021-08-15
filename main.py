import discord
import os
import bot_functions as bf
#from keep_alive import keep_alive
import json
import requests

from ids import discord_ids_names
from hero_detect import find_heroes_in_match

from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")

with open('heroes.json', 'r') as f:
    heroes_json = json.load(f)

def save_image(image_url, file_name):
    img_data = requests.get(image_url).content
    try:
        os.mkdir(file_name)
    except:
        pass
    with open(f'{file_name}.png', 'wb') as handler:
        handler.write(img_data)

def get_hero_ids(user_ids, args, found_heroes):
    message_heroes = []
    for i in range(len(user_ids)):
        target_slot = args[i]
        for found_hero in found_heroes:
            if found_hero['hero_slot'] == int(target_slot):
                message_heroes.append({user_ids[i]: found_hero['hero_id']})
                break
    return message_heroes

client = discord.Client()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

async def notify_hero_averages(message, user_ids, hero_avgs):
  base_message = "Considerando a média de K/D/A das últimas 20 partidas:\n"
  for i in range(len(user_ids)):
    hero_name = heroes_json[str(hero_avgs[i]['hero_id'])]['localized_name']
    base_message += f"  •  {discord_ids_names[user_ids[i]]} [**{hero_name}**] - **{int(hero_avgs[i]['kills'])}/{int(hero_avgs[i]['deaths'])}/{int(hero_avgs[i]['assists'])}**\n"
  
  await message.channel.send(base_message)
  return

async def detect_flow(message):
    await message.channel.send("Analizando imagem!")
    team = message.content[-1]
    user_ids = bf.get_mentioned_user_ids(message)
    args = bf.get_message_args(message)[:-1]
    try:
        save_image(message.attachments[0].url, 'temp')
    except:
        await message.channel.send("Nenhuma imagem adicionada na mensagem!")
        return
    try:
        found_heroes = find_heroes_in_match('temp.png', team)
        found_heroes = sorted(found_heroes, key=lambda k: k['hero_slot'])
    except Exception as e:
        print(e)
        await message.channel.send("Time não encontrado! Digitar r para Radiant ou d para Dire!")
        return

    message_heroes = get_hero_ids(user_ids, args, found_heroes)
    found_heroes_msg =''
    for found_hero in found_heroes:
      found_heroes_msg += f"Slot {found_hero['hero_slot']}: {found_hero['hero_name']} (ID: {found_hero['hero_id']}) "

    await message.channel.send(found_heroes_msg)
    return message_heroes


async def predict_flow(message, turbo, message_heroes):
  if turbo:
    await message.channel.send("Pedido de predict TURBO recebido! Calculando...")
  else:
    await message.channel.send("Pedido de predict NORMAL recebido! Calculando...")

  user_ids = [list(x.keys())[0] for x in message_heroes]
  hero_ids = [list(x.values())[0] for x in message_heroes]
  
  try:
    hero_avgs = bf.get_player_hero_averages(user_ids, hero_ids)
  except:
    await message.channel.send("Não encontradas partidas com o heroi!")
    return

  if hero_avgs == None:
    await message.channel.send("Pedido de predict mal formatado!")
    return
  
  await notify_hero_averages(message, user_ids, hero_avgs)

  input_df = bf.preprocess_input(hero_avgs, turbo=turbo)
  
  result, confidence = bf.predict_match(input_df)
  result_text = "**GANHAR**" if result else "**PERDER**"

  await message.channel.send(f"A lekers vai {result_text} com **{round(confidence*100, 2)}%** de certeza!")

  return

@client.event
async def on_message(message):
  if message.author == client.user:
      return

  if message.content.startswith('!predict'):
    message_heroes = await detect_flow(message)
    if message_heroes:
      await predict_flow(message, 1, message_heroes)
    else:
      await message.channel.send(f"Falha na análise da imagem!")
    return
  
  if message.content.startswith('!normal_predict'):
    message_heroes = await detect_flow(message)
    if message_heroes:
      await predict_flow(message, 0, message_heroes)
    else:
      await message.channel.send(f"Falha na análise da imagem!")
    return

client.run(BOT_TOKEN)
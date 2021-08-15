import re
import pandas as pd
from ids import discord_ids_dict
from pickle import load

import numpy as np

#import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense


def get_model(node_size, n_nodes):
    model = Sequential()
    for i in range(n_nodes):
        model.add(Dense(node_size, activation='relu'))
    
    model.add(Dense(2, activation='softmax'))
    
    model.compile(optimizer='adam', 
                  loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])
    return model

# load the model
model = get_model(128, 1)
model.load_weights('model/latest')

# load the scaler
scaler = load(open('scaler.pkl', 'rb'))


def predict_match(input_df):
  scaled_input = scaler.transform(input_df)
  prediction = model.predict(scaled_input)[0]

  result = np.argmax(prediction)
  confidence = prediction[result]

  return result, confidence


def preprocess_input(hero_avgs, turbo):
    input_data = {}
    input_data['is_turbo'] = 1 if turbo == 1 else 0
    
    for hero_avg in hero_avgs:
        input_data[f"{hero_avg['player_id']}_{hero_avg['hero_id']}"] = 1
        input_data[f"{hero_avg['player_id']}_present"] = 1
        input_data[f"{hero_avg['player_id']}_kills"] = hero_avg['kills']
        input_data[f"{hero_avg['player_id']}_deaths"] = hero_avg['deaths']
        input_data[f"{hero_avg['player_id']}_assists"] = hero_avg['assists']
    
    player_df = pd.read_csv('party_matches_sample.csv')
    columns = player_df.columns.tolist()

    sorted_input = {}
    for column in columns:
        if column in input_data.keys():
            sorted_input[column] = input_data[column]
            continue
        sorted_input[column] = 0
    
    del sorted_input['result']
    input_df = pd.DataFrame([sorted_input])
    
    return input_df


def get_player_hero_averages(discord_ids, hero_ids):
  if len(discord_ids) != len(hero_ids):
    print('Error in disc ids and hero ids size!')
    return None
  matches_df = pd.read_csv('lekers_matches.csv')
  hero_averages = []
  for i in range(len(discord_ids)):
    try:
      player_id = discord_ids_dict[discord_ids[i]]
    except:
      print('ID não encontrado! Finalizando')
      return None
    
    player_df = matches_df[matches_df['player_id']==player_id].copy()
    player_df = player_df[player_df['hero_id']==int(hero_ids[i])]
    player_df = player_df.set_index('start_time').sort_index()
    player_df = player_df[-20:]
    player_df = (player_df
                  .groupby('player_id')
                  .agg({
                      'kills' : 'mean',
                      'deaths' : 'mean',
                      'assists' : 'mean',
                  }))
    player_df['kills'] = player_df['kills'].apply(lambda x: round(x,0))
    player_df['deaths'] = player_df['deaths'].apply(lambda x: round(x,0))
    player_df['assists'] = player_df['assists'].apply(lambda x: round(x,0))

    avgs = player_df.to_dict('records')[0]
    avgs['discord_id'] = discord_ids[i]
    avgs['player_id'] = player_id
    avgs['hero_id'] = int(hero_ids[i])
    hero_averages.append(avgs)
  #print(hero_averages)
  return hero_averages

def get_mentioned_user_ids(message):
  user_ids = []
  for mention in message.mentions:
    user_ids.append(mention.id)
  return user_ids

def get_message_args(message):
  msg_content = message.content
  if len(message.mentions):
    last_mention = message.mentions[-1].id
    last_mention_pos = msg_content.find(str(last_mention))
    msg_content = msg_content[last_mention_pos+len(str(last_mention))+2:]
  args = re.sub(' +', ' ', msg_content)
  args = args.split(' ')
  print(f'Message content: {msg_content}')
  print(f"Received args: {args}")
  return args
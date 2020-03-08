import requests
import bson 


def decode_response(content):
    return bson.loads(content)['data']

data = {
    'text': ['hi there whats up', 'my name is bob.'] * 100
}

print('Making request')

response = requests.post('http://104.168.136.18:6969/generate_speech/bulk', json=data)
response.raise_for_status()
print('done')

print('decoding response')
data = decode_response(response.content)
print('done')

print('writing files')
for i, file_data in enumerate(data):
    with open(f'{i}.mp3', 'wb') as f:
        f.write(file_data)

print('Done')

import time 

time.sleep(10)

import os 

for file in os.listdir(): 
    if file.endswith('.mp3'):
        os.remove(file)
import requests
import bson 
import zlib
import time
import os 

def decode_response(content):
    return bson.loads(content)['data']

data = {
    'text': ['hi there whats up', 'my name is bob.'] * 100
}

print('Making request')

response = requests.post(os.getenv('HOST') + '/generate_speech/bulk', json=data, stream=True)
response.raise_for_status()
print('done')



start = time.time()

print(len(response.content)/(10**6))
print((time.time()-start)/1000)

print('compressing')
print(len(zlib.decompress(response.content))/(10**6))
print('finished compressing')
print()

print('decoding response')
data = decode_response(response.content)
print('done')

print('writing files')
for i, file_data in enumerate(data):
    with open(f'{i}.mp3', 'wb') as f:
        f.write(file_data)

print('Done')

time.sleep(10)


for file in os.listdir(): 
    if file.endswith('.mp3'):
        os.remove(file)


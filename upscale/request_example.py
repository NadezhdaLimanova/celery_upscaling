import requests
import time

with open('lama_300px.png', 'rb') as image_file:
    resp = requests.post('http://localhost:5000/upscale', files={'image': (image_file.name, image_file)})


resp_data = resp.json()
task_id = resp_data.get('task_id')

status = 'PENDING'

resp = requests.get(f'http://127.0.0.1:5000/upscale/{task_id}')
print(resp.json())
time.sleep(20)

resp = requests.get(f'http://127.0.0.1:5000/upscale/{task_id}')
print(resp.json())



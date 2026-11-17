import requests, json

url = 'http://127.0.0.1:5000/getData?key=123&start=2022-11-23%2005:28:10&end=2022-11-23%2005:28:15'
r = requests.get(url)
resp = json.loads(r.text)
print('getData:', resp['msg'])
print(len(resp['data']), 'records')

url = 'http://127.0.0.1:5000/countInPolygon?key=123&polygon=-74%2042,-75%2039,-74%2041,-74%2042'
r = requests.get(url)
resp = json.loads(r.text)
print('countInPolygon:', resp['msg'])
print(resp['data']['count'], 'points in polygon')

url = 'http://127.0.0.1:5000/getAvgSpeedByFlight?key=123&start=2022-11-23%2005:00:00&end=2022-11-23%2008:00:00'
r = requests.get(url)
resp = json.loads(r.text)
print('getAvgSpeedByFlight:', resp['msg'])
print(len(resp['data']), 'flight averages')
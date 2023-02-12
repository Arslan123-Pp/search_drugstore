from io import BytesIO
from PIL import Image
import math
import requests
import sys


def lonlat_distance(a, b):
    degree_to_meters_factor = 111 * 1000
    a_lon, a_lat = a
    b_lon, b_lat = b
    radians_lattitude = math.radians((a_lat + b_lat) / 2)
    lat_lon_factor = math.cos(radians_lattitude)
    dx = abs(a_lon - b_lon) * degree_to_meters_factor * lat_lon_factor
    dy = abs(a_lat - b_lat) * degree_to_meters_factor
    distance = math.sqrt(dx * dx + dy * dy)
    return distance


def get_spn(json_response):
    try:
        crds = \
            json_response['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']
        lc = crds['boundedBy']['Envelope']['lowerCorner'].split()
        uc = crds['boundedBy']['Envelope']['upperCorner'].split()
        x = str(abs(float(uc[0]) - float(lc[0])))
        y = str(abs(float(uc[1]) - float(lc[1])))
        return [x, y]
    except Exception:
        return ['1', '1']


search_api_server = "https://search-maps.yandex.ru/v1/"
geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"
api_key = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"

toponym_to_find = " ".join(sys.argv[1:])
geocoder_params = {
    "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
    "geocode": toponym_to_find,
    "format": "json"}

response = requests.get(geocoder_api_server, params=geocoder_params)

if not response:
    # обработка ошибочной ситуации
    pass

# Преобразуем ответ в json-объект
json_response = response.json()
# Получаем первый топоним из ответа геокодера.
toponym = json_response["response"]["GeoObjectCollection"][
    "featureMember"][0]["GeoObject"]
# Координаты центра топонима:
toponym_coodrinates = toponym["Point"]["pos"]
# Долгота и широта:
toponym_longitude, toponym_lattitude = toponym_coodrinates.split(" ")
address_ll = f'{toponym_longitude},{toponym_lattitude}'


search_params = {
    "apikey": api_key,
    "text": "аптека",
    "lang": "ru_RU",
    "ll": address_ll,
    "type": "biz"
}

response = requests.get(search_api_server, params=search_params)

if not response:
    pass
json_response = response.json()

# Получаем первую найденную организацию.
organization = json_response["features"][0]
work_time = json_response['features'][1]["properties"]["CompanyMetaData"]['Hours']['text']
# Название организации.
org_name = organization["properties"]["CompanyMetaData"]["name"]
# Адрес организации.
org_address = organization["properties"]["CompanyMetaData"]["address"]
# Получаем координаты ответа.
point = organization["geometry"]["coordinates"]
org_point = "{0},{1}".format(point[0], point[1])
delta = "0.005"
camera_position_x = min([float(address_ll.split(',')[0]), float(org_point.split(',')[0])]) + \
                    (abs(float(org_point.split(',')[0]) - float(address_ll.split(',')[0])) / 2)
camera_position_y = min([float(address_ll.split(',')[1]), float(org_point.split(',')[1])]) + \
                    (abs(float(org_point.split(',')[1]) - float(address_ll.split(',')[1])) / 2)
dst = lonlat_distance(list(map(float, org_point.split(','))), list(map(float, address_ll.split(','))))
print(org_address, org_name, work_time, f'{round(dst, 2)} метр')

# Собираем параметры для запроса к StaticMapsAPI:
map_params = {
    # позиционируем карту центром на наш исходный адрес
    "ll": f'{camera_position_x},{camera_position_y}',
    "spn": ",".join([delta, delta]),
    "l": "map",
    # добавим точку, чтобы указать найденную аптеку
    "pt": '~'.join(["{0},pm2dgl".format(org_point), "{0},pm2dbl".format(address_ll)])
}
map_api_server = "http://static-maps.yandex.ru/1.x/"
# ... и выполняем запрос
response = requests.get(map_api_server, params=map_params)
Image.open(BytesIO(
    response.content)).show()
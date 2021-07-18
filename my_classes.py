from collections import defaultdict

# for citymobil parsing
from selenium import webdriver
import time

# Yandex_taxi API
import requests


class YandexGeocoderAPI:
    def __init__(self, apikey_):
        self.apikey = apikey_

    @staticmethod
    def create_object():
        with open('geocoder data.txt', 'r') as f:
            apikey = f.read().splitlines()
        return YandexGeocoderAPI(*apikey)

    def get_json_for_coordinates(self, address):
        main_page = 'https://geocode-maps.yandex.ru/1.x/?'
        params = f'format=json&apikey={self.apikey}&geocode={address}'
        page = main_page + params
        response = requests.get(page)
        return response.json()

    def get_json_for_address(self, coordinates):
        main_page = 'https://geocode-maps.yandex.ru/1.x/?'
        params = f'format=json&apikey={self.apikey}&geocode={coordinates}'
        page = main_page + params
        response = requests.get(page)
        return response.json()

    def get_coordinates(self, address):
        json_file = self.get_json_for_coordinates(address)
        coordinates = json_file['response']['GeoObjectCollection'][
            'featureMember'][0]['GeoObject']['Point']['pos']
        lon, lat = coordinates.split()
        return f'{lon},{lat}'

    def get_address(self, coordinates):
        json_file = self.get_json_for_coordinates(coordinates)
        address = json_file['response']['GeoObjectCollection'][
            'featureMember'][0]['GeoObject']['metaDataProperty'][
            'GeocoderMetaData']['AddressDetails']['Country']['AddressLine']
        return address

    def get_correct_address(self, address):
        coordinates = self.get_coordinates(address)
        return self.get_address(coordinates)


class YandexTaxiAPI:
    def __init__(self, apikey_, clid_):
        self.apikey = apikey_
        self.clid = clid_

    @staticmethod
    def create_object():
        with open('yandex_taxi data.txt', 'r') as f:
            data_ = f.read().splitlines()
            apikey = data_[0]
            clid = data_[1]
        return YandexTaxiAPI(apikey, clid)

    def get_json(self, geocoder: YandexGeocoderAPI,
                 taxi_class, address_from, address_to):
        coordinates_from = geocoder.get_coordinates(address_from)
        coordinates_to = geocoder.get_coordinates(address_to)
        main_page = 'https://taxi-routeinfo.taxi.yandex.net/taxi_info?'
        params = f'clid={self.clid}&apikey={self.apikey}&rll=' \
                 f'{coordinates_from}~{coordinates_to}&class={taxi_class}'
        page = main_page + params
        response = requests.get(page)
        return response.json()

    def get_price_time_distance(self, geocoder: YandexGeocoderAPI,
                                taxi_class, address_from, address_to) -> list:
        json_file = self.get_json(geocoder,
                                  taxi_class, address_from, address_to)
        return [str(json_file['options'][0]['price']) + 'р',
                str(json_file['time'] / 60) + ' мин',
                str(json_file['distance'] / 1000) + ' км']


class Citymobil:
    def __init__(self, taxi_class_, address_from_, address_to_):
        self.taxi_class = taxi_class_
        self.address_from = address_from_
        self.address_to = address_to_

    def get_price(self):
        """For non-headless version(visual opening Chrome)
         you can comment first 3 strings and recomment 4-th."""
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        driver = webdriver.Chrome(chrome_options=options)
        # driver = webdriver.Chrome()
        driver.get('https://city-mobil.ru')
        time.sleep(2)
        # geolocation test
        driver.find_element_by_class_name('Button_button__2WaUX').click()
        time.sleep(1)
        # order button
        driver.find_element_by_class_name('Button_button__2sv0Y').click()
        time.sleep(1)
        input_address = driver.find_elements_by_class_name('mtw-input')
        input_address[0].send_keys(self.address_from)
        time.sleep(1)
        driver.find_elements_by_class_name('svelte-1e1mlwx')[1].click()  # from
        time.sleep(1)

        input_address[1].send_keys(self.address_to)
        time.sleep(1)
        driver.find_elements_by_class_name('svelte-1e1mlwx')[1].click()  # to
        time.sleep(3)
        taxi_class_name = driver.find_elements_by_class_name('mtw-tariff-name')
        price = driver.find_elements_by_class_name('mtw-tariff-price')

        d = defaultdict()
        for i in range(len(taxi_class_name)):
            d[taxi_class_name[i].text] = price[i].text

        for i in d.keys():
            if i == self.taxi_class:
                return d[self.taxi_class]
        else:
            raise Exception('NOT FOUNDED TAXI_CLASS')

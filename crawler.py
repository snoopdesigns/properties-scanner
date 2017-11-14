#!/usr/bin/python3

import urllib.request
import urllib.parse
import csv
from pyquery import PyQuery as pq
from lxml import etree
import time
import json
import myconfig

TELEGRAM_TOKEN = "453478799:AAGyWsQm2B28Yok4I81EGkv-CHA58lPlgDo"
TELEGRAM_CHAT_ID = "116360945"
AVITO_DATA_FILE_PATH = myconfig.avito_datafile
AVITO_URL = myconfig.avito_url
POINTS_DATA_FILE = myconfig.points_datafile

new_apartments_avito = []

def send_bot_msg(msg):
	msg = urllib.parse.quote_plus(msg)
	getUrl = "https://api.telegram.org/bot%s/sendMessage?chat_id=%s&text=%s" % (TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, msg)
	with urllib.request.urlopen(getUrl) as response:
		html = response.read()
		print("Response: " + str(html))

def inform_load():
	for new_ap in new_apartments_avito:
		text = "New apartment:\n"
		text += new_ap
		send_bot_msg(text)

def load_page(url):
	print("Loading url:" + url)
	fp = urllib.request.urlopen(url)
	mybytes = fp.read()
	mystr = mybytes.decode("utf8")
	fp.close()
	return mystr;

def process_page_avito(html, write_header, existing_ids_avito, millis):
	ids = []
	infos = []
	urls = []
	prices = []
	address = []

	d = pq(html)
	for item in d("div.item.item_table"):
		ids.append(item.attrib["id"])
	for item in d("a.item-description-title-link"):
		infos.append(item.text.strip().split(",")[1].strip().replace(" м²", ""))
		urls.append(item.attrib["href"])
	for item in d("div.about"):
		prices.append(item.text.strip().replace(" руб. в месяц", "").replace(" ", ""))
	for item in d("p.address.fader"):
		address.append(item[1].tail.strip().replace(", ","", 1).replace('\"',''))

	with open(AVITO_DATA_FILE_PATH, 'a') as csvfile:
		fieldnames = ['id', 'url', 'info', 'price', 'address', 'timestamp']
		writer = csv.DictWriter(csvfile, fieldnames=fieldnames, dialect='unixpwd')
		if write_header == 1:
			writer.writeheader()
		for idx, val in enumerate(infos):
			if ids[idx] not in existing_ids_avito:
				#print("Found unique id:" + str(ids[idx]))
				new_apartments_avito.append("https://www.avito.ru%" + urls[idx])
				writer.writerow({'id': ids[idx], 'url': urls[idx], 'info': infos[idx], 'price': prices[idx], 'address': address[idx], 'timestamp': millis})
			else:
				print("Found already existing id:" + str(ids[idx]))
	
	return len(ids)

def run_avito_crawler():
	existing_ids_avito = []
	millis = str(int(round(time.time() * 1000)))

	csv.register_dialect('unixpwd', delimiter=':', quoting=csv.QUOTE_NONE)
	# Read file for ids
	with open(AVITO_DATA_FILE_PATH, newline='') as csvfile:
		reader = csv.reader(csvfile, delimiter=':')
		for row in reader:
			if len(row) > 0:
				existing_ids_avito.append(row[0])

	total = 0
	for page in range(1, 10, 1):
		url = AVITO_URL + "&p=" + str(page)
		html = load_page(url)
		write_header = 1
		if page > 1:
			write_header = 0
		page_len = process_page_avito(html, write_header, existing_ids_avito, millis)
		total += page_len
		print("Number of loaded apartments: " + str(page_len))
		if (page_len < 50):
			break

def geocode_addr(addr):
	addr = urllib.parse.quote_plus(addr)
	url = "https://geocode-maps.yandex.ru/1.x/?format=json&results=1&geocode=" + addr
	fp = urllib.request.urlopen(url)
	mybytes = fp.read()
	mystr = mybytes.decode("utf8")
	fp.close()
	json_res = json.loads(mystr)
	print(json_res["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]["Point"]["pos"])
	return mystr

points  = open(POINTS_DATA_FILE, 'r').read()
d = pq(points)
print(d)
#print(d("Point"))
for item in d("Placemark"):
	print(item.text)
#result = geocode_addr("Санкт-Петербург, м. Улица Дыбенко, Искровский пр-кт, д.28")
#run_avito_crawler()
#inform_load()



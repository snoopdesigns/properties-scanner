#!/usr/bin/python3

import urllib.request
import urllib.parse
import csv
from pyquery import PyQuery as pq
from lxml import etree
import time
import json
import xml.etree.ElementTree as ET
from math import radians, cos, sin, asin, sqrt
import os
import myconfig

TELEGRAM_TOKEN = "453478799:AAGyWsQm2B28Yok4I81EGkv-CHA58lPlgDo"
TELEGRAM_CHAT_ID = "116360945"
AVITO_DATA_FILE_PATH = myconfig.avito_datafile
AVITO_URL = myconfig.avito_url
POINTS_DATA_FILE = myconfig.points_datafile
INFORM = myconfig.inform_flag
DIST_THRESHOLD = myconfig.dist_threshold

points = []
names = []

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
				if find_matches(address[idx]) == 1:
					new_apartments_avito.append("MATCH:\nhttps://www.avito.ru%" + urls[idx])
					print("https://www.avito.ru%s" % urls[idx])
				else:
					#print("Match not found: " + address[idx])
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
		if os.path.getsize(AVITO_DATA_FILE_PATH)==0:
			write_header = 0
		if page > 1:
			write_header = 0
		page_len = process_page_avito(html, write_header, existing_ids_avito, millis)
		total += page_len
		print("Number of loaded apartments: " + str(page_len))
		if (page_len < 50):
			break

def dist(left, right):
	lon1 = float(left.split(",")[0])
	lat1 = float(left.split(",")[1])
	lon2 = float(right.split(",")[0])
	lat2 = float(right.split(",")[1])
	lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
	dlon = lon2 - lon1 
	dlat = lat2 - lat1 
	a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
	c = 2 * asin(sqrt(a))
	km = 6371* c
	return km

def find_matches(addr):
	addr = urllib.parse.quote_plus(addr)
	with urllib.request.urlopen('https://geocode-maps.yandex.ru/1.x/?results=1&geocode=' + addr) as response:
	   html = response.read()
	tree = ET.fromstring(html)
	coord = "undefined"
	for point in tree.iter('{http://www.opengis.net/gml}Point'):
		coord = point[0].text.strip().split(" ")[0] + "," + point[0].text.strip().split(" ")[1]
	#print("Target coord: " + coord)

	if coord=="undefined":
		return 0
	for idx, point in enumerate(points):
		distance = dist(point, coord)
		if (distance < DIST_THRESHOLD):
			print("Match found: %s" % names[idx])
			#print(point)
			#print(names[idx])
			return 1
	return 0

def prepare_points():
	tree = ET.parse(POINTS_DATA_FILE)
	root = tree.getroot()
	for point in root.iter('{http://www.opengis.net/kml/2.2}Placemark'):
		points.append(point[2][0].text.strip().split(",")[0] + "," + point[2][0].text.strip().split(",")[1])
		names.append(point[0].text.strip())
	print("Loaded %d points from file" % len(points))

prepare_points()
run_avito_crawler()
if INFORM=="1":
	inform_load()



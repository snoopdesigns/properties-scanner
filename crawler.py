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
DATA_FILE_PATH = myconfig.avito_datafile
AVITO_URL = myconfig.avito_url
CIAN_URL = myconfig.cian_url
POINTS_DATA_FILE = myconfig.points_datafile
INFORM = myconfig.inform_flag
DIST_THRESHOLD = myconfig.dist_threshold

points = []
names = []

new_apartments = []

def send_bot_msg(msg):
	msg = urllib.parse.quote_plus(msg)
	getUrl = "https://api.telegram.org/bot%s/sendMessage?chat_id=%s&text=%s" % (TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, msg)
	with urllib.request.urlopen(getUrl) as response:
		html = response.read()
		print("Response: " + str(html))

def inform_load():
	for new_ap in new_apartments:
		send_bot_msg(new_ap)

def load_page(url):
	print("Loading url:" + url)
	fp = urllib.request.urlopen(url)
	mybytes = fp.read()
	mystr = mybytes.decode("utf8")
	fp.close()
	return mystr;

def generate_inform_msg(addr, target_addr, url, type):
	if type==0: #not match
		return "New apartment:\n" + url
	else: # match
		return "New apartment [!!!!!!!!!!!!!!!!!]:\n" + addr + "[" + target_addr + "]\n" + url

def parse_avito_page(d, ids, infos, urls, prices, address):
	for item in d("div.item.item_table"):
		ids.append(item.attrib["id"])
	for item in d("a.item-description-title-link"):
		infos.append(item.text.strip().split(",")[1].strip().replace(" м²", ""))
		urls.append("https://www.avito.ru" + item.attrib["href"])
	for item in d("div.about"):
		prices.append(item.text.strip().replace(" руб. в месяц", "").replace(" ", ""))
	for item in d("p.address.fader"):
		address.append(item[1].tail.strip().replace(", ","", 1).replace('\"',''))

def parse_cian_page(d, ids, infos, urls, prices, address):
	offers = []
	for item in d("div"):
		if "offer-container" in str(item.attrib.get('class')):
			offers.append(item)
	for offer in offers:
		auth_elem=offer[0][1][0][0][1][1][0][0][0][1][0][0]
		if "Собственник" not in str(auth_elem.text):
			continue
		# address parse
		addr_elem=offer[0][1][0][0][0][0][0][0][1]
		if 'building' in addr_elem.attrib.get('class'):
			addr_elem=offer[0][1][0][0][0][0][0][0][2]
		addr_res = ""
		for elem_i in range(0, len(addr_elem), 1):
			addr_res = addr_res + addr_elem[elem_i].text + " "
		address.append(addr_res)
		#print(addr_res)
		
		id_elem=offer[0][1][0][1][0]
		#print(id_elem.attrib.get('href'))
		urls.append(id_elem.attrib.get('href'))
		id_1=id_elem.attrib.get('href').replace("https://spb.cian.ru/rent/flat/","").replace("/","")
		ids.append(id_1)
		infos.append('undefined')
		prices.append('undefined')

def process_page(html, write_header, existing_ids, millis, type):
	ids = []
	infos = []
	urls = []
	prices = []
	address = []

	#print(html)
	d = pq(html)
	if type==1:
		parse_avito_page(d, ids, infos, urls, prices, address)
	else:
		parse_cian_page(d, ids, infos, urls, prices, address)

	with open(DATA_FILE_PATH, 'a') as csvfile:
		fieldnames = ['id', 'url', 'info', 'price', 'address', 'timestamp']
		writer = csv.DictWriter(csvfile, fieldnames=fieldnames, dialect='unixpwd', escapechar='\\')
		if write_header == 1:
			writer.writeheader()
		for idx, val in enumerate(infos):
			if ids[idx] not in existing_ids:
				#print("Found unique id:" + str(ids[idx]))
				match_res = find_matches(address[idx])
				if match_res != "":
					new_apartments.append(generate_inform_msg(address[idx], match_res, urls[idx], 1))
					print("=============================================")
					print(urls[idx])
					print(match_res)
					print(address[idx])
					print("=============================================")
				else:
					#print("Match not found: " + address[idx])
					new_apartments.append(generate_inform_msg("", "", urls[idx], 0))
				writer.writerow({'id': ids[idx], 'url': urls[idx], 'info': infos[idx], 'price': prices[idx], 'address': address[idx], 'timestamp': millis})
	return len(ids)

def run_crawler():
	existing_ids = []
	millis = str(int(round(time.time() * 1000)))

	csv.register_dialect('unixpwd', delimiter=':', quoting=csv.QUOTE_NONE)
	# Read file for ids
	with open(DATA_FILE_PATH, newline='') as csvfile:
		reader = csv.reader(csvfile, delimiter=':', escapechar='\\')
		for row in reader:
			if len(row) > 0:
				existing_ids.append(row[0])

	total = 0
	write_header = 0
	if os.path.getsize(DATA_FILE_PATH)==0:
		write_header = 1
		
	# AVITO crawling
	for page in range(1, 10, 1):
		#break # TODO remove
		url = AVITO_URL + "&p=" + str(page)
		html = load_page(url)
		page_len = process_page(html, write_header, existing_ids, millis, 1)
		write_header = 0
		total += page_len
		print("Number of loaded apartments [AVITO]: " + str(page_len))
		if (page_len < 50):
			break

	# CIAN crawling
	for page in range(1, 10, 1):
		url = CIAN_URL + "&p=" + str(page)
		html = load_page(url)
		page_len = process_page(html, write_header, existing_ids, millis, 2)
		total += page_len
		print("Number of loaded apartments [CIAN]: " + str(page_len))
		if (page_len < 25):
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
		return ""
	for idx, point in enumerate(points):
		distance = dist(point, coord)
		if (distance < DIST_THRESHOLD):
			#print("Match found: %s" % names[idx])
			#print(point)
			#print(names[idx])
			return names[idx]
	return ""

def prepare_points():
	tree = ET.parse(POINTS_DATA_FILE)
	root = tree.getroot()
	for point in root.iter('{http://www.opengis.net/kml/2.2}Placemark'):
		points.append(point[2][0].text.strip().split(",")[0] + "," + point[2][0].text.strip().split(",")[1])
		names.append(point[0].text.strip())
	print("Loaded %d points from file" % len(points))

prepare_points()
run_crawler()
if INFORM=="1":
	inform_load()



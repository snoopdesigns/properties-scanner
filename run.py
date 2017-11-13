#!/usr/bin/python3

import urllib.request
import urllib.parse
import csv
from pyquery import PyQuery as pq
from lxml import etree
import time
import myconfig

TELEGRAM_TOKEN = "453478799:AAGyWsQm2B28Yok4I81EGkv-CHA58lPlgDo"
TELEGRAM_CHAT_ID = "116360945"
CSV_FILE_PATH = myconfig.datafile

new_apartments = []

def inform_load():
	for new_ap in new_apartments:
		text = "New apartment:\n"
		text += "https://www.avito.ru%s\n" % (new_ap)
		text = urllib.parse.quote_plus(text)
		getUrl = "https://api.telegram.org/bot%s/sendMessage?chat_id=%s&text=%s" % (TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, text)
		with urllib.request.urlopen(getUrl) as response:
			html = response.read()
			print("Response: " + str(html))

def load_page(url):
	print("Loading url:" + url)
	fp = urllib.request.urlopen(url)
	mybytes = fp.read()
	mystr = mybytes.decode("utf8")
	fp.close()
	return mystr;

def process_page(html, write_header, existing_ids, millis):
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

	with open(CSV_FILE_PATH, 'a') as csvfile:
		fieldnames = ['id', 'url', 'info', 'price', 'address', 'timestamp']
		writer = csv.DictWriter(csvfile, fieldnames=fieldnames, dialect='unixpwd')
		if write_header == 1:
			writer.writeheader()
		for idx, val in enumerate(infos):
			if ids[idx] not in existing_ids:
				print("Found unique id:" + str(ids[idx]))
				new_apartments.append(urls[idx])
				writer.writerow({'id': ids[idx], 'url': urls[idx], 'info': infos[idx], 'price': prices[idx], 'address': address[idx], 'timestamp': millis})
			else:
				print("Found already existing id:" + str(ids[idx]))
	
	return len(ids)

existing_ids = []
millis = str(int(round(time.time() * 1000)))

csv.register_dialect('unixpwd', delimiter=':', quoting=csv.QUOTE_NONE)
# Read file for ids
with open(CSV_FILE_PATH, newline='') as csvfile:
	reader = csv.reader(csvfile, delimiter=':')
	for row in reader:
		#print(row)
		if len(row) > 0:
			existing_ids.append(row[0])

total = 0
for page in range(1, 10, 1):
	url = "https://www.avito.ru/sankt-peterburg/kvartiry/sdam/na_dlitelnyy_srok/1-komnatnye?pmax=23000&pmin=0&s=101&user=1&metro=171-196-208&f=568_14010b" + "&p=" + str(page)
	html = load_page(url)
	write_header = 1
	if page > 1:
		write_header = 0
	page_len = process_page(html, write_header, existing_ids, millis)
	total += page_len
	print("Number of loaded apartments: " + str(page_len))
	if (page_len < 50):
		break

inform_load()



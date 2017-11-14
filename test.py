#!/usr/bin/python3
import xml.etree.ElementTree as ET
import urllib.request
from math import radians, cos, sin, asin, sqrt

print("START")

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
	for point in tree.iter('{http://www.opengis.net/gml}Point'):
		coord = point[0].text.strip().split(" ")[0] + "," + point[0].text.strip().split(" ")[1]
	print("Target coord: " + coord)

	for idx, point in enumerate(points):
		distance = dist(point, coord)
		if (distance < 0.15):
			print("Match found:")
			print(point)
			print(names[idx])
			return 1
	return 0

def prepare_points():
	tree = ET.parse('ap.xml')
	root = tree.getroot()
	for point in root.iter('{http://www.opengis.net/kml/2.2}Placemark'):
		points.append(point[2][0].text.strip().split(",")[0] + "," + point[2][0].text.strip().split(",")[1])
		names.append(point[0].text.strip())

points = []
names = []

addr = "Санкт-Петербург, м. Улица Дыбенко, ул Крыленко д 1стр1 корп"
prepare_points()
match_res = find_matches(addr)
print("Match res: " + str(match_res))

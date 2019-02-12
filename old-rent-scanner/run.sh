#!/bin/sh
filter="Народная,Большевиков,Дальневосточный,Тельмана,Новосёлов,Крыленко,Огнева,Шотмана,Дыбенко,Искровский,Овсеенко,Подвойского,Товарищеский,Белышева,Нерчинская,Бадаева,Рида,Коллонтай,Солидарности,Клочков,Пятилеток,Российский,Союзный,Октябрьская,Латышских,Челиева"
rm data_new.csv
cat data.csv | while read line
do
	year=${line: -5}
	if [ "${year:0:2}" = "20" ] || [ "${year:0:2}" = "19" ]; then
		if [[ "$year" > 2003 ]]; then
			for filter_name in $(echo $filter | sed "s/,/ /g")
			do
				if [[ $line == *"$filter_name"* ]]; then
					echo $line >> data_new.csv
					break
				fi
			done
		fi
	fi
done
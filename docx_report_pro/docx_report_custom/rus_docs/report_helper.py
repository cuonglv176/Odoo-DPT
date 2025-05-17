# -*- coding: utf-8 -*-

from datetime import datetime
import re
from pytils import numeral, dt


class Helper(object):
    def numer(self, name):
        if name:
            numeration = re.findall("\d+$", name)
            if numeration:
                return numeration[0]
        return ""

    def ru_date(self, date):
        if date and date != "False":
            return dt.ru_strftime(
                '"%d" %B %Y года',
                date=datetime.strptime(str(date), "%Y-%m-%d"),
                inflected=True,
            )
        return ""

    def ru_date2(self, date):
        if date and date != "False":
            return dt.ru_strftime(
                "%d %B %Y г.",
                date=datetime.strptime(str(date), "%Y-%m-%d %H:%M:%S"),
                inflected=True,
            )
        return ""

    def in_words(self, number):
        return numeral.in_words(number)

    def rubles(self, sum):
        "Transform sum number in rubles to text"
        text_rubles = numeral.rubles(int(sum))
        copeck = round((sum - int(sum)) * 100)
        text_copeck = numeral.choose_plural(
            int(copeck), ("копейка", "копейки", "копеек")
        )
        return ("%s %02d %s") % (text_rubles, copeck, text_copeck)

    def initials(self, fio):
        if fio:
            return (
                fio.split()[0]
                + " "
                + "".join([fio[0:1] + "." for fio in fio.split()[1:]])
            ).strip()
        return ""

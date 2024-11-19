# -*- coding: utf-8 -*-

from odoo.fields import datetime
from odoo import _
from odoo.exceptions import ValidationError
from datetime import timedelta
import pytz
import os
import os.path
from dateutil import rrule
from dateutil.relativedelta import relativedelta



def ks_get_date(ks_date_filter_selection, self, type):
    try:
        timezone = self._context.get('tz')
    except Exception as e:
        timezone = self.env.user.tz

    if not timezone:
        ks_tzone = os.environ.get('TZ')
        if ks_tzone:
            timezone = ks_tzone
        elif os.path.exists('/etc/timezone'):
            ks_tzone = open('/etc/timezone').read()
            timezone = ks_tzone[0:-1]
            try:
                datetime.now(pytz.timezone(timezone))
            except Exception as e:
                raise ValidationError(_("Please set the local timezone."))

        else:
            raise ValidationError(_("Please set the local timezone."))

    series = ks_date_filter_selection
    if ks_date_filter_selection in ['t_fiscal_year', 'n_fiscal_year', 'ls_fiscal_year']:
        return eval("ks_date_series_" + series.split("_")[0])(series.split("_")[1], timezone, type,self)
    else:
        return eval("ks_date_series_" + series.split("_")[0])(series.split("_")[1], timezone, type, self)
def ks_date_series_td(ks_date_selection, timezone, type, self=None):
    return eval("ks_get_date_range_from_td_" + ks_date_selection)(timezone, type, self)

def ks_get_date_range_from_td_year(timezone, type,self):
    ks_date_data = {}
    date = datetime.now(pytz.timezone(timezone))
    year = date.year
    start_date = datetime(year, 1, 1)
    end_date = date
    if type == 'date':
        ks_date_data["selected_start_date"] = datetime.strptime(start_date.strftime("%Y-%m-%d"), '%Y-%m-%d')
        ks_date_data["selected_end_date"] = datetime.strptime(end_date.strftime("%Y-%m-%d"), '%Y-%m-%d')
    else:
        ks_date_data["selected_start_date"] = ks_convert_into_utc(start_date, timezone)
        ks_date_data["selected_end_date"] = ks_convert_into_utc(end_date, timezone)
    return ks_date_data

def ks_get_date_range_from_td_month(timezone, type,self):
    ks_date_data = {}

    date = datetime.now(pytz.timezone(timezone))
    year = date.year
    month = date.month
    start_date = datetime(year, month, 1)
    end_date = date
    if type == 'date':
        ks_date_data["selected_start_date"] = datetime.strptime(start_date.strftime("%Y-%m-%d"), '%Y-%m-%d')
        ks_date_data["selected_end_date"] = datetime.strptime(end_date.strftime("%Y-%m-%d"), '%Y-%m-%d')
    else:
        ks_date_data["selected_start_date"] = ks_convert_into_utc(start_date, timezone)
        ks_date_data["selected_end_date"] = ks_convert_into_utc(end_date, timezone)
    return ks_date_data
def ks_get_date_range_from_td_week(timezone, type,self):
    ks_date_data = {}
    lang = self.env['res.lang']._lang_get(self.env.user.lang)
    week_start = lang.week_start
    start_Date = rrule.weekday(int(week_start) - 1)
    start_date = datetime.today() + relativedelta(weekday=start_Date(-1))
    end_date = datetime.now(pytz.timezone(timezone))
    start_date = datetime.strptime(start_date.strftime("%Y-%m-%d"), '%Y-%m-%d')
    if type == 'date':
        ks_date_data["selected_start_date"] = start_date
        end_date = datetime.strptime(end_date.strftime("%Y-%m-%d"), '%Y-%m-%d')
        ks_date_data["selected_end_date"] = end_date
    else:
        ks_date_data["selected_start_date"] = ks_convert_into_utc(start_date, timezone)
        ks_date_data["selected_end_date"] = ks_convert_into_utc(end_date, timezone)
    return ks_date_data
def ks_get_date_range_from_td_quarter(timezone, type,self):
    ks_date_data = {}
    date = datetime.now(pytz.timezone(timezone))
    year = date.year
    quarter = int((date.month - 1) / 3) + 1
    start_date = datetime(year, 3 * quarter - 2, 1)
    end_date = date
    if type == 'date':
        ks_date_data["selected_start_date"] = datetime.strptime(start_date.strftime("%Y-%m-%d"), '%Y-%m-%d')
        ks_date_data["selected_end_date"] = datetime.strptime(end_date.strftime("%Y-%m-%d"), '%Y-%m-%d')
    else:
        ks_date_data["selected_start_date"] = ks_convert_into_utc(start_date, timezone)
        ks_date_data["selected_end_date"] = ks_convert_into_utc(end_date, timezone)
    return ks_date_data


# Last Specific Days Ranges : 7, 30, 90, 365
def ks_date_series_l(ks_date_selection, timezone, type, self=None):
    ks_date_data = {}
    date_filter_options = {
        'day': 0,
        'week': 7,
        'month': 30,
        'quarter': 90,
        'year': 365,
        'past': False,
        'future': False
    }
    end_time = datetime.strptime(datetime.now(pytz.timezone(timezone)).strftime("%Y-%m-%d 23:59:59"),
                                                          '%Y-%m-%d %H:%M:%S')
    start_time = datetime.strptime((datetime.now(pytz.timezone(timezone)) - timedelta(
        days=date_filter_options[ks_date_selection])).strftime("%Y-%m-%d 00:00:00"), '%Y-%m-%d %H:%M:%S')
    if type == 'date':
        ks_date_data["selected_end_date"] = datetime.strptime(end_time.strftime("%Y-%m-%d"), '%Y-%m-%d')
        ks_date_data["selected_start_date"] = datetime.strptime(start_time.strftime("%Y-%m-%d"), '%Y-%m-%d')
    else:
        ks_date_data["selected_end_date"] = ks_convert_into_utc(end_time, timezone)
        ks_date_data["selected_start_date"] = ks_convert_into_utc(start_time, timezone)

    return ks_date_data


# Current Date Ranges : Week, Month, Quarter, year
def ks_date_series_t(ks_date_selection, timezone, type, self=None):
    return eval("ks_get_date_range_from_" + ks_date_selection)("current", timezone, type,self)


# Previous Date Ranges : Week, Month, Quarter, year
def ks_date_series_ls(ks_date_selection, timezone, type,self=None):
    return eval("ks_get_date_range_from_" + ks_date_selection)("previous", timezone, type,self)


# Next Date Ranges : Day, Week, Month, Quarter, year
def ks_date_series_n(ks_date_selection, timezone, type,self=None):
    return eval("ks_get_date_range_from_" + ks_date_selection)("next", timezone, type, self)


def ks_get_date_range_from_day(date_state, timezone, type,self):
    ks_date_data = {}

    date = datetime.now(pytz.timezone(timezone))

    if date_state == "previous":
        date = date - timedelta(days=1)
    elif date_state == "next":
        date = date + timedelta(days=1)
    start_date = datetime(date.year, date.month, date.day)
    end_date = datetime(date.year, date.month, date.day) + timedelta(days=1, seconds=-1)
    if type == 'date':
        ks_date_data["selected_start_date"] = datetime.strptime(start_date.strftime("%Y-%m-%d"), '%Y-%m-%d')
        ks_date_data["selected_end_date"] = datetime.strptime(end_date.strftime("%Y-%m-%d"), '%Y-%m-%d')
    else:
        ks_date_data["selected_start_date"] = ks_convert_into_utc(start_date,timezone)
        ks_date_data["selected_end_date"] =  ks_convert_into_utc(end_date,timezone)
    return ks_date_data


def ks_get_date_range_from_week(date_state, timezone, type,self):
    ks_date_data = {}

    # date = datetime.now(pytz.timezone(timezone))
    # ks_week = 0
    lang = self.env['res.lang']._lang_get(self.env.user.lang)
    week_start = lang.week_start
    start_Date = rrule.weekday(int(week_start) - 1)
    start_date = datetime.today() + relativedelta(weekday=start_Date(-1))
    if date_state == "previous":
        start_date = datetime.today() - relativedelta(weeks=1, weekday=start_Date(-1))
    elif date_state == "next":
        start_date = datetime.today() - relativedelta(weeks=-1, weekday=start_Date(-1))

    start_date = datetime.strptime(start_date.strftime("%Y-%m-%d"), '%Y-%m-%d')
    if type == 'date':
        ks_date_data["selected_start_date"] = start_date
        end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59, milliseconds=59)
        ks_date_data["selected_end_date"] = end_date
    else:
        ks_date_data["selected_start_date"] = ks_convert_into_utc(start_date, timezone)
        end_date = start_date + timedelta(days=6, hours=23, minutes=59, seconds=59, milliseconds=59)
        ks_date_data["selected_end_date"] = ks_convert_into_utc(end_date, timezone)
    return ks_date_data

def ks_get_date_range_from_month(date_state, timezone, type,self):
    ks_date_data = {}

    date = datetime.now(pytz.timezone(timezone))
    year = date.year
    month = date.month

    if date_state == "previous":
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    elif date_state == "next":
        month += 1
        if month == 13:
            month = 1
            year += 1

    end_year = year
    end_month = month
    if month == 12:
        end_year += 1
        end_month = 1
    else:
        end_month += 1
    start_date = datetime(year, month, 1)
    end_date = datetime(end_year, end_month, 1) - timedelta(seconds=1)
    if type == 'date':
        ks_date_data["selected_start_date"] = datetime.strptime(start_date.strftime("%Y-%m-%d"), '%Y-%m-%d')
        ks_date_data["selected_end_date"] = datetime.strptime(end_date.strftime("%Y-%m-%d"), '%Y-%m-%d')
    else:
        ks_date_data["selected_start_date"] = ks_convert_into_utc(start_date, timezone)
        ks_date_data["selected_end_date"] = ks_convert_into_utc(end_date, timezone)
    return ks_date_data


def ks_get_date_range_from_quarter(date_state, timezone, type,self):
    ks_date_data = {}

    date = datetime.now(pytz.timezone(timezone))
    year = date.year
    quarter = int((date.month - 1) / 3) + 1

    if date_state == "previous":
        quarter -= 1
        if quarter == 0:
            quarter = 4
            year -= 1
    elif date_state == "next":
        quarter += 1
        if quarter == 5:
            quarter = 1
            year += 1

    start_date = datetime(year, 3 * quarter - 2, 1)

    month = 3 * quarter
    remaining = int(month / 12)
    end_date = datetime(year + remaining, month % 12 + 1, 1) - timedelta(seconds=1)
    if type == 'date':
        ks_date_data["selected_start_date"] = datetime.strptime(start_date.strftime("%Y-%m-%d"), '%Y-%m-%d')
        ks_date_data["selected_end_date"] = datetime.strptime(end_date.strftime("%Y-%m-%d"), '%Y-%m-%d')
    else:
        ks_date_data["selected_start_date"] = ks_convert_into_utc(start_date, timezone)
        ks_date_data["selected_end_date"] = ks_convert_into_utc(end_date, timezone)
    return ks_date_data


def ks_get_date_range_from_year(date_state, timezone, type,self):
    ks_date_data = {}

    date = datetime.now(pytz.timezone(timezone))
    year = date.year

    if date_state == "previous":
        year -= 1
    elif date_state == "next":
        year += 1
    start_date = datetime(year, 1, 1)
    end_date = datetime(year + 1, 1, 1) - timedelta(seconds=1)
    if type == 'date':
        ks_date_data["selected_start_date"] = datetime.strptime(start_date.strftime("%Y-%m-%d"), '%Y-%m-%d')
        ks_date_data["selected_end_date"] = datetime.strptime(end_date.strftime("%Y-%m-%d"), '%Y-%m-%d')
    else:
        ks_date_data["selected_start_date"] = ks_convert_into_utc(start_date, timezone)
        ks_date_data["selected_end_date"] = ks_convert_into_utc(end_date, timezone)
    return ks_date_data

def ks_get_date_range_from_past(date_state, self_tz, type, self):
    ks_date_data = {}
    date = datetime.now(pytz.timezone(self_tz))
    if type == 'date':
        ks_date_data["selected_end_date"] = datetime.strptime(date.strftime("%Y-%m-%d"), '%Y-%m-%d')
    else:
        ks_date_data["selected_end_date"] = ks_convert_into_utc(date, self_tz)
    ks_date_data["selected_start_date"] = False
    return ks_date_data


def ks_get_date_range_from_pastwithout(date_state, self_tz, type,self):
    ks_date_data = {}
    date = datetime.now(pytz.timezone(self_tz))
    hour = date.hour + 1
    date = date - timedelta(hours=hour)
    date = datetime.strptime(date.strftime("%Y-%m-%d 23:59:59"), '%Y-%m-%d %H:%M:%S')
    ks_date_data["selected_start_date"] = False
    if type == 'date':
        ks_date_data["selected_end_date"] = datetime.strptime(date.strftime("%Y-%m-%d"), '%Y-%m-%d')
    else:
        ks_date_data["selected_end_date"] = ks_convert_into_utc(date, self_tz)
    return ks_date_data


def ks_get_date_range_from_future(date_state, self_tz, type,self):
    ks_date_data = {}
    date = datetime.now(pytz.timezone(self_tz))
    ks_date_data["selected_end_date"] = False
    if type == 'date':
        ks_date_data["selected_start_date"] = date.strptime(date.strftime("%Y-%m-%d"), '%Y-%m-%d')
    else:
        ks_date_data["selected_start_date"] = ks_convert_into_utc(date,self_tz)
    return ks_date_data


def ks_get_date_range_from_futurestarting(date_state, self_tz, type,self):
    ks_date_data = {}
    date = datetime.now(pytz.timezone(self_tz))
    date = date + timedelta(days=1)
    start_date = datetime.strptime(date.strftime("%Y-%m-%d 00:00:00"), '%Y-%m-%d %H:%M:%S')
    if type == 'date':
        ks_date_data["selected_start_date"] = datetime.strptime(start_date.strftime("%Y-%m-%d"), '%Y-%m-%d')
        ks_date_data["selected_end_date"] = False
    else:
        ks_date_data["selected_start_date"] = ks_convert_into_utc(start_date, self_tz)
        ks_date_data["selected_end_date"] = False
    return ks_date_data

def ks_convert_into_utc(datetime, timezone):
    ks_tz = timezone and pytz.timezone(timezone) or pytz.UTC
    return ks_tz.localize(datetime.replace(tzinfo=None), is_dst=False).astimezone(pytz.UTC).replace(tzinfo=None)

def ks_convert_into_local(datetime, timezone):
    ks_tz = timezone and pytz.timezone(timezone) or pytz.UTC
    return pytz.UTC.localize(datetime.replace(tzinfo=None), is_dst=False).astimezone(ks_tz).replace(tzinfo=None)
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import datetime
import xlrd

def convert_excel_date_to_python_date(xl_date):
	if isinstance(xl_date,int) or isinstance(xl_date,float):
		datetime_date = xlrd.xldate_as_datetime(int(xl_date), 0)
		date_object = datetime_date.date()
		string_date = date_object.isoformat()
		return string_date
	return

# convert excel date to python date
"""def convert_excel_date_to_python_date(excel_date):
  dt = datetime.fromordinal(datetime(1900, 1, 1).toordinal() + int(excel_date) - 2)
  dt.strftime('%Y-%m-%d')
  return str(dt)"""

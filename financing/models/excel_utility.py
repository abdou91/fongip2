# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import datetime
import xlrd

def convert_excel_date_to_python_date(xl_date):
	if isinstance(xl_date,int):
		datetime_date = xlrd.xldate_as_datetime(xl_date, 0)
		date_object = datetime_date.date()
		string_date = date_object.isoformat()
		return string_date
	return 

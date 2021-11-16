# -*- coding: utf-8 -*-

from datetime import date
from workalendar.africa import IvoryCoast as Senegal
cal = Senegal()

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import ValidationError


class HrHolidaysPublic(models.Model):
    _inherit = "hr.holidays.public"

    def scheduler_compute_public_holidays(self):
        year = date.today().year
        country_id = self.env["res.country"].search([
            ('code', '=', 'SN'),], limit=1)
        holidays = []
        for h in cal.holidays(year):
            if h[1] and h[1] == 'National Peace Day':
                continue
            elif h[1] and h[1] == 'Independence Day':
                holidays.append([0, 0, {
                    'variable_date': True,
                    'date': f"{year}-04-04",
                    'name': h[1],
                }])
            else:
                holidays.append([0, 0, {
                    'variable_date': True,
                    'date': str(h[0]),
                    'name': h[1],
                }])
        holidays_year = self.env['hr.holidays.public'].search([
            ('year', '=', year),
        ], limit=1)
        if holidays_year:
            holidays_year.line_ids = False
            holidays_year.write({
                'country_id': country_id.id,
                'line_ids': holidays,
            })
        else:
            self.env['hr.holidays.public'].create({
                'country_id': country_id.id,
                'line_ids': holidays,  
            })


class HrHolidaysPublicLine(models.Model):
    _inherit = "hr.holidays.public.line"
    
    def _check_date_state_one(self):
        return True
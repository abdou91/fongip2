# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models

TYPE_EMPLOYEE = [
    ('prestataire','Prestataire'),
    ('stagiaire','Stagiaire'),
    ('consultant','Consultant'),
    ('permanant','Permanent'),
]


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    @api.onchange('vaccination_covid19')
    def _onchange_vaccination_covid19(self):
        for record in self:
            if not record.vaccination_covid19:
                record.vaccination = False
        return

    matricule_pointage = fields.Integer(string='Matricule pointage')
    matricule = fields.Char(string="Matricule")
    color = fields.Integer(String = 'Color Index')
    type_employee = fields.Selection(TYPE_EMPLOYEE, string="Type", store=True)
    agence = fields.Many2one('hr.agence',string='Lieu de travail')
    hourly_rate = fields.Float(string='Objectifs', store=True, readonly=True)
    vaccination_covid19 = fields.Boolean(string='Vaccination Covid19', store=True)
    vaccination = fields.Date(string='Date Vaccination', store=True)
    

class HrEmployee(models.Model):
    _name = 'hr.employee'
    _inherit = 'hr.employee'

    def pointage_entree(self):
        self.env['pointage.manuel'].create({
            'employee': self.id,
            'type_pointage': 'entree',
            'date_heure': datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
        })

    def pointage_sortie_pause(self):
        self.env['pointage.manuel'].create({
            'employee': self.id,
            'type_pointage': 'sortie_pause',
            'date_heure': datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
        })

    def pointage_retour_pause(self):
        self.env['pointage.manuel'].create({
            'employee': self.id,
            'type_pointage': 'retour_pause',
            'date_heure': datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
        })

    def pointage_sortie(self):
        self.env['pointage.manuel'].create({
            'employee': self.id,
            'type_pointage': 'sortie',
            'date_heure': datetime.today().strftime("%Y-%m-%d %H:%M:%S"),
        })

    def create_presence_for_employee(self, employee_id, date_from, date_to):
        if employee_id and date_from and date_to:
            presence = self.env['hr.presence'].create({
                'employee': employee_id,
                'date_from': date_from,
                'date_to': date_to,
            })
            return presence

    def scheduler_send_mail_working_week_statistique(self):
        today = datetime.today()
        tdelta = timedelta(days=today.weekday(), weeks=1)
        #Lundi semaine passée
        date_from = today - tdelta
        #Vendredi semaine passée
        date_to = date_from + timedelta(days=4)
        all_employees = self.env["hr.employee"].search([])
        for employee in all_employees:
            presence = self.create_presence_for_employee(employee.id, date_from, date_to)
            presence.send_mail_working_statistique()
        return

    def last_day_of_month(self, any_day):
        next_month = any_day.replace(day=28) + timedelta(days=4)
        return next_month - timedelta(days=next_month.day)

    def scheduler_send_mail_working_month_statistique(self):
        date_from = datetime.today().replace(day=1)
        date_to = self.last_day_of_month(date_from)
        all_employees = self.env["hr.employee"].search([])
        for employee in all_employees:
            presence = self.create_presence_for_employee(employee.id, date_from, date_to)
            presence.send_mail_working_statistique()
        return

    def get_weekly_hour(self):
        day_week = []
        work_hour = self.resource_calendar_id
        if work_hour:
            for attendance_id in work_hour.attendance_ids:
                if attendance_id.dayofweek not in day_week:
                    day_week.append(attendance_id.dayofweek)
            return work_hour.hours_per_day * len(day_week)
        return 40.0

    def sheduler_compute_hourly_rate_employee(self):
        today = datetime.today()
        all_employees = self.search([])
        for employee in all_employees:
            work_time = self.env['hr.presence'].new_compute_working_time(
                today, today, employee
            )
            if work_time and work_time[0]:
                work_hour = employee.get_weekly_hour()
                #On recommence les lundis
                if today.weekday() == 0:
                    employee.hourly_rate = round(work_time[0], 3) * 100 / work_hour
                else:
                    employee.hourly_rate += round(work_time[0], 3) * 100 / work_hour
        return


class HRBureau(models.Model):
    _name = 'hr.agence'
    _description = "Agence"

    name = fields.Char(string="Nom d'agence")


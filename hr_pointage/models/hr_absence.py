# -*- coding: utf-8 -*-
from odoo import api, fields, models

STATE = [
    ('draft', 'Broullion'),
    ('validation_drh', 'Validation DRH'),
    ('validation_dg', 'Validation DG'),
    ('cancel', 'Annulé'),
    ('done', 'Validé'),
]

class HRAbsence(models.Model):
    _name = 'hr.absence'
    _description = "Absence"

    name = fields.Char(string="Titre", required=True)
    employee = fields.Many2one('hr.employee', string="Employé Absent", required=True)
    date_from = fields.Date(string="Date début")
    date_to = fields.Date(string="Date fin")
    state = fields.Selection(STATE, string="Etat", default='draft',store=True)
    absence_line = fields.One2many('hr.absence.line', 'absence_id', string='Absence Line')

    def action_draft(self):
    	self.state = 'validation_drh'

    def action_validation_drh(self):
    	self.state = 'validation_dg'

    def action_validation_dg(self):
    	self.state = 'done'

    def action_cancel(self):
    	self.state = 'cancel'

    def action_reset_draft(self):
    	self.state = 'draft'


class HRAbsenceLine(models.Model):
    _name = 'hr.absence.line'
    _description = 'Absence Line'

    title = fields.Char(string="Titre du Fichier")
    description = fields.Text(string='Description')
    file = fields.Binary('File')
    fname = fields.Char('Fichier')
    absence_id = fields.Many2one('hr.absence')



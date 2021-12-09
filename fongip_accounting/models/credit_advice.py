# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from datetime import datetime

class CreditAdvice(models.Model):
	_name = 'credit.advice'
	_description = 'Credit advice'

	name = fields.cahr(string = "Intitulé")
	date = fields.Date(string = "Date")
	#compte
	partner_id = fields.Many2one('res.partner',string = "Nom de l'établissement")
	lot = fields.Integer(string = "Lot N")
	page = fields.Integer(string = "Page")
	line = fields.Integer(string = "Ligne")
	currency_id = fields.Many2one('res.currency','Currency',default=lambda self: self.env.company.currency_id.id)
	amount = fields.Monetary(string = "Montant")
	observations = fields.Text(string = "Observations")
	document = fields.Many2many('ir.attachment',string = "Joindre le document")

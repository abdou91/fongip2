# -*- coding: utf-8 -*-

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    number_of_days = fields.Float(
    	string="Attribution Jours par mois",
    	default=2.0,
    	config_parameter='hr_holidays_inherit.number_of_days'
    )
    automatic_validation = fields.Float(
    	string="Validation Automatique",
        default=10,
    	config_parameter='hr_holidays_inherit.number_of_days_before_validate_leave'
    )
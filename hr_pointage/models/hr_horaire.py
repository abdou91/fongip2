from datetime import date
from odoo import api, fields, models


class HRHoraire(models.Model):
    _name = "hr.horaire"
    _description = "Definition des horaires"
    _order = "active_horaire desc"

    name = fields.Char(string="Titre")
    flexible = fields.Boolean()
    entry_time = fields.Float(string="Heure d'entree")
    exit_time = fields.Float(string="Heure de sortie")
    flexible_entry_time = fields.Float(string="Heure d'entree flexible")
    flexible_exit_time = fields.Float(string="Heure de sortie flexible")
    active_horaire = fields.Boolean(default=True)
    user_id = fields.Many2one('res.users', string='Utilisateur')
    inactive_date = fields.Date()

    @api.model
    @api.returns('self', lambda value: value.id)
    def create(self, vals):
    	#A la creation d'une nouvelle horaire on désactive les autres
    	self.search([('active_horaire','=', True)]).write({
    		'active_horaire': False,
    	})
    	self.flush()
    	#On active celle qu'on vient de créer
    	vals['active_horaire'] = True
    	return super(HRHoraire, self).create(vals)

    def write(self, vals):
        return super(HRHoraire, self).write(vals)

    def action_active(self):
    	self.search([('active_horaire','=', True)]).write({
    		'active_horaire': False,
    	})
    	self.flush()
    	self.active_horaire = True
    	return

    def action_inactive(self):
    	self.active_horaire = False
    	self.user_id = self.env.user.id
    	self.inactive_date = date.today()
    	return


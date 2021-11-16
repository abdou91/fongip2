# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

TYPE_POINTAGE = [
    ('entree', 'Entrée'),
    ('sortie_pause', 'Sortie Pause'),
    ('retour_pause', 'Retour Pause'),
    ('sortie', 'Sortie'),
]


class PointageManuel(models.Model):
    _name = "pointage.manuel"
    _description = "Pointage manuel"

    @api.depends('date_heure')
    def _compute_date_and_heure_pointage(self):
        if self.date_heure:
            date_heure = str(self.date_heure)
            self.date_pointage, self.heure_pointage = date_heure.split(' ')[0], date_heure.split(' ')[1]

    @api.depends('date_heure')
    def _compute_delay(self):
        #Valeur par défaut
        entry_time = 9; 
        exit_time = 18;
        #Récupération de l'heure d'entree et d'arrivee
        horaire = self.env['hr.horaire'].search([
            ('active_horaire','=', True)
        ], limit=1)
        if horaire:
            if horaire.flexible:
                entry_time = horaire.flexible_entry_time or horaire.entry_time
                exit_time = horaire.flexible_exit_time or horaire.exit_time
            else:
                entry_time = horaire.entry_time
                exit_time = horaire.exit_time
        for res in self:
            if res.date_heure:
                #Calcul de l'heure
                date_hour_time = res.date_heure.time()
                hour_time = date_hour_time.hour + date_hour_time.minute/60.0
                #Type de pointage
                if res.type_pointage == "entree":
                    res.entry_delay = hour_time - entry_time
                    res.entry_time = entry_time
                elif res.type_pointage == "sortie":
                    res.exit_delay = exit_time - hour_time
                    res.exit_time = exit_time
        return

    employee = fields.Many2one('hr.employee', string='Employee', required=True)
    type_pointage = fields.Selection(TYPE_POINTAGE, string='Type de pointage', required=True)
    date_heure = fields.Datetime(string='Date heure', required=True)
    date_pointage = fields.Date(String='Date Pointage', store=True, compute='_compute_date_and_heure_pointage')
    heure_pointage = fields.Char(String='Heure Pointage', store=True, compute='_compute_date_and_heure_pointage')
    presence_id = fields.Many2one('hr.presence', string='Presence')
    is_admin = fields.Boolean(store=True)
    observation = fields.Char(string = "Observation")
    piece_justificative = fields.Many2many('ir.attachment' ,string="Joindre la pièce justificative")
    entry_delay = fields.Float(string="Retard Entrée", compute="_compute_delay", store=True)
    exit_delay = fields.Float(string="Retard Sortie", compute="_compute_delay", store=True)
    entry_time = fields.Float(string="Heure d'entree", compute="_compute_delay", store=True)
    exit_time = fields.Float(string="Heure de sortie", compute="_compute_delay", store=True)


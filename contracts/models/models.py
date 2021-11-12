# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


STATE = [
    ('draft', 'Brouillon'),
    ('confirm', 'Confirmé'),
    ('cancel', 'Annulé'),
    ('validate', 'Validé'),
]

TYPE_AVENANT = [
    ('a_insidence_financiere', 'A insidence financière'),
    ('a_insidence_sur_la_duree', 'A insidence sur la durée'),
]

UNITE_MESURE = [('days', 'Jours'), ('months', 'Mois'), ('years', 'Année')]


class IRAttachment(models.Model):
    _name = 'ir.attachment'
    _inherit = 'ir.attachment'
    annexe_ids = fields.Many2many('contract', string=u'Contractants')
    # avenant_ids = fields.Many2many('contract', 'avenant_ids', string=u'Contractants')


class Respartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'
    contract_ids = fields.Many2many(
        'contract', 'contractant_ids', string=u'Contractants'
    )
    signataire_ids = fields.Many2many(
        'contract', 'signataire_ids', string=u'Signataires'
    )


class FongipJuridiqueTypeContrat(models.Model):
    _name = 'contract.type'
    _description = "Contracts"
    name = fields.Char(string=u'Type de contrat', size=128)
    code = fields.Char(string=u'Code', size=128)


class FongipJuridiqueContrat(models.Model):
    _name = 'contract'
    _description = 'Contract'
    name = fields.Char(string=u'Nom du contrat', size=128)
    reference = fields.Char(string="Référence")
    type_id_code = fields.Char(compute="_compute_code", store=True, readonly=True)
    type_id = fields.Many2one('contract.type', string=u'Type du contrat')
    contractant_ids = fields.Many2many(
        'res.partner', 'contract_ids', string=u'Contractants'
    )
    signataire_ids = fields.Many2many(
        'res.partner', 'signataire_ids', string=u'Signataires'
    )
    duree = fields.Integer(string=u'Durée initiale (en mois)')
    unite_mesure = fields.Selection(UNITE_MESURE, default="months", string="Unité")

    duree_final = fields.Integer(
        string=u'Durée finale (en mois)', compute='_compute_duree_final', store=True
    )
    date_signature = fields.Date(string=u'Date de signature')
    date_effet = fields.Date(string=u"Date de prise d'effet")
    date_limite_preavis = fields.Date(
        compute="_compute_date_limite_preavis",
        store=True,
        readonly=True,
        string=u"Date limite de demande de prevais",
    )
    date_fin = fields.Date(string=u"Date de fin")
    annexe_ids = fields.Many2many('ir.attachment', 'annexe_ids', string="Annexes")
    convention_ids = fields.Many2many('ir.attachment', string="Convention")
    renouvellement_mode = fields.Selection(
        [
            ('renouvelable', "Renouvelable"),
            ('tacite_reconduction', "Tacite Reconduction"),
            ('non_renouvelable', "Non Renouvelable"),
        ],
        string="Mode de renouvellement",
    )
    duree_preavis = fields.Integer(string=u'Durée préavis(en mois)')
    observations = fields.Html(string=u'Observations')
    # avenant_ids = fields.Many2many('ir.attachment', 'avenant_ids', string="Avenants")
    avenant_ids = fields.One2many('contract.avenant', 'contract_id', string="Avenants")
    currency_id = fields.Many2one(
        'res.currency', 'Currency', default=lambda self: self.env.company.currency_id.id
    )
    montant = fields.Monetary(string="Montant initial")
    montant_final = fields.Monetary(
        string="Montant final", compute="_compute_montant_final", store=True
    )
    state = fields.Selection(STATE, default="draft", string="Etat")
    decaissement_ids = fields.One2many(
        'contract.decaissement', 'contract_id', string="Décaissements"
    )
    #budget_id = fields.Many2one('crossovered.budget', string="Budget")
    # budget_line_ids = fields.One2many('crossovered.budget.lines','contract')
    is_confidential_contract = fields.Boolean(
        string='Est un contrat confidentiel', default=False
    )
    contact_person_id = fields.Many2one('hr.employee', string='Personne ressource')

    @api.constrains('montant', 'decaissement_ids')
    def _check_validate_decaissements(self):
        for record in self:
            if (
                record.montant
                and record.decaissement_ids
                and record.montant < sum(record.decaissement_ids.mapped('montant'))
            ):
                raise ValidationError(
                    "La somme des décaissements ne doit pas dépasser le montant du"
                    " contrat"
                )

    @api.depends('date_effet', 'duree_preavis')
    def _compute_date_limite_preavis(self):
        for record in self:
            if record.date_effet and record.duree_preavis:
                date_effet = fields.Date.from_string(
                    record.date_effet
                )  # datetime.strptime(record.date_effet, '%Y-%m-%d')
                date_limite_preavis = date_effet - relativedelta(
                    months=record.duree_preavis
                )
                record.date_limite_preavis = date_limite_preavis

    @api.depends('type_id')
    def _compute_code(self):
        for record in self:
            if record.type_id:
                record.type_id_code = record.type_id.code

    @api.depends('avenant_ids.montant', 'montant')
    def _compute_montant_final(self):
        for record in self:
            record.montant_final = (
                sum(record.avenant_ids.mapped('montant')) + record.montant
            )

    @api.depends('avenant_ids.duree', 'duree')
    def _compute_duree_final(self):
        for record in self:
            record.duree_final = sum(record.avenant_ids.mapped('duree')) + record.duree

    @api.onchange('type_id')
    def onchange_type_id(self):
        if self.type_id:
            self.type_id_code = self.type_id.code

    def get_end_contract_partner(self):
        all_contracts = self.search([])
        contracts_to_end = []
        for contract in all_contracts:
            if contract.date_end and contract.type_id:
                date_end = datetime.strptime(contract.date_fin, '%Y-%m-%d')
                if (
                    date_end - relativedelta(months=2)
                ).date() == datetime.today().date():
                    contracts_to_end.append(
                        {'contract': contract, 'expire_dans': '2 mois'}
                    )
                if (
                    date_end - relativedelta(months=1)
                ).date() == datetime.today().date():
                    contracts_to_end.append(
                        {'contract': contract, 'expire_dans': '1 mois'}
                    )
                    # informer les concernés
                if (date_end.date() - datetime.today().date()).days == 15:
                    contracts_to_end.append(
                        {'contract': contract, 'expire_dans': '15 jours'}
                    )

    def send_mail_end_contract_partner(self):
        # informer certaines personnes
        contracts = self.get_end_contract_partner()
        if contracts:
            template = self.env.ref('contracts.email_template_end_contract')
            self.env['mail.template'].browse(template.id).send_mail(self.id)

    def confirmer(self):
        for record in self:
            record.state = 'confirm'

    def valider(self):
        for record in self:
            record.state = 'validate'

    def annuler(self):
        for record in self:
            record.state = 'cancel'


class ContractDecaissement(models.Model):
    _name = 'contract.decaissement'
    _description = "Décaissement"
    name = fields.Char(string="Référence")
    objet = fields.Char(string="Objet")
    contract_id = fields.Many2one('contract', string="Contrat")
    date = fields.Date(string="Date", required=True)
    currency_id = fields.Many2one(
        'res.currency', 'Currency', default=lambda self: self.env.company.currency_id.id
    )
    montant = fields.Monetary(string="Montant", required=True)

    @api.model
    def create(self, vals):
        vals['name'] = "Décaissement du " + str(vals['date'])
        return super(ContractDecaissement, self).create(vals)


class ContractAvenant(models.Model):
    _name = 'contract.avenant'
    _description = 'Avenant'

    objet = fields.Char(string="Objet")
    montant = fields.Monetary(string="Montant")
    duree = fields.Integer(string="Durée (en mois)")
    unite_mesure = fields.Selection(UNITE_MESURE, default="months", string="Unité")
    type_avenant = fields.Selection(
        TYPE_AVENANT, default='a_insidence_financiere', string="Type d'avenant"
    )
    currency_id = fields.Many2one(
        'res.currency', 'Currency', default=lambda self: self.env.company.currency_id.id
    )
    date = fields.Date(string="Date")
    avenant_ids = fields.Many2many('ir.attachment', string="Joindre l'avenant")
    contract_id = fields.Many2one('contract', string="Contrat")

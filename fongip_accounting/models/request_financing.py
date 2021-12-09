# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _
from datetime import datetime
import xlrd
import base64
from . import excel_utility


RECEPTION_MODE = [
						('dossier_electronique','Dossier électronique'),
						('dossier_physique','Dossier physique'),
				 ]
GENRE = [
                ('Homme','Homme'),
                ('Femme','Femme'),
        ]


class FinancingRequest(models.Model):
    _name = 'financing.request'
    _description = 'Demande de financement'

    name = fields.Char()
    order_number = fields.Char(string = "Numéro d'ordre")
    reception_mode = fields.Selection(RECEPTION_MODE,default="dossier_physique",string = "Mode de réception")
    currency_id = fields.Many2one('res.currency','Currency',default=lambda self: self.env.company.currency_id.id)
    project_cost = fields.Monetary(string = "Cout du projet")
    credit_requested = fields.Monetary(string = "Crédit sollicité")
    quotite = fields.Float(string = "Quotité de garantie",default=70)
    guarantee_amount = fields.Monetary(string = "Garantie éventuelle",compute = '_compute_guarantee_amount',store=True)
    transmission_date = fields.Date(string = "Date de transmission")
    number_of_job = fields.Integer(string = "Nombre d'emplois")
    imputation_date = fields.Date(string = "Date d'imputation à l'ingénieur")
    transmitted_to = fields.Many2one('hr.employee',string = "Transmis à")
    partner_id =  fields.Many2one('res.partner',string = "Porteur de projet")
    date = fields.Date(string = "Date")
    email = fields.Char(string = "Email", related='partner_id.email')
    phone = fields.Char(string = "Numéro téléphone",related='partner_id.mobile')
    genre = fields.Selection(GENRE, string = "Genre")
    legal_status_id = fields.Many2one('legal.status',store=True,string = "Forme juridique",related = 'partner_id.parent_id.legal_status_id')
    activity_sector_id = fields.Many2one('activity.sector',store=True,string = "Secteur d'activité",related = 'partner_id.parent_id.activity_sector_id')
    filiere_id = fields.Many2one('financing.filiere',store=True,string = "Filière",related='partner_id.parent_id.filiere_id')
    region_id = fields.Many2one('res.country.region', store=True,string = "Région",related='partner_id.parent_id.region_id')

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.genre = self.partner_id.genre


    @api.depends('credit_requested','quotite')
    def _compute_guarantee_amount(self):
        for record in self:
            if record.credit_requested and record.quotite:
                record.guarantee_amount = (record.credit_requested * record.quotite) // 100

    """@api.model
    def create(self,vals):
        create_date = fields.Datetime.to_string(self.create_date)[0]
        number = self.env['ir.sequence'].next_by_code('financing.request')
        vals['order_number'] = create_date + '-' + number
        return super(FinancingRequest,self).create(vals)"""


class FinancingRequestImport(models.Model):
    _name = 'financing.request.import'
    _description = 'Import demande de financement'

    import_date = fields.Datetime(string = "Date d'import",default=lambda self: fields.Datetime.now())
    filename = fields.Char('File Name')
    data = fields.Binary('Importer le fichier')
    request_line_ids = fields.One2many('financing.request.line','financing_request_id',string = "Ligne de demandes")
    imported_by = fields.Many2one('res.users',string = "Importé par",default = lambda self: self.env.user.id)
    state = fields.Selection([('draft','Brouillon'),('confirmed','Confirmé'),('cancelled','Annulé')],default='draft',string = "Etat")

    def cancel(self):
        for record in self:
            record.state = "cancelled"
            
    def confirm(self):
        for record in self:
            if record.request_line_ids:
                dico = {}
                for request_line in record.request_line_ids:
                    if not request_line.phone:
                        continue
                    dico['transmission_date'] = request_line.transmission_date
                    dico['number_of_job'] = request_line.number_of_job
                    dico['project_cost'] = request_line.project_cost
                    dico['credit_requested'] = request_line.credit_requested
                    #dico['guarantee_amount'] = request_line.guarantee_amount
                    dico['imputation_date'] = request_line.imputation_date
                    dico['reception_mode'] = request_line.reception_mode
                    dico['genre'] = request_line.genre
                    
                    customer = self.env['res.partner'].search([('mobile','=',request_line.phone)],limit=1)
                    if customer:
                        dico['partner_id'] = customer.id
                    else:
                        #customer
                        customer_dico = {}
                        customer_dico['name'] = request_line.customer_name
                        customer_dico['genre'] = request_line.genre
                        customer_dico['mobile'] = request_line.phone
                        customer_dico['email'] = request_line.email
                        customer_company = self.env['res.partner'].search([('name','like',request_line.customer_company_name),('company_type','=','company')],limit=1)
                        if not customer_company:
                            company_dico = {}
                            company_dico['name'] = request_line.customer_company_name
                            company_dico['company_type'] = 'company'
                            legal_status = self.env['legal.status'].search([('name','=',request_line.legal_status_name)],limit=1)
                            if legal_status:
                                company_dico['legal_status_id'] = legal_status.id
                            else:
                                legal_status = self.env['legal.status'].create({'name':request_line.legal_status_name,'description':request_line.legal_status_name})
                                company_dico['legal_status_id'] = legal_status.id
                            if request_line.sector_name:
                                filiere = self.env['financing.filiere'].search([('name','=',request_line.sector_name)],limit=1)
                                if filiere:
                                    company_dico['filiere_id'] = filiere.id
                                    company_dico['activity_sector_id'] = filiere.activity_sector_id.id
                                else:
                                    if request_line.activity_sector_name:
                                        activity_sector = self.env['activity.sector'].search([('name','=',request_line.activity_sector_name)],limit=1)
                                        if activity_sector:
                                            company_dico['activity_sector_id'] = activity_sector.id
                                            filiere = self.env['financing.filiere'].create({'name':request_line.sector_name,'activity_sector_id':activity_sector.id})
                                            company_dico['filiere_id'] = filiere.id
                                        else:
                                            activity_sector = self.env['activity.sector'].create({'name':request_line.activity_sector_name})
                                            filiere = self.env['financing.filiere'].create({'name':request_line.sector_name,'activity_sector_id':activity_sector.id})
                                            company_dico['filiere_id'] = filiere.id
                                            company_dico['activity_sector_id'] = activity_sector.id
                            #region
                            region = self.env['res.country.region'].search([('name','=',request_line.region_name)],limit=1)
                            if region:
                                company_dico['region_id'] = region.id
                            else:
                                region = self.env['res.country.region'].create({'name':request_line.region_name})
                                company_dico['region_id'] = region.id
                            #create company
                            company = self.env['res.partner'].create(company_dico)
                            customer_dico['parent_id'] = company.id
                        customer = self.env['res.partner'].create(customer_dico)
                    dico['partner_id'] = customer.id
                    employee = self.env['hr.employee'].search([('name','like',request_line.transmitted_to)],limit=1)
                    if employee:
                        dico['transmitted_to'] = employee.id
                    #create financing_request
                    self.env['financing.request'].create(dico)
            record.state = 'confirmed'

    @api.onchange('data')
    def import_request_financing_data(self):
        if self.data:
            wb = xlrd.open_workbook(file_contents=base64.decodestring(self.data))
            sheet = wb.sheets()[0]
            values = []
            """for s in wb.sheets():
                values = []"""
            for row in range(3,sheet.nrows):
                col_value = []
                for col in range(1,sheet.ncols):
                    value = sheet.cell(row, col).value
                    col_value.append(value)
                values.append(col_value)
            dicos = self.fusion(values)
            lines = []
            for dic in dicos:
                lines.append((0, 0, dic))
            self.request_line_ids = lines
        return

    def fusion(self, liste):
        columns = [
                    'transmission_date',
                    'reception_mode',
                    'customer_name',
                    'genre',
                    'email',
                    'phone',
                    'customer_company_name',
                    'legal_status_name',
                    'activity_sector_name',
                    'sector_name',
                    'region_name',
                    'project_cost',
                    'credit_requested',
                    'guarantee_amount',
                    'number_of_job',
                    'imputation_date',
                    'transmitted_to'
                    ]
        dicos = []
        for i in range(0, len(liste)):
            dicos.append(dict(zip(columns, liste[i])))
        for i in range(len(dicos)):
            for key in dicos[i]:
                if 'transmission_date' == key and dicos[i][key]:
                    dicos[i][key] = excel_utility.convert_excel_date_to_python_date(dicos[i][key])
                if 'imputation_date' == key and dicos[i][key]:
                    dicos[i][key] = excel_utility.convert_excel_date_to_python_date(dicos[i][key])
                if 'reception_mode' == key and dicos[i][key]:
                    reception_mode = dicos[i][key]
                    if reception_mode.strip().lower() == "dossier électronique":
                        dicos[i][key] = "dossier_electronique"
                    else:
                        dicos[i][key] = "dossier_physique"

        return dicos

    """def clear_imported_lines(self):
        for request_line in self.request_line_ids:
            request_line.unlink()
            if critere.display_type not in ['line_section', 'line_note']:
                critere.unlink()
        self.data = False
        return

    def clear_section_lines(self):
        for request_line in self.request_line_ids:

            if critere.display_type in ['line_section', 'line_note']:
                critere.unlink()
        self.data = False
        return"""

    def clear_all_lines(self):
        self.request_line_ids.unlink()
        self.data = False
        return


class FinancingRequestLine(models.Model):
    _name = 'financing.request.line'
    _description = 'Ligne demande de financement'

    transmission_date = fields.Date(string = "Date de transmission")
    reception_mode = fields.Selection(RECEPTION_MODE,default="dossier_physique",string = "Mode de réception")
    customer_name = fields.Char(string = "Prénom et nom du porteur de projet")
    genre = fields.Selection(GENRE, string = "Genre",default = "Homme")
    email = fields.Char(string = "Email")
    phone = fields.Char(string = "Numéro téléphone")
    customer_company_name = fields.Char(string = "Raison sociale entreprise")
    legal_status_name = fields.Char(string = "Forme juridique")
    activity_sector_name = fields.Char(string = "Secteur d'activité")
    sector_name = fields.Char(string = "Activité")
    region_name = fields.Char(string = "Région")
    currency_id = fields.Many2one('res.currency','Currency',default=lambda self: self.env.company.currency_id.id)
    project_cost = fields.Monetary(string = "Cout du projet")
    credit_requested = fields.Monetary(string = "Crédit sollicité")
    quotite = fields.Float(string = "Quotité de garantie")
    guarantee_amount = fields.Monetary(string = "Garantie éventuelle")
    number_of_job = fields.Integer(string = "Nombre d'emplois")
    imputation_date = fields.Date(string = "Date d'imputation à l'ingénieur")
    transmitted_to = fields.Char(string = "Transmis à")
    financing_request_id = fields.Many2one('financing.request.import',string = 'Demande de financement')
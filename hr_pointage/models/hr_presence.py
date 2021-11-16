# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from datetime import date
from dateutil.relativedelta import relativedelta
from random import randint
from odoo import api, fields, models, SUPERUSER_ID, _

HIDE = [
    ('DISPLAY', 'o'),
    ('NODISPLAY', 'n'),
]


class HRPresence(models.Model):
    _name = "hr.presence"
    _inherit = ['mail.thread']
    _description = "Liste de Presence"
    
    @api.depends('employee', 'date_from', 'date_to')
    def _compute_pointage_statistique(self):
        element = []
        if self.env.user.id not in [SUPERUSER_ID, 2]:
            self.employee = self.env["hr.employee"].search([
                ('user_id', '=', self.env.user.id),
            ], limit=1)

        if not self.employee and not self.date_from:
            self.hide_diff_presence = 'NODISPLAY'
            all_pointage_user = self.env["pointage.manuel"].search([])
            self.pointage_manuel_ids = all_pointage_user
        
        elif self.employee and not self.date_from:
            all_pointage_user = self.env["pointage.manuel"].search([
                ('employee', '=', self.employee.id)
            ])
            self.pointage_manuel_ids = all_pointage_user
            
        elif self.employee and self.date_from:
            self.hide_diff_presence = 'DISPLAY'
            #Par defaut on prend la date_from
            self.date_to = self.date_to or self.date_from
            date_from = datetime.strptime(str(self.date_from) + ' ' + '00:00:00', '%Y-%m-%d %H:%M:%S')
            date_to = datetime.strptime(str(self.date_to) + ' ' + '23:59:59', '%Y-%m-%d %H:%M:%S')
            all_pointage_user = self.env["pointage.manuel"].search([
                ('employee', '=', self.employee.id),
                ('date_heure', '>=', fields.Date.to_string(date_from)),
                ('date_heure', '<=', fields.Date.to_string(date_to)),
            ])

            self.pointage_manuel_ids = all_pointage_user

            #working time delta
            #self.horaire_a_faire = len(all_pointage_user) * 8
            self.diff_presence = self.compute_working_time(date_from, date_to, self.employee.id)[0]
            nb_jours_pointes = self.compute_working_time(date_from, date_to, self.employee.id)[1]
            self.nb_jours_pointes = nb_jours_pointes
            self.horaire_a_faire =  nb_jours_pointes * 8
            
        elif not self.employee and self.date_from:
            self.hide_diff_presence = 'NODISPLAY'
            self.date_to = self.date_to or self.date_from
            date_from = datetime.strptime(str(self.date_from) + ' ' + '00:00:00', '%Y-%m-%d %H:%M:%S')
            date_to = datetime.strptime(str(self.date_to) + ' ' + '23:59:59', '%Y-%m-%d %H:%M:%S')
            all_pointage_user = self.env["pointage.manuel"].search([
                ('date_heure', '>=', fields.Date.to_string(date_from)),
                ('date_heure', '<=', fields.Date.to_string(date_to)),
            ])
            self.pointage_manuel_ids = all_pointage_user
        return    

    employee = fields.Many2one('hr.employee', string='Employee')
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    diff_presence = fields.Float(string='Presence', compute='_compute_pointage_statistique', store=True)
    nb_jours_pointes = fields.Integer(string="Nombre de jours pointes",compute='_compute_pointage_statistique', store=True)
    horaire_a_faire = fields.Float(string='Sur ', compute='_compute_pointage_statistique', store=True)
    hide_diff_presence = fields.Selection(HIDE, store=True)
    pointage_manuel_ids = fields.One2many('pointage.manuel', 'presence_id', string='Presences', compute='_compute_pointage_statistique', store=True)
    current_user = fields.Boolean(defaut=True, store=True)

    @api.model
    def default_get(self, fields):
        res = super(HRPresence, self).default_get(fields)
        employee_is_related_user = self.env["hr.employee"].search([
            ('user_id', '=', self.env.user.id),
        ], limit=1)
        if 'employee' in fields and employee_is_related_user:
            res.update({
                'employee' : employee_is_related_user.id,
            })
        return res

    def compute_working_time(self,date_from, date_to, employee_id):
        working_time = 0
        FMT = '%H:%M:%S'
        nb_jours_pointes = 0

        while date_from <= date_to:
            str_date_from = str(date_from).split(' ')[0]
            entree=[]
            sortie=[]
            #ALL pointage
            pointage_all = self.env["pointage.manuel"].search([
                ('employee', '=', employee_id),
                ('date_pointage', '=', str_date_from),
            ])
            if pointage_all:
                nb_jours_pointes += 1
                #On regroupe par categorie
                for pointage in pointage_all:
                    #type IN
                    if pointage.type_pointage in ['entree', 'retour_pause']:
                        entree.append(pointage.heure_pointage)
                    #type OUT
                    if pointage.type_pointage in ['sortie', 'sortie_pause']:
                        sortie.append(pointage.heure_pointage)
                if entree and sortie:
                    for index in range(min(len(entree), len(sortie))):
                        tdelta_day_work_time = datetime.strptime(sortie[index], FMT) - datetime.strptime(entree[index], FMT)
                        working_time += tdelta_day_work_time.total_seconds()/3600.0
            date_from = date_from + relativedelta(days=1)
        return working_time , nb_jours_pointes

    def chargement_donnees_test_pointage(self):
        """
        Job desactivité par defaut
        A lancer manuellement
        A utiliser pour charger des données de test (Pointage manuel semaine precedente)
        """
        liste_heure_entree = ['07:30:00', '08:00:00', '08:15:00', '08:30:00', '08:30:00', '09:50:00', '10:15:00', '10:30:00']
        liste_heure_sortie_pause = ['13:00:00', '13:05:00', '13:15:00', '13:30:00', '13:50:00', '13:45:00', '13:59:00', '13:55:00']
        liste_heure_retour_pause = ['14:00:00', '14:05:00', '14:15:00', '14:30:00', '14:50:00', '15:00:00', '15:15:00', '15:30:00']
        liste_heure_sortie = ['17:30:00', '18:00:00', '18:30:00', '18:45:00', '18:50:00', '19:00:00', '19:30:00', '20:30:00']
        today = datetime.today()
        tdelta = timedelta(days=today.weekday(), weeks=1)
        #Lundi semaine passée
        date_from = today - tdelta
        #Vendredi semaine passée
        date_to = date_from + timedelta(days=16)
        all_employees = self.env["hr.employee"].search([])
        for employee in all_employees:
                date_from_employee = date_from
                while date_from_employee <= date_to:
                    date_from_point_entree = str(date_from_employee).split(' ')[0] + ' ' + liste_heure_entree[randint(0, len(liste_heure_entree)-1)]
                    date_from_point_sortie_pause = str(date_from_employee).split(' ')[0] + ' ' + liste_heure_sortie_pause[randint(0, len(liste_heure_sortie_pause)-1)]
                    date_from_point_retour_pause = str(date_from_employee).split(' ')[0] + ' ' + liste_heure_retour_pause[randint(0, len(liste_heure_retour_pause)-1)]
                    date_from_point_sortie = str(date_from_employee).split(' ')[0] + ' ' + liste_heure_sortie[randint(0, len(liste_heure_sortie)-1)]
                    self.env['pointage.manuel'].create({
                        'employee': employee.id,
                        'type_pointage': 'entree',
                        'date_heure': date_from_point_entree,
                    })
                    self.flush()
                    self.env['pointage.manuel'].create({
                        'employee': employee.id,
                        'type_pointage': 'sortie_pause',
                        'date_heure': date_from_point_sortie_pause,
                    })
                    self.flush()
                    self.env['pointage.manuel'].create({
                        'employee': employee.id,
                        'type_pointage': 'retour_pause',
                        'date_heure': date_from_point_retour_pause,
                    })
                    self.flush()
                    self.env['pointage.manuel'].create({
                        'employee': employee.id,
                        'type_pointage': 'sortie',
                        'date_heure': date_from_point_sortie,
                    })
                    self.flush()
                    date_from_employee = date_from_employee + relativedelta(days=1)
        return

    def action_send_presence(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference('hr_pointage', 'email_template_edi_presence')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'hr.presence',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
        })
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    def action_print_presence(self):
        return self.env.ref('hr_pointage.report_hr_pointage_presence').report_action(self)

    def get_horaire_employee(self, date, employee_id):
        observation = ""
        #Heure d'entrée
        pointage_entree = self.env["pointage.manuel"].search([
        	('employee', '=', employee_id),
            ('date_pointage', '=', date),
            ('type_pointage', '=', 'entree')
        ], limit=1)
        pointage_entree_time = pointage_entree.heure_pointage
        if pointage_entree.observation:
            observation += pointage_entree.observation +","
        #Heure Sortie pause
        pointage_sortie_pause = self.env["pointage.manuel"].search([
            ('employee', '=', employee_id),
            ('date_pointage', '=', date),
            ('type_pointage', '=', 'sortie_pause')
        ], limit=1)
        pointage_sortie_pause_time = pointage_sortie_pause.heure_pointage
        if pointage_sortie_pause.observation:
            observation += pointage_sortie_pause.observation + ","
        #Heure Retour Pause
        pointage_retour_pause = self.env["pointage.manuel"].search([
            ('employee', '=', employee_id),
            ('date_pointage', '=', date),
            ('type_pointage', '=', 'retour_pause')
        ], limit=1)
        pointage_retour_pause_time = pointage_retour_pause.heure_pointage
        if pointage_retour_pause.observation:
            observation += pointage_retour_pause.observation + "," 
        #Heure descente
        pointage_sortie = self.env["pointage.manuel"].search([
            ('employee', '=', employee_id),
            ('date_pointage', '=', date),
            ('type_pointage', '=', 'sortie')
        ], limit=1)
        pointage_sortie_time = pointage_sortie.heure_pointage
        if pointage_sortie.observation:
            observation += pointage_sortie.observation + ","
        return {
            'entree': pointage_entree_time,
            'sortie_pause': pointage_sortie_pause_time,
            'retour_pause': pointage_retour_pause_time,
            'sortie': pointage_sortie_time,
            'observation' : observation[:-1],
        }

    def new_compute_working_time(self,date_from,date_to,employee):
        working_time = 0
        entry_delay = 0
        exit_delay = 0
        FMT = '%H:%M:%S'
        from_date = date_from
        while from_date <= date_to:
            entree = []
            sortie = []
            #All pointage
            pointage_all = self.env['pointage.manuel'].search([('employee','=',employee.id),('date_pointage','=',fields.Date.to_string(from_date))])
            if pointage_all:
                for pointage in pointage_all:
                    if pointage.type_pointage in ['entree', 'retour_pause']:
                        entree.append(pointage.heure_pointage)
                        if pointage.type_pointage == 'entree':
                            entry_delay += pointage.entry_delay
                    else:
                        sortie.append(pointage.heure_pointage)
                        if pointage.type_pointage == 'sortie':
                            exit_delay += pointage.exit_delay
                if entree and sortie :
                    for index in range(min(len(entree),len(sortie))):
                        tdelta_day_work_time = datetime.strptime(sortie[index], FMT) - datetime.strptime(entree[index], FMT)
                        working_time += tdelta_day_work_time.total_seconds()/3600.0

            from_date = from_date + relativedelta(days=1)

        return working_time, entry_delay, exit_delay

    def compute_working_time(self,date_from, date_to, employee_id):
        working_time = 0
        FMT = '%H:%M:%S'
        nb_jours_pointes = 0
        while date_from <= date_to:
            str_date_from = str(date_from).split(' ')[0]
            entree=[]
            sortie=[]
            #ALL pointage
            pointage_all = self.env["pointage.manuel"].search([
                ('employee', '=', employee_id),
                ('date_pointage', '=', str_date_from),
            ])
            if pointage_all:
                nb_jours_pointes += 1
                #On regroupe par categorie
                for pointage in pointage_all:
                    #type IN
                    if pointage.type_pointage in ['entree', 'retour_pause']:
                        entree.append(pointage.heure_pointage)
                    #type OUT
                    if pointage.type_pointage in ['sortie', 'sortie_pause']:
                        sortie.append(pointage.heure_pointage)
                if entree and sortie:
                    for index in range(min(len(entree), len(sortie))):
                        tdelta_day_work_time = datetime.strptime(sortie[index], FMT) - datetime.strptime(entree[index], FMT)
                        working_time += tdelta_day_work_time.total_seconds()/3600.0
            date_from = date_from + relativedelta(days=1)
        return working_time , nb_jours_pointes

    def get_pointages(self,date_from,date_to,employee):
        from_date = fields.Date.from_string(date_from)
        to_date = fields.Date.from_string(date_to)
        pointage = []
        while from_date <= to_date:
            if from_date.weekday() not in [5,6]:
                dico = self.get_horaire_employee(fields.Date.to_string(from_date), employee.id)
                dico['date_pointage'] = fields.Date.to_string(from_date)
                #wk_time = self.compute_working_time(from_date, from_date, employee.id)[0]
                wk_time, entry_delay, exit_delay = self.new_compute_working_time(from_date,from_date,employee)
                dico['presence'] = round(wk_time, 2)
                dico['entry_delay'] = entry_delay
                dico['exit_delay'] = exit_delay
                pointage.append(dico)
            from_date = from_date + relativedelta(days=1)
        return pointage

    def day_is_not_pointed(self , str_date):
        pointages = self.env["pointage.manuel"].search([('date_pointage','=',str_date)])
        if pointages:
            return False
        else:
            return True

    def get_number_of_friday(self,date_from,date_to):
        nb_fridays = 0
        from_date = fields.Date.from_string(date_from)
        to_date = fields.Date.from_string(date_to)
        while from_date <= to_date:
            if from_date.weekday() == 4 and not self.day_is_not_pointed(fields.Date.to_string(from_date)):
                nb_fridays += 1
            from_date = from_date + relativedelta(days=1)
        return nb_fridays

    def employee_is_missing(self,date,employee):
        if not self.day_is_not_pointed(date):
            pointages = self.env['pointage.manuel'].search([('date_pointage','=',date),('employee','=',employee.id)])
            if pointages:
                return False
            else:
                return True

    def employee_est_en_mission(self,date,employee):
        return False

    def employee_est_en_conge(self,date,employee):
        return False

    def compute_pointed_day_for_employee(self,employee,date_from,date_to):
        from_date = fields.Date.from_string(date_from)
        to_date = fields.Date.from_string(date_to)
        nbre_jour_en_conges = 0
        nbre_jour_en_mission = 0
        nbre_jour_absentes = 0
        nbre_jour_travailles = 0
        absences_justifiees = 0
        nbre_jours_pointes = self.get_number_of_pointed_day(date_from,date_to)
        while from_date <= to_date:
            if self.employee_is_missing(fields.Date.to_string(from_date),employee):
                if self.employee_est_en_mission(fields.Date.to_string(from_date),employee):
                    nbre_jour_en_mission +=1
                elif self.employee_est_en_conge(fields.Date.to_string(from_date),employee):
                    nbre_jour_en_conges +=1
                else:
                    nbre_jour_absentes +=1
                    if self.missing_day_is_justify(employee,fields.Date.to_string(from_date)):
                        absences_justifiees += 1
            from_date = from_date + relativedelta(days=1)
        nbre_jour_travailles = nbre_jours_pointes - (nbre_jour_en_mission + nbre_jour_en_conges + absences_justifiees)
        return nbre_jour_travailles,nbre_jour_en_conges,nbre_jour_en_mission,nbre_jour_absentes

    def get_number_of_pointed_day(self,date_from,date_to):
        nbre_jour_pointes = 0
        from_date = fields.Date.from_string(date_from)
        to_date = fields.Date.from_string(date_to)
        while from_date <= to_date:
            if from_date.weekday() not in [5,6]:
                if not self.day_is_not_pointed(fields.Date.to_string(from_date)):
                    nbre_jour_pointes += 1
            from_date = from_date + relativedelta(days=1)
        return nbre_jour_pointes

    def missing_day_is_justify(self,employee,date):
        if employee and date:
            absence = self.env['hr.absence'].search([
                ('employee','=',employee.id),
                ('state','=','done'),
                ('date_from','<=',date),
                ('date_to','>=',date)
            ],limit=1)
            if absence:
                return True
        return False

    def missing_day_is_holiday(self,employee,date):
        if employee and date:
            leave = self.env['hr.leave'].search([
                ('employee_id','=',employee.id),
                ('state','=','validate'),
                ('date_from','<=',date),
                ('date_to','>=',date)
            ],limit=1)
            if leave:
                return True
        return False

    def send_mail_working_statistique(self):
    	template_id = self.env.ref('hr_pointage.email_template_edi_presence')
    	self.env['mail.template'].browse(template_id.id).sudo().send_mail(self.id)


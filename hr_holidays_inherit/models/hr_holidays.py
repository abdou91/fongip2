# -*- coding: utf-8 -*-

from time import strftime
from calendar import monthrange
from datetime import datetime, date, timedelta
import requests
from dateutil.relativedelta import relativedelta
from random import randint

from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError

from . import api_sms


class HolidaysAllocation(models.Model):
    _inherit = 'hr.leave.allocation'

    category = fields.Selection(
        string='Catégorie', related='holiday_status_id.category'
    )

    def scheduler_increment_employee_holidays(self):
        pass
        # month = int(date.today().strftime("%m"))
        # year = date.today().strftime("%Y")
        # params = self.env['ir.config_parameter'].sudo()
        # number_of_days = float(params.get_param('hr_holidays_inherit.number_of_days'))
        # month_letter = ""
        # if month == 1:
        #     month_letter = "janvier"
        # if month == 2:
        #     month_letter = "février"
        # if month == 3:
        #     month_letter = "mars"
        # if month == 4:
        #     month_letter = "avril"
        # if month == 5:
        #     month_letter = "mai"
        # if month == 6:
        #     month_letter = "juin"
        # if month == 7:
        #     month_letter = "juillet"
        # if month == 8:
        #     month_letter = "août"
        # if month == 9:
        #     month_letter = "septembre"
        # if month == 10:
        #     month_letter = "octobre"
        # if month == 11:
        #     month_letter = "novembre"
        # if month == 12:
        #     month_letter = "décembre"
        # description = "Congé du mois de " + month_letter + " " + year
        # all_employees = self.env["hr.employee"].search([])
        # leave_type_id = (
        #     self.env['hr.leave.type'].search([('category', '=', 'paid')], limit=1).id
        # )
        # if leave_type_id:
        #     for employee in all_employees:
        #         res = self.env['hr.leave.allocation'].create(
        #             {
        #                 'name': description,
        #                 'holiday_status_id': leave_type_id,
        #                 'number_of_days': number_of_days,
        #                 'holiday_type': 'employee',
        #                 'employee_id': employee.id,
        #             }
        #         )
        #         res.sudo().action_validate()
        # return


# HolidaysStaus
class hr_holidays_status(models.Model):
    _inherit = 'hr.leave.type'

    delai_soumission = fields.Integer(string="Délai de soumission(en jours)")
    nbre_de_jours = fields.Integer(string="Duree par defaut")
    category = fields.Selection(
        [
            ('paid', 'Payé'),
            ('unpaid', 'Sans solde'),
            ('disease', 'Maladie'),
            ('compensation', 'Compensation'),
            ('wedding', 'Mariage'),
            ('anticipated', 'Anticipé'),
            ('birth', 'Naissance'),
            ('death', 'Décès'),
            ('other', 'Autre'),
        ],
        string=u'Catégorie',
    )


# Holidays
class hr_holidays(models.Model):
    _name = 'hr.leave'
    _inherit = 'hr.leave'

    url_redirection = fields.Char(
        String='Url de redirection', compute='compute_generate_url', store='True'
    )
    color = fields.Integer(string='Color')
    max_leaves = fields.Float(
        compute='_compute_user_left_days',
        string='Maximum Allowed',
        help=(
            'This value is given by the sum of all holidays requests with a positive'
            ' value.'
        ),
    )
    leaves_taken = fields.Float(
        compute='_compute_user_left_days',
        string='Leaves Already Taken',
        help=(
            'This value is given by the sum of all holidays requests with a negative'
            ' value.'
        ),
    )
    remaining_leaves = fields.Float(
        compute='_compute_user_left_days',
        string='Remaining Leaves',
        help='Maximum Leaves Allowed - Leaves Already Taken',
    )

    user_to_validate = fields.Many2one(
        'res.users',
        string='Utilsateur a validé',
        compute='_compute_user_to_validate',
        store=True,
    )
    number_day_waiting = fields.Integer(store=True)
    sms_ref = fields.Char(string='Référence', store=True)

    def _compute_user_left_days(self):
        employee_id = (
            self.env.context.get('employee_id')
            or self.env['hr.employee']
            .search([('user_id', '=', self.env.uid)], limit=1)
            .id
        )
        if employee_id:
            res = self.env['hr.holidays.status'].get_days(employee_id)
        else:
            res = {
                sid: {'max_leaves': 0, 'leaves_taken': 0, 'remaining_leaves': 0}
                for sid in self.ids
            }
        for record in self.env['hr.holidays.status']:
            record.leaves_taken = res[record.id]['leaves_taken']
            record.remaining_leaves = res[record.id]['remaining_leaves']
            record.max_leaves = res[record.id]['max_leaves']
            if 'virtual_remaining_leaves' in res[record.id]:
                record.virtual_remaining_leaves = res[record.id][
                    'virtual_remaining_leaves'
                ]

    @api.constrains('date_from')
    def _check_date_from(self):
        if self.date_from and self.date_to:
            number_of_days = self._get_number_of_days(
                datetime.today(), self.date_from, self.employee_id.id
            )['days']
            if number_of_days < self.holiday_status_id.delai_soumission:
                raise ValidationError(
                    "Vous ne pouvez pas soumettre une demande de ce type de congés en"
                    " moins de %s jours de la date prévue de départ"
                    % (self.holiday_status_id.delai_soumission)
                )
        else:
            self.number_of_days = 0

    def action_approve(self):
        res = super(hr_holidays, self).action_approve()
        if self.multi_level_validation:
            validate = self.sudo()._compute_user_to_validate()
            if validate:
                template = self.env.ref(
                    'hr_holidays_inherit.email_template_edi_holidays_permission'
                )
                self.env['mail.template'].browse(template.id).sudo().send_mail(
                    self.id, force_send=True
                )
            else:
                template = self.env.ref(
                    'hr_holidays_inherit.email_template_edi_holidays'
                )
                self.env['mail.template'].browse(template.id).sudo().send_mail(
                    self.id, force_send=True
                )
        return res

    def rapidsms_approve(self, cngref, action):
        leave = self.search([('sms_ref', '=', cngref)], limit=1)
        user_id = leave.user_to_validate.id
        if action and action.lower() == 'ok':
            leave.with_user(user_id).action_approve()
        else:
            leave.with_user(user_id).action_refuse()
        return True

    @api.depends('leave_approvals')
    def _compute_user_to_validate(self):
        for res in self:
            if res.multi_level_validation and res.leave_approvals:
                leave_validation_status = self.env['leave.validation.status'].search(
                    [
                        ('holiday_status', '=', res.id),
                        ('validation_status', '=', False),
                    ],
                    limit=1,
                )
                if leave_validation_status:
                    user = leave_validation_status.validating_users
                    res.user_to_validate = user.id
                    if user.has_group('hr_pointage.group_dg') or user.has_group(
                        'hr_pointage.group_dp'
                    ):
                        res.sms_ref = res.gen_sms_ref()
                        res.notify_rapidsms(user.id)
                    else:
                        res.sms_ref = False
                    return True
                else:
                    res.user_to_validate = False
                    return False
        return True

    def notify_rapidsms(self, user_id):
        emp = self.env['hr.employee'].search([('user_id', '=', user_id)], limit=1)
        if emp and emp.mobile_phone:
            message = (
                f"Bonjour {emp.name} a demande des conges du {self.request_date_to} au"
                f" {self.request_date_from}. Reference: {self.sms_ref}"
            )
            api_sms.send(f"notify {emp.mobile_phone}::{message}", "+221778088471")
        return

    def gen_sms_ref(self):
        ref = f"cng{randint(10, 99)}"
        record = self.search([('sms_ref', '=', ref)])
        if record:
            self.gen_sms_ref()
        return ref

    @api.model
    def create(self, values):
        res = super(hr_holidays, self).create(values)
        if res.multi_level_validation:
            template = self.env.ref(
                'hr_holidays_inherit.email_template_edi_holidays_permission'
            )
            self.env['mail.template'].browse(template.id).sudo().send_mail(
                res.id, force_send=True
            )
        return res

    def action_refuse(self):
        for res in self:
            if res.multi_level_validation:
                template = res.env.ref(
                    'hr_holidays_inherit.email_template_edi_holidays_refuse'
                )
                res.env['mail.template'].browse(template.id).sudo().send_mail(
                    res.id, force_send=True
                )
        return super(hr_holidays, self).action_refuse()

    def action_confirm(self):
        if self.multi_level_validation:
            self.sudo()._compute_user_to_validate()
            template = self.env.ref(
                'hr_holidays_inherit.email_template_edi_holidays_permission'
            )
            self.env['mail.template'].browse(template.id).sudo().send_mail(
                self.id, force_send=True
            )
        return super(hr_holidays, self).action_confirm()

    @api.depends('holiday_status_id')
    def compute_generate_url(self):
        for res in self:
            current_url = (
                self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            )
            menu_id = (
                self.env['ir.model.data']
                .sudo()
                .search(
                    [
                        (
                            'name',
                            '=',
                            'hr_holidays.hr_leave_action_new_request_view_form',
                        )
                    ],
                    limit=1,
                )
            )
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            if base_url and base_url[-1:] != '/':
                base_url += '/'
            db = res._cr.dbname
            res.url_redirection = (
                "{}web?debug{}#id={}&view_type=form&model={}&action={}".format(
                    base_url, db, res.id, "hr.leave", menu_id.res_id
                )
            )

    @api.onchange('holiday_status_id')
    def add_validators(self):
        """Update the tree view and add new validators
        when leave type is changed in leave request form"""

        if self.multi_level_validation:
            li = []
            self.leave_approvals = [(5, 0, 0)]
            li2 = []
            manager = self.employee_id.parent_id.user_id
            if manager:
                m_is_dp = manager.has_group('hr_pointage.group_dp')
                m_is_drh = manager.has_group('hr_pointage.group_drh')
                m_is_dg = manager.has_group('hr_pointage.group_dg')
                if not m_is_dp and not m_is_drh and not m_is_dg:
                    li.append((0, 0, {'validating_users': manager.id}))
            director = self.employee_id.parent_id.parent_id.user_id
            if director and director != manager:
                d_is_dp = manager.has_group('hr_pointage.group_dp')
                d_is_drh = manager.has_group('hr_pointage.group_drh')
                d_is_dg = manager.has_group('hr_pointage.group_dg')
                if not d_is_dp and not d_is_drh and not d_is_dg:
                    li.append((0, 0, {'validating_users': director.id}))
            for user in self.leave_approvals:
                li2.append(user.validating_users.id)
            for l in self.holiday_status_id.leave_validators:
                if l.holiday_validators.id not in li2:
                    li.append((0, 0, {'validating_users': l.holiday_validators.id}))
            self.leave_approvals = li
            # compute Order validation number
            i = 1
            for li in self.leave_approvals:
                li.ordre_validation = i
                i += 1
        else:
            super(hr_holidays, self).add_validators()

    @api.constrains('holiday_status_id', 'date_to', 'date_from')
    def _check_leave_type_validity(self):
        pass

    def sheduler_automatical_validate_holidays(self):
        params = self.env['ir.config_parameter'].sudo()
        number_day_waiting = int(
            params.get_param('hr_holidays_inherit.number_of_days_before_validate_leave')
        )
        hr_leaves = self.search([('state', '=', 'confirm')])
        for hr_leave in hr_leaves:
            if hr_leave.number_day_waiting >= number_day_waiting:
                hr_leaves.state = 'validate'
                hr_leave.number_day_waiting = 0
            hr_leave.number_day_waiting += 1
        return


class LeaveValidationStatus(models.Model):
    """Model for leave validators and their status for each leave request"""

    _inherit = 'leave.validation.status'
    _order = 'ordre_validation'

    ordre_validation = fields.Integer(string="Ordre Validation")

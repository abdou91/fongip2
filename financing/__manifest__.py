# -*- coding: utf-8 -*-
{
    'name': "Financement",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Abdou Mbar Ly",
    'website': "http://www.fongip.sn",

    # Categories can be used to filter modules in modules listing
    #'category': 'HR',
    'category': 'Human Resources/Financing',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'hr',
        'mail',
    ],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/request_financing.xml',
        'views/res_partner.xml',
        #'report/hr_pointage_reports.xml',
        #'report/hr_presence_templates.xml',
        #'data/mail_templates.xml',
        #'views/hr_horaire_views.xml',
        #'views/hr_absence_views.xml',
        #'data/hr_pointage_ir_cron.xml',
    ],
    
    'qweb' : [
    
    ],
    'license': 'LGPL-3',
}

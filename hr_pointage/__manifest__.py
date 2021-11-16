# -*- coding: utf-8 -*-
{
    'name': "Hr Pointage",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Prosentic",
    'website': "http://www.prosentic.sn",

    # Categories can be used to filter modules in modules listing
    'category': 'HR',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'hr',
        'hr_holidays_inherit',
        'mail',
    ],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/hr_pointage_groups.xml',
        'views/hr_pointage_views.xml',
        'report/hr_pointage_reports.xml',
        'report/hr_presence_templates.xml',
        'data/mail_templates.xml',
        'views/hr_horaire_views.xml',
        'views/hr_absence_views.xml',
        'data/hr_pointage_ir_cron.xml',
    ],
    
    'qweb' : [
    
    ],
    'license': 'LGPL-3',
}

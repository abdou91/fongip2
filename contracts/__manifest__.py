# -*- coding: utf-8 -*-
{
    'name': "Contrats et conventions de partenariat",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Module de gestion des conventions et des contrats auprès de la direction juridique et du contentieux. 
    """,

    'author': "Abdou Mbar Ly",
    'website': "http://www.fongip.sn",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/10.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','mail','hr'], #

    # always loaded
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/views.xml',
        #'views/templates.xml',
        'data/convention_type.xml',
        #'report/contract_template.xml',
        #'report/contracts_report.xml',
        #'data/mail_template.xml',
        #'data/cron.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'license': 'LGPL-3',
}

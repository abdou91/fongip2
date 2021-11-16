# -*- coding: utf-8 -*-
{
    'name': "Holidays",
    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,
    'author': "Prosentic",
    'website': "http://www.prosentic.sn",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'HR',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'hr', 
        'hr_holidays',
        'mail',
        'resource',
        'hr_holidays_public',
        'ohrms_holidays_approval',
    ],
    # always loaded
    'data': [
        'views/hr_holidays_views.xml',
        'data/hr_holidays_inherit_data.xml',
        'data/template_mail.xml',
        'views/res_config_settings_views.xml',
        'data/hr_holidays_inherit_ir_cron.xml',
    ],
    
    'qweb' : [],
    'license': 'LGPL-3',
}
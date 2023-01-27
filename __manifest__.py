# -*- encoding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'OT',
    'version': '1.0',
    'category': '',
    'summary': '',
    'description': "",
    'website': '',
    'depends': [
        'base_setup',
        'mail',
        'project',
    ],
    'data': [
        'security/security_views.xml',
        'security/ir.model.access.csv',
        'views/ot_management_views.xml',
        'views/ot_registration_lines_views.xml',
        'data/employee_data.xml',
        'data/mail_template.xml',
    ],
    'installable': True,
    'application': True,
}

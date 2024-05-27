# -*- coding: utf-8 -*-
{
    'name': 'DPT Service Management',
    'version': '1.0',
    'summary': 'Manage Services Information',
    'category': 'Services',
    'author': 'CuongLV',
    'maintainer': 'Your Name',
    'website': 'http://dpt.com',
    'depends': ['base', 'account', 'hr', 'sale', 'sales_team'],
    'data': [
        'security/ir.model.access.csv',
        'data/service_sequence.xml',
        'views/service_view.xml',
    ],
    'installable': True,
    'application': True,
}

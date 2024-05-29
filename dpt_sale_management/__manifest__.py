# -*- coding: utf-8 -*-
{
    'name': 'DPT Sale Management',
    'version': '1.0',
    'summary': 'Manage Sale Information',
    'category': 'Services',
    'author': 'CuongLV',
    'maintainer': 'Your Name',
    'website': 'http://dpt.com',
    'depends': ['sale', 'sale_management', 'dpt_service_management', 'uom'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_service_view.xml',
    ],
    'installable': True,
    'application': True,
}

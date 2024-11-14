# -*- coding: utf-8 -*-
{
    'name': 'DPT Sale Management',
    'version': '1.0',
    'summary': 'Manage Sale Information',
    'category': 'Services',
    'author': 'CuongLV',
    'maintainer': 'Your Name',
    'website': 'http://dpt.com',
    'depends': ['sale', 'sale_management', 'dpt_service_management', 'uom', 'dpt_service_pricelist'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/dpt_sale_calculation.xml',
        'views/sale_order.xml',
        'views/res_partner.xml',
    ],
    'installable': True,
    'application': True,
}

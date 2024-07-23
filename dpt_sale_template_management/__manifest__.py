# -*- coding: utf-8 -*-
{
    'name': 'DPT Sale Template Management',
    'version': '1.0',
    'summary': 'Manage Sale Information',
    'category': 'Services',
    'author': 'CuongLV',
    'maintainer': 'Your Name',
    'website': 'http://dpt.com',
    'depends': ['sale', 'sale_management', 'dpt_service_management', 'uom', 'dpt_service_pricelist','dpt_sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_template.xml',
    ],
    'installable': True,
    'application': True,
}

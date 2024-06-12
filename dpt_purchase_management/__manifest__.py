# -*- coding: utf-8 -*-
{
    'name': 'DPT Purchase Management',
    'version': '1.0',
    'summary': 'Manage Purchase Information',
    'category': 'Services',
    'author': 'CuongLV',
    'maintainer': 'Your Name',
    'website': 'http://dpt.com',
    'depends': ['sale', 'sale_management', 'dpt_service_management', 'purchase', 'stock', 'dpt_sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/dpt_service_management.xml',
        'views/purchase_order.xml',
        'views/sale_order.xml',
    ],
}

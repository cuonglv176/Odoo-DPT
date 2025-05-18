# -*- coding: utf-8 -*-
{
    'name': 'DPT Service Management',
    'version': '1.0',
    'summary': 'Manage Services Information',
    'category': 'Services',
    'author': 'CuongLV',
    'maintainer': 'Your Name',
    'website': 'http://dpt.com',
    'depends': ['base','init_web_tree_view','account', 'hr', 'sale', 'sales_team', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'data/service_sequence.xml',
        'views/service_view.xml',
        'views/service_combo_view.xml',
        'views/product.xml',
    ],
    'installable': True,
    'application': True,
}

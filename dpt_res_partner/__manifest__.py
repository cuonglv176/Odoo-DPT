# -*- coding: utf-8 -*-
{
    'name': 'DPT Res Partner Custom',
    'version': '1.0',
    'summary': 'DPT Res Partner Custom',
    'category': 'Sale',
    'author': 'CuongLV',
    'maintainer': 'Your Name',
    'website': 'http://dpt.com',
    'depends': ['sale', 'sale_management', 'init_web_tree_view', 'base'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_partner.xml',
        'security/ir_rules.xml',
    ],
    'installable': True,
    'application': True,
}

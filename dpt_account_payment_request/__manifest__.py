# -*- coding: utf-8 -*-
{
    'name': 'DPT Account Custom',
    'version': '1.0',
    'summary': 'Manage Accounting',
    'category': 'hr',
    'author': 'CuongLV',
    'maintainer': 'Your Name',
    'website': 'http://dpt.com',
    'depends': ['base', 'account', 'purchase'],
    'data': [
        'security/ir.model.access.csv',
        'data/account_sequence.xml',
        'views/account_payment.xml',
        'views/account_payment_request_type.xml',
        'views/purchase_order.xml',
        'views/menu.xml',
    ],
}

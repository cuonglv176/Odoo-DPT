# -*- coding: utf-8 -*-
{
    'name': 'DPT Account Custom',
    'version': '1.0',
    'summary': 'Manage Accounting',
    'category': 'hr',
    'author': 'CuongLV',
    'maintainer': 'Your Name',
    'website': 'http://dpt.com',
    'depends': ['base', 'account', 'purchase', 'dpt_sale_deposit'],
    'assets': {
        'web.assets_backend': [
            'dpt_account_payment_request/static/src/xml/*.xml',
            'dpt_account_payment_request/static/src/js/*.js'
        ],
    },
    'data': [
        'security/ir.model.access.csv',
        'security/account_security.xml',
        'data/account_sequence.xml',
        'views/account_payment.xml',
        'views/account_payment_request_type.xml',
        'views/purchase_order.xml',
        'views/sale_order.xml',
        'views/menu.xml',
    ],
}

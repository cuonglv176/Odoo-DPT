# -*- coding: utf-8 -*-
{
    'name': 'DPT Sale Deposit',
    'version': '1.0',
    'summary': 'DPT Sale Deposit',
    'category': 'Sale',
    'author': 'CuongLV',
    'maintainer': 'Your Name',
    'website': 'http://dpt.com',
    'depends': ['sale', 'sale_management', 'dpt_service_management', 'uom', 'dpt_service_pricelist',
                'dpt_sale_management', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order.xml',
        'views/account_payment.xml',
    ],
    'installable': True,
    'application': True,
}

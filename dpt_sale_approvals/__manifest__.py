# -*- coding: utf-8 -*-
{
    'name': 'DPT Sale Approvals Price',
    'version': '1.0',
    'summary': 'DPT Sale Approvals Price',
    'category': 'Sale',
    'author': 'CuongLV',
    'maintainer': 'Your Name',
    'website': 'http://dpt.com',
    'depends': ['sale', 'product', 'sale_management', 'dpt_service_management', 'uom', 'dpt_service_pricelist',
                'dpt_account_payment_request',
                'dpt_sale_management', 'approvals'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order.xml',
        'views/dpt_sale_change_price.xml',
        'views/approval_request.xml',
        'views/dpt_service_management_views.xml',
    ],
    'installable': True,
    'application': True,
}

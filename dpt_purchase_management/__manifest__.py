# -*- coding: utf-8 -*-
{
    'name': 'DPT Purchase Management',
    'version': '1.0',
    'summary': 'Manage Purchase Information',
    'category': 'Services',
    'author': 'CuongLV',
    'maintainer': 'Your Name',
    'website': 'http://dpt.com',
    'depends': ['sale', 'sale_management', 'dpt_service_management', 'purchase', 'stock', 'dpt_sale_management', 'uom',
                'dpt_helpdesk_ticket'],
    'data': [
        'security/ir.model.access.csv',
        'data/res_partner.xml',
        'data/package_sequence.xml',
        'views/dpt_service_management.xml',
        'views/order_package_view.xml',
        'views/purchase_order.xml',
        'views/sale_order.xml',
        'views/uom_uom.xml',
    ],
}

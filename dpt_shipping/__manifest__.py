# -*- coding: utf-8 -*-
{
    'name': 'DPT Shipping Management',
    'version': '1.0',
    'summary': 'Manage Sale Stock Information',
    'category': 'Stock',
    'author': 'TuUH',
    'maintainer': 'Your Name',
    'website': 'http://dpt.com',
    'depends': ['dpt_sale_management', 'sale', 'fleet', 'vtg_stock_transfer'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/dpt_shipping_slip.xml',
        'views/dpt_vehicle_stage.xml',
        'views/sale_order.xml',
    ],
}

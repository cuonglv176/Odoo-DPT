# -*- coding: utf-8 -*-
{
    'name': 'DPT Purchase Stock',
    'version': '1.0',
    'summary': 'Manage Purchase Stock',
    'category': 'Services',
    'author': 'TuUH',
    'maintainer': 'TuUH',
    'website': 'http://dpt.com',
    'depends': ['stock', 'dpt_purchase_management', 'dpt_stock_management', 'purchase', 'product', 'sale'],
    'data': [
        'views/stock_picking.xml',
        'views/purchase_order.xml',
        'views/sale_order.xml',
    ],
}

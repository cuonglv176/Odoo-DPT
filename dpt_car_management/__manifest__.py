# -*- coding: utf-8 -*-
{
    'name': 'DPT Car Management',
    'version': '1.0',
    'summary': 'Manage Car Information',
    'category': 'Stock',
    'author': 'TuUH',
    'maintainer': 'Your Name',
    'website': 'http://dpt.com',
    'depends': ['stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/dpt_car_management.xml',
        'views/dpt_car_tracking.xml',
        'views/stock_picking.xml',
    ],
}

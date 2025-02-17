# -*- coding: utf-8 -*-
{
    'name': 'DPT Stock Management',
    'version': '1.0',
    'summary': 'Manage Stock Information',
    'category': 'Stock',
    'author': 'TuUH',
    'maintainer': 'Your Name',
    'website': 'http://dpt.com',
    'depends': ['stock', 'dpt_purchase_management', 'vtg_stock_transfer', 'dpt_sale_management'],
    'data': [
        'views/order_package_view.xml',
        'views/stock_picking.xml',
        'views/stock_warehouse.xml',
        'views/uom_uom.xml',
        'views/stock_quant.xml'
    ],
}

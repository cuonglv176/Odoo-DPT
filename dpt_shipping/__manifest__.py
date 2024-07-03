# -*- coding: utf-8 -*-
{
    'name': 'DPT Shipping Management',
    'version': '1.0',
    'summary': 'Manage Sale Stock Information',
    'category': 'Stock',
    'author': 'TuUH',
    'maintainer': 'Your Name',
    'website': 'http://dpt.com',
    'depends': ['dpt_sale_management', 'sale', 'fleet', 'vtg_stock_transfer', 'dpt_helpdesk_ticket',
                'dpt_stock_management', 'dpt_export_import'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'data/ir_cron.xml',
        'views/fleet_vehicle.xml',
        'views/hr_department.xml',
        'views/dpt_shipping_slip.xml',
        'views/dpt_vehicle_stage.xml',
        'views/sale_order.xml',
        'views/stock_picking.xml',
    ],
}

# -*- coding: utf-8 -*-
{
    'name': 'DPT Export Import',
    'version': '1.0',
    'summary': 'Manage Export Import Information',
    'category': 'Services',
    'author': 'CuongLV',
    'maintainer': 'Your Name',
    'website': 'http://dpt.com',
    'depends': ['sale', 'sale_management', 'dpt_service_management', 'dpt_purchase_management', 'hr', 'purchase',
                'stock', 'dpt_purchase_stock', 'dpt_stock_management', 'dpt_security', 'dpt_helpdesk_ticket',
                'dpt_currency_management'],
    'data': [
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/export_import_view.xml',
        'views/product_template_view.xml',
        'views/export_import_view_line.xml',
        'views/sale_order_view.xml',
        'views/export_import_acfta.xml',
    ],
}

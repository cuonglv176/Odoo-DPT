# -*- coding: utf-8 -*-
{
    'name': "Service Pricelist",
    'author': "TuUH",
    'website': 'http://dpt.com',
    'version': '0.1',
    'depends': ['base', 'product', 'dpt_service_management'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/product_pricelist_item.xml',
        'views/partner_view.xml',
        'views/product_pricelist.xml',
        'views/dpt_service_management.xml',
    ],
}

# -*- coding: utf-8 -*-
{
    'name': "Service Pricelist",
    'author': "TuUH",
    'website': 'http://dpt.com',
    'version': '0.1',
    'depends': ['base', 'product', 'dpt_service_management', 'approvals'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/product_pricelist_item.xml',
        'views/partner_view.xml',
        'data/approval_category_data.xml',
        'views/product_pricelist.xml',
        'views/dpt_service_management.xml',
        'views/product_pricelist_views.xml',
        'wizards/pricelist_reject_wizard_views.xml',
    ],
}

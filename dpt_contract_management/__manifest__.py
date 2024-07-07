# -*- coding: utf-8 -*-
{
    'name': "DPT Contract Management",
    'summary': """DPT Contract Management""",
    'description': """ DPT Contract Management """,
    'author': "Binhdh",
    'website': "",
    'category': 'Uncategorized',
    'version': '0.1',
    # any module necessary for this one to work correctly
    'depends': ['dpt_purchase_management', 'dpt_sale_management'],
    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/dpt_contract_management_views.xml',
        'views/dpt_creat_new_contract_views.xml',
        'views/purchase_order_views.xml',
        'views/sale_order_views.xml',
        'views/res_partner_views.xml',
        'data/service_sequence.xml',
        'report/contract_pdf.xml',
        'report/sub_contract_pdf.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
}

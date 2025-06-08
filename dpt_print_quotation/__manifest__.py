# -*- coding: utf-8 -*-
{
    'name': "DPT Print Quotation",

    'summary': "",

    'depends': ['base', 'sale', 'dpt_sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'wizards/dpt_quotation_print_wizard.xml',
        'views/sale_order.xml',
    ],
}

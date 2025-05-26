# -*- coding: utf-8 -*-
{
    'name': "DPT Expense",

    'depends': ['base', 'hr_expense', 'dpt_shipping', 'purchase', 'dpt_purchase_management'],

    'data': [
        'security/ir.model.access.csv',
        'views/account_move.xml',
        'views/dpt_expense_allocation.xml',
        'views/purchase_order.xml',
        'views/uom_uom.xml',
    ],
}


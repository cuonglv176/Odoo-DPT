# -*- coding: utf-8 -*-
{
    'name': "DPT Expense",

    'depends': ['base', 'hr_expense', 'dpt_shipping'],

    'data': [
        'security/ir.model.access.csv',
        'views/account_move.xml',
        'views/dpt_expense_allocation.xml',
        'views/uom_uom.xml',
    ],
}


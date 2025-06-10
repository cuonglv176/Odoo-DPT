# -*- coding: utf-8 -*-
{
    'name': "DPT Expense",

    'depends': ['base', 'account', 'hr_expense', 'dpt_shipping', 'purchase', 'dpt_purchase_management', 'dpt_service_management'],

    'data': [
        'security/ir.model.access.csv',
        'views/account_move.xml',
        'views/dpt_expense_allocation.xml',
        'views/dpt_service_combo.xml',
        'views/dpt_service_management.xml',
        'views/purchase_order.xml',
        'views/uom_uom.xml',
        'wizards/dpt_create_account_expense_wizard.xml',
    ],
}

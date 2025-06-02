# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class DPTCreateAccountExpenseWizard(models.TransientModel):
    _name = 'dpt.create.account.expense.wizard'
    _description = 'Wizard Tạo hóa đơn'

    po_id = fields.Many2one('purchase.order', string='Đơn mua', required=True)
    type = fields.Selection([
        ('expense_allocation', 'Phân bổ chi phí'),
        ('expense_invoice', 'Hóa đơn'),
    ], "Tạo hóa đơn hay phân bổ chi phí?", required=True, default='expense_allocation')

    def action_confirm(self):
        if self.type == 'expense_allocation':
            self.po_id.action_allocate()
        if self.type == 'expense_invoice':
            self.po_id.action_create_invoice()

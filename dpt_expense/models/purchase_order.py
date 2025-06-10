# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    shipping_slip_ids = fields.Many2many('dpt.shipping.slip', string="Phiếu vận chuyển")
    order_expense_ids = fields.Many2many('sale.order', 'purchase_order_expense_rel', 'purchase_id', 'sale_id',
                                         string="Đơn hàng chi phí")
    total_order_expense_ids = fields.Many2many('sale.order', string="Tât cả đơn hàng tính chi phí", store=False,
                                               compute="_compute_order_expense")
    expense_allocation_count = fields.Integer('Số lượng phiếu phân bổ',
                                              compute="_compute_expense_allocation_information")

    @api.depends('shipping_slip_ids', 'order_expense_ids')
    def _compute_order_expense(self):
        for item in self:
            item.total_order_expense_ids = item.shipping_slip_ids.mapped('sale_ids') | item.order_expense_ids

    def _compute_expense_allocation_information(self):
        for item in self:
            item.expense_allocation_count = self.env['dpt.expense.allocation'].search_count(
                [('purchase_order_ids', 'in', item.ids)])

    def action_view_expense_allocation(self):
        action = self.env.ref('dpt_expense.dpt_expense_allocation_action').sudo().read()[0]
        action['domain'] = [('purchase_order_ids', 'in', self.ids)]
        action['context'] = {'create': False, 'delete': False}
        return action

    def action_view_expense_account_move(self):
        action = self.env.ref('account.action_move_in_invoice_type').sudo().read()[0]
        all_expense_allocation_ids = self.env['dpt.expense.allocation'].search([('purchase_order_ids', 'in', self.ids)])
        action['domain'] = [('id', 'in', all_expense_allocation_ids.mapped('allocation_move_ids').ids)]
        return action

    def action_create_expense_allocation(self):
        expense_allocation = self.env['dpt.expense.allocation'].create({
            'purchase_order_ids': [(6, 0, self.ids)],
            'name': f'Phân bổ chi phí đơn mua {self.name}'
        })
        expense_allocation._onchange_get_expense()
        action = self.env.ref('dpt_expense.dpt_expense_allocation_action').sudo().read()[0]
        action['res_id'] = expense_allocation.id
        action['view_mode'] = 'form'
        return action

    def action_popup_create_account_move(self):
        return {
            'name': _('Tạo hóa đơn / phân bổ'),
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.create.account.expense.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_po_id': self.id},
        }

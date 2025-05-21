# -*- coding: utf-8 -*-
import logging
from odoo.exceptions import ValidationError
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class DPTExpenseAllocation(models.Model):
    _name = 'dpt.expense.allocation'
    _description = 'DPT Expense Allocation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char("Name", reuqired=1)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    main_currency_id = fields.Many2one('res.currency', string='Main Currency', compute="_compute_main_currency")
    expense_id = fields.Many2one('product.product', string='Expense')
    total_expense = fields.Monetary(string='Total Expense', currency_field='currency_id')
    total_expense_in_main_currency = fields.Monetary(string='Total Expense In Main Currency',
                                                  currency_field='main_currency_id')
    shipping_id = fields.Many2one('dpt.shipping.slip', string='Shipping')
    sale_ids = fields.Many2many('sale.order', string='Orders', compute="_compute_order")
    state = fields.Selection([('draft', 'Draft'), ('allocated', 'Allocated')], string='State', default='draft')

    @api.depends('shipping_id')
    def _compute_order(self):
        for item in self:
            item.sale_ids = item.shipping_id.sale_ids

    @api.depends('shipping_id')
    def _compute_main_currency(self):
        for item in self:
            item.main_currency_id = self.env.company.currency_id

    @api.onchange('shipping_id')
    def _onchange_get_expense(self):
        if not self.shipping_id or not self.shipping_id.po_id:
            return
        self.currency_id = self.shipping_id.po_id.currency_id if self.shipping_id.po_id.currency_id else self.env.company.currency_id
        self.total_expense = self.shipping_id.po_id.amount_total

    def action_allocate(self):
        self.state = 'allocated'
        total_revenue = 0
        revenue_group_by_uom = {}
        quantity_group_by_uom = {}
        uom_by_order = {}
        for sale_id in self.sale_ids:
            uom_quantity = {}
            for sale_service_id in sale_id.sale_service_ids:
                if not sale_service_id.compute_uom_id or (
                        sale_service_id.compute_uom_id and not sale_service_id.compute_uom_id.use_for_allocate_expense):
                    continue
                total_revenue += sale_service_id.amount_total
                if revenue_group_by_uom.get(sale_service_id.compute_uom_id):
                    revenue_group_by_uom[sale_service_id.compute_uom_id] = revenue_group_by_uom[
                                                                               sale_service_id.compute_uom_id] + sale_service_id.amount_total
                else:
                    revenue_group_by_uom[sale_service_id.compute_uom_id] = sale_service_id.amount_total
                if quantity_group_by_uom.get(sale_service_id.compute_uom_id):
                    quantity_group_by_uom[sale_service_id.compute_uom_id] = quantity_group_by_uom[
                                                                                sale_service_id.compute_uom_id] + sale_service_id.quantity
                else:
                    quantity_group_by_uom[sale_service_id.compute_uom_id] = sale_service_id.quantity
                if uom_quantity.get(sale_service_id.compute_uom_id):
                    uom_quantity[sale_service_id.compute_uom_id] = uom_quantity[
                                                                       sale_service_id.compute_uom_id] + sale_service_id.compute_value
                else:
                    uom_quantity[sale_service_id.compute_uom_id] = sale_service_id.compute_value
            if uom_quantity:
                uom_by_order.update({
                    sale_id: uom_quantity
                })
        # xử lý phân bổ
        if revenue_group_by_uom:
            expense_group_by_uom = {}
            for uom_id, revenue in revenue_group_by_uom.items():
                expense_group_by_uom[uom_id] = self.total_expense_in_main_currency / total_revenue * revenue
            if uom_by_order:
                expense_by_order = {}
                for sale_id, order_uom_quantity in uom_by_order.items():
                    expense = 0
                    for uom_id, uom_quantity in order_uom_quantity.items():
                        expense += uom_quantity * expense_group_by_uom.get(uom_id, 0) / quantity_group_by_uom.get(
                            uom_id)
                    expense_by_order[sale_id] = expense
                if expense_by_order:
                    journal_id = self.env['account.journal'].sudo().search([('type','=','purchase')], limit=1)
                    if not journal_id:
                        raise ValidationError("Vui lòng cấu hình sổ nhật ký mua hàng!!")
                    for sale_id, expense in expense_by_order.items():
                        move_id = self.env['account.move'].sudo().create({
                            'partner_id': self.shipping_id.po_id.partner_id.id,
                            'sale_id': sale_id.id,
                            'journal_id': journal_id.id,
                            'invoice_line_ids': [(0, 0, {
                                'product_id': self.expense_id.id,
                                'account_id': self.expense_id.property_account_expense_id.id,
                                'quantity': 1,
                                'price_unit': expense
                            })]
                        })
                        move_id.action_post()

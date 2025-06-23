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
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', default=lambda self: self.env.company.currency_id)
    main_currency_id = fields.Many2one('res.currency', string='Tiền tệ chính', compute="_compute_main_expense")
    total_expense = fields.Monetary(string='Giá trị phân bổ', currency_field='currency_id', compute="compute_total_expense", store=False)
    purchase_order_ids = fields.Many2many('purchase.order', string='Đơn mua hàng')
    shipping_ids = fields.Many2many('dpt.shipping.slip', string='PVC', compute="_compute_order_shipping")
    sale_ids = fields.Many2many('sale.order', string='Đơn bán hàng', compute="_compute_order_shipping")
    state = fields.Selection([('draft', 'Draft'), ('allocated', 'Allocated')], string='Trạng thái', default='draft')
    allocation_move_ids = fields.One2many('account.move', 'expense_allocation_id', string='Hóa đơn phân bổ')
    allocation_move_count = fields.Integer(string='Allocation Moves Count', compute="_compute_allocation_move_count")

    def _compute_allocation_move_count(self):
        for item in self:
            item.allocation_move_count = len(item.allocation_move_ids)

    @api.depends('purchase_order_ids')
    def _compute_order_shipping(self):
        for item in self:
            item.sale_ids = item.purchase_order_ids.mapped('total_order_expense_ids')
            item.shipping_ids = item.purchase_order_ids.mapped('shipping_slip_ids')

    # @api.depends('purchase_order_ids', 'total_expense')
    def _compute_main_expense(self):
        for item in self:
            item.main_currency_id = self.env.company.currency_id

    @api.onchange('purchase_order_ids')
    def _onchange_get_expense(self):
        if not self.purchase_order_ids:
            return
        self.currency_id = self.purchase_order_ids[0].currency_id if self.purchase_order_ids[
            0].currency_id else self.env.company.currency_id

    @api.depends('purchase_order_ids')
    def compute_total_expense(self):
        if not self.purchase_order_ids:
            return
        self.total_expense = sum(self.purchase_order_ids.mapped('order_line.price_subtotal3'))

    def action_allocate(self):
        self.state = 'allocated'
        total_revenue = 0
        revenue_group_by_uom = {}
        quantity_group_by_uom = {}
        uom_by_order = {}
        journal_id = self.env['account.journal'].sudo().search([('type', '=', 'purchase')], limit=1)
        if not journal_id:
            raise ValidationError("Vui lòng cấu hình sổ nhật ký mua hàng!!")
        # combine sale with revenue
        for sale_id in self.sale_ids:
            uom_quantity = {}
            # dịch vụ
            for sale_service_id in sale_id.sale_service_ids:
                if sale_service_id.combo_id or not sale_service_id.compute_uom_id or (
                        sale_service_id.compute_uom_id and not sale_service_id.compute_uom_id.use_for_allocate_expense) or sale_service_id.service_id or (
                        sale_service_id.service_id and not sale_service_id.service_id.use_for_allocate_expense):
                    continue
                total_revenue += sale_service_id.amount_total
                if revenue_group_by_uom.get(sale_service_id.compute_uom_id):
                    revenue_group_by_uom[sale_service_id.compute_uom_id] = revenue_group_by_uom[
                                                                               sale_service_id.compute_uom_id] + sale_service_id.amount_total
                else:
                    revenue_group_by_uom[sale_service_id.compute_uom_id] = sale_service_id.amount_total
                if quantity_group_by_uom.get(sale_service_id.compute_uom_id):
                    quantity_group_by_uom[sale_service_id.compute_uom_id] = quantity_group_by_uom[
                                                                                sale_service_id.compute_uom_id] + sale_service_id.compute_value
                else:
                    quantity_group_by_uom[sale_service_id.compute_uom_id] = sale_service_id.compute_value
                if uom_quantity.get(sale_service_id.compute_uom_id):
                    uom_quantity[sale_service_id.compute_uom_id] = uom_quantity[
                                                                       sale_service_id.compute_uom_id] + sale_service_id.compute_value
                else:
                    uom_quantity[sale_service_id.compute_uom_id] = sale_service_id.compute_value

            # combo
            for service_combo_id in sale_id.service_combo_ids:
                if not service_combo_id.compute_uom_id or (
                        service_combo_id.compute_uom_id and not service_combo_id.compute_uom_id.use_for_allocate_expense) or not service_combo_id.combo_id or (
                        service_combo_id.combo_id and not service_combo_id.combo_id.use_for_allocate_expense):
                    continue
                total_revenue += service_combo_id.amount_total
                if revenue_group_by_uom.get(service_combo_id.compute_uom_id):
                    revenue_group_by_uom[service_combo_id.compute_uom_id] = revenue_group_by_uom[
                                                                                service_combo_id.compute_uom_id] + service_combo_id.amount_total
                else:
                    revenue_group_by_uom[service_combo_id.compute_uom_id] = service_combo_id.amount_total
                if quantity_group_by_uom.get(service_combo_id.compute_uom_id):
                    quantity_group_by_uom[service_combo_id.compute_uom_id] = quantity_group_by_uom[
                                                                                 service_combo_id.compute_uom_id] + service_combo_id.compute_value
                else:
                    quantity_group_by_uom[service_combo_id.compute_uom_id] = service_combo_id.compute_value
                if uom_quantity.get(service_combo_id.compute_uom_id):
                    uom_quantity[service_combo_id.compute_uom_id] = uom_quantity[
                                                                        service_combo_id.compute_uom_id] + service_combo_id.compute_value
                else:
                    uom_quantity[service_combo_id.compute_uom_id] = service_combo_id.compute_value

            if uom_quantity:
                uom_by_order.update({
                    sale_id: uom_quantity
                })
        # combine expense with value
        expense_by_value = {}
        for po_id in self.purchase_order_ids:
            for order_line in po_id.order_line:
                if not order_line.product_id.can_be_expensed:
                    continue
                key = f"{order_line.product_id.id}-{order_line.order_id.partner_id.id}"
                if expense_by_value.get(key):
                    expense_by_value[key] = expense_by_value[key] + order_line.price_subtotal3
                else:
                    expense_by_value[key] = order_line.price_subtotal3

        if not expense_by_value:
            raise ValidationError("Không có chi phí nào để phân bổ!!")
        _logger.info('uom_by_order: %s' % uom_by_order)
        _logger.info('revenue_group_by_uom: %s' % revenue_group_by_uom)
        _logger.info('quantity_group_by_uom: %s' % quantity_group_by_uom)
        _logger.info('expense_by_value: %s' % expense_by_value)
        move_line_vals = []
        for partner_expense, total_expense in expense_by_value.items():
            expense_allocated = 0
            expense_id = self.env['product.product'].sudo().browse(int(partner_expense.split('-')[0]))
            partner_id = self.env['res.partner'].sudo().browse(int(partner_expense.split('-')[1]))
            # xử lý phân bổ
            if revenue_group_by_uom:
                expense_group_by_uom = {}
                for uom_id, revenue in revenue_group_by_uom.items():
                    expense_group_by_uom[uom_id] = round(total_expense / total_revenue * revenue, 2)
                if uom_by_order:
                    expense_by_order = {}
                    index = 1
                    for sale_id, order_uom_quantity in uom_by_order.items():
                        if index != len(uom_by_order):
                            expense = 0
                            for uom_id, uom_quantity in order_uom_quantity.items():
                                expense += round((uom_quantity * expense_group_by_uom.get(uom_id,
                                                                                          0) / quantity_group_by_uom.get(
                                    uom_id)), 0)
                            expense_allocated += expense
                        else:
                            expense = total_expense - expense_allocated
                        expense_by_order[sale_id] = expense
                        index += 1
                    _logger.info('expense_by_order: %s' % expense_by_order)
                    if expense_by_order:
                        for sale_id, expense in expense_by_order.items():
                            move_line_vals.append((0, 0, {
                                'journal_id': journal_id.id,
                                'product_id': expense_id.id,
                                'sale_order_id': sale_id.id,
                                'account_id': expense_id.property_account_expense_id.id,
                                'display_type': 'product',
                                'price_unit': expense,
                                'debit': expense,
                                'balance': expense,
                                'quantity': 1,
                                # 'expense_id': expense_id.id,
                            }))

                move_line_vals.append((0, 0, {
                    'partner_id': partner_id.id,
                    'journal_id': journal_id.id,
                    'account_id': partner_id.property_account_payable_id.id if partner_id.property_account_payable_id else None,
                    'display_type': 'payment_term',
                    'credit': total_expense,
                    'balance': -total_expense,
                    # 'expense_id': expense_id.id,
                }))
        move_id = self.env['account.move'].sudo().create({
            'journal_id': journal_id.id,
            'expense_allocation_id': self.id,
            'line_ids': move_line_vals
        })
        move_id.action_post()

    def action_view_invoice(self):
        action = self.env.ref('account.action_move_in_invoice_type').sudo().read()[0]
        action['domain'] = [('expense_allocation_id', '=', self.id)]
        return action

# -*- coding: utf-8 -*-

from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.fields import Command
from odoo.addons.sale.models.sale_order import SaleOrder
from odoo.tools import float_is_zero, format_amount, format_date, html_keep_url, is_html_empty


def _create_invoices(self, grouped=False, final=False, date=None):
    """ Create invoice(s) for the given Sales Order(s).

    :param bool grouped: if True, invoices are grouped by SO id.
        If False, invoices are grouped by keys returned by :meth:`_get_invoice_grouping_keys`
    :param bool final: if True, refunds will be generated if necessary
    :param date: unused parameter
    :returns: created invoices
    :rtype: `account.move` recordset
    :raises: UserError if one of the orders has no invoiceable lines.
    """
    if not self.env['account.move'].check_access_rights('create', False):
        try:
            self.check_access_rights('write')
            self.check_access_rule('write')
        except AccessError:
            return self.env['account.move']

    product_buy_id = self.env['product.product'].sudo().search([('is_product_buy', '=', True)], limit=1)
    if not product_buy_id:
        raise ValidationError(_("No product buy found."))

    product_deposit_id = self.env['product.product'].sudo().search([('is_product_deposit', '=', True)], limit=1)
    if not product_deposit_id:
        raise ValidationError(_("No product deposit found."))

    # 1) Create invoices.
    invoice_vals_list = []
    invoice_item_sequence = 0  # Incremental sequencing to keep the lines order on the invoice.
    for order in self:
        if order.type_so_route == 'office_route':
            import_ids = self.env['dpt.export.import'].search(
                [('sale_ids', 'in', order.ids),
                 ('state', 'not in', ('cleared', 'back_for_stock', 'released', 'cancelled'))])
            if import_ids:
                import_name = ','.join(import_ids.mapped('name'))
                raise UserError(f"Tờ khai: {import_name} chưa được thông quan, vui lòng kiểm tra lại!!!")
            import_not_ids = self.env['dpt.export.import'].search(
                [('sale_ids', 'in', order.ids)])
            # if not import_not_ids:
            #     raise UserError(f"Không có tờ khai: vui lòng kiểm tra lại!!!")

            vehicle_stage_ids = self.env['dpt.vehicle.stage'].search([('is_finish_stage', '=', True)])
            shipping_ids = self.env['dpt.shipping.slip'].search(
                [('vn_vehicle_stage_id', 'in', vehicle_stage_ids.ids), ('export_import_ids.sale_ids', 'in', order.ids)])
            shipping_tq_ids = self.env['dpt.shipping.slip'].search(
                [('cn_vehicle_stage_id', 'in', vehicle_stage_ids.ids), ('export_import_ids.sale_ids', 'in', order.ids)])
            shipping_last_vn_ids = self.env['dpt.shipping.slip'].search(
                [('last_vn_vehicle_stage_id', 'in', vehicle_stage_ids.ids), ('export_import_ids.sale_ids', 'in', order.ids)])
            if not shipping_ids and not shipping_tq_ids and not shipping_last_vn_ids:
                raise UserError(f"Vận chuyển chưa được hoàn thành, vui lòng kiểm tra lại!!!")

        # picking_ids = self.env['stock.picking'].search(
        #     ['|', ('sale_purchase_id', '=', self.id), ('sale_id', '=', order.id),
        #      ('state', 'not in', ('confirmed','done', 'cancel'))])
        # if picking_ids:
        #     picking_name = ','.join(picking_ids.mapped('name'))
        #     raise UserError(f"Vận chuyển : {picking_name} chưa được hoàn thành, vui lòng kiểm tra lại!!!")
        #
        # picking_lot_name_ids = self.env['stock.picking'].search(
        #     ['|', ('sale_purchase_id', '=', order.id), ('sale_id', '=', order.id),
        #      ('state', '!=', 'cancel'), ('picking_lot_name', '=', False)])
        # if picking_lot_name_ids:
        #     picking_lot_name = ','.join(picking_lot_name_ids.mapped('name'))
        #     raise UserError(f"Vận chuyển : {picking_lot_name} chưa được cập nhật mã lô, vui lòng kiểm tra lại!!!")
        # picking_not_ids = self.env['stock.picking'].search(
        #     ['|', ('sale_purchase_id', '=', self.id), ('sale_id', '=', order.id)])
        # if not picking_not_ids:
        #     raise UserError(f"Không có Vận chuyển: vui lòng kiểm tra lại!!!")

        order = order.with_company(order.company_id).with_context(lang=order.partner_invoice_id.lang)

        invoice_vals = order._prepare_invoice()
        # invoiceable_lines = order._get_invoiceable_lines(final)

        # DEPOSIT
        invoice_line_vals = []
        deposit = 0
        for deposit_id in self.deposit_ids:
            if deposit_id.state == 'posted':
                deposit += deposit_id.amount
        if deposit > 0:
            invoice_line_vals.append(Command.create(
                {
                    'product_id': product_deposit_id.id,
                    'display_type': 'product',
                    'quantity': 1,
                    'price_unit': 0 - deposit
                }))

        if order.purchase_amount_total != 0:
            invoice_line_vals.append(Command.create(
                {
                    'product_id': product_buy_id.id,
                    'order_line_ids': order.order_line.ids,
                    'display_type': 'product',
                    'quantity': 1,
                    # 'price_unit': sum(order.order_line.mapped('price_subtotal')),
                    'price_unit': order.purchase_amount_total
                }))

        if order.settle_by == 'planned':
            if order.planned_sale_service_ids:
                for sale_service_id in order.sale_service_ids:
                    if sale_service_id.price != 0:
                        if not sale_service_id.service_id.product_id:
                            product_vals = {
                                'name': sale_service_id.service_id.name,
                                'type': 'service',
                                'invoice_policy': 'order',
                                'sale_ok': True,
                                'purchase_ok': False,
                                'list_price': sale_service_id.price,
                                'default_code': sale_service_id.service_id.code or f"SERV-{sale_service_id.service_id.id}",
                                'taxes_id': [(6, 0,
                                              sale_service_id.service_id.tax_ids.ids)] if sale_service_id.service_id.tax_ids else False,
                            }
                            new_product = self.env['product.product'].sudo().create(product_vals)
                            sale_service_id.service_id.sudo().write({'product_id': new_product.id})
                        line_vals = {
                            'product_id': sale_service_id.service_id.product_id.id,
                            'display_type': 'product',
                            'quantity': sale_service_id.compute_value,
                            'price_unit': sale_service_id.price,
                            'service_line_ids': [(6, 0, sale_service_id.ids)],
                        }
                        invoice_line_vals.append(Command.create(line_vals))
            if order.planned_service_combo_ids:
                for planned_service_combo_id in order.planned_service_combo_ids:
                    if planned_service_combo_id.price != 0:
                        if not planned_service_combo_id.combo_id.product_id:
                            product_vals = {
                                'name': planned_service_combo_id.combo_id.name,
                                'type': 'service',
                                'invoice_policy': 'order',
                                'sale_ok': True,
                                'purchase_ok': False,
                                'list_price': planned_service_combo_id.price,
                                'default_code': planned_service_combo_id.combo_id.code or f"COMBO-{planned_service_combo_id.combo_id.id}",
                                'property_account_expense_id':  planned_service_combo_id.combo_id.expense_account_id.id,
                                'property_account_income_id':  planned_service_combo_id.combo_id.revenue_account_id.id,
                            }
                            new_product = self.env['product.product'].sudo().create(product_vals)
                            planned_service_combo_id.combo_id.sudo().write({'product_id': new_product.id})
                        line_vals = {
                            'product_id': planned_service_combo_id.combo_id.product_id.id,
                            'display_type': 'product',
                            'quantity': planned_service_combo_id.qty,
                            'price_unit': planned_service_combo_id.price,
                        }
                        invoice_line_vals.append(Command.create(line_vals))

        if order.settle_by == 'actual':
            if order.sale_service_ids:
                for sale_service_id in order.sale_service_ids:
                    if sale_service_id.price != 0:
                        # Kiểm tra nếu dịch vụ không có sản phẩm liên kết
                        if not sale_service_id.service_id.product_id:
                            # Tạo sản phẩm mới từ thông tin dịch vụ
                            product_vals = {
                                'name': sale_service_id.service_id.name,
                                'type': 'service',
                                'invoice_policy': 'order',
                                'sale_ok': True,
                                'purchase_ok': False,
                                'list_price': sale_service_id.price,
                                'default_code': sale_service_id.service_id.code or f"SERV-{sale_service_id.service_id.id}",
                                'property_account_expense_id': sale_service_id.service_id.expense_account_id.id,
                                'property_account_income_id': sale_service_id.service_id.revenue_account_id.id,
                            }
                            new_product = self.env['product.product'].sudo().create(product_vals)
                            sale_service_id.service_id.sudo().write({'product_id': new_product.id})
                        line_vals = {
                            'product_id': sale_service_id.service_id.product_id.id,
                            'display_type': 'product',
                            'quantity': sale_service_id.compute_value,
                            'price_unit': sale_service_id.price,
                            'service_line_ids': [(6, 0, sale_service_id.ids)],
                        }
                        invoice_line_vals.append(Command.create(line_vals))
            if order.service_combo_ids:
                for service_combo_id in order.service_combo_ids:
                    if service_combo_id.price != 0:
                        if not service_combo_id.combo_id.product_id:
                            product_vals = {
                                'name': service_combo_id.combo_id.name,
                                'type': 'service',
                                'invoice_policy': 'order',
                                'sale_ok': True,
                                'purchase_ok': False,
                                'list_price': service_combo_id.price,
                                'default_code': service_combo_id.combo_id.code or f"COMBO-{planned_service_combo_id.combo_id.id}",
                                'property_account_expense_id':  service_combo_id.combo_id.expense_account_id.id,
                                'property_account_income_id':  service_combo_id.combo_id.revenue_account_id.id,
                            }
                            new_product = self.env['product.product'].sudo().create(product_vals)
                            service_combo_id.combo_id.sudo().write({'product_id': new_product.id})
                        line_vals = {
                            'product_id': service_combo_id.combo_id.product_id.id,
                            'display_type': 'product',
                            'quantity': service_combo_id.qty,
                            'price_unit': service_combo_id.price,
                        }
                        invoice_line_vals.append(Command.create(line_vals))

        # if not any(not line.display_type for line in invoiceable_lines):
        #     invoice_vals_list.append(invoice_vals)
        #     continue

        down_payment_section_added = False
        # for line in invoiceable_lines:
        # if not down_payment_section_added and line.is_downpayment:
        #     # Create a dedicated section for the down payments
        #     # (put at the end of the invoiceable_lines)
        #     invoice_line_vals.append(
        #         Command.create(
        #             order._prepare_down_payment_section_line(sequence=invoice_item_sequence)
        #         ),
        #     )
        #     down_payment_section_added = True
        #     invoice_item_sequence += 1
        # invoice_line_vals.append(
        #     Command.create(
        #         line._prepare_invoice_line(sequence=invoice_item_sequence)
        #     ),
        # )
        # invoice_item_sequence += 1

        invoice_vals['invoice_line_ids'] += invoice_line_vals
        invoice_vals_list.append(invoice_vals)

    if not invoice_vals_list and self._context.get('raise_if_nothing_to_invoice', True):
        raise UserError(self._nothing_to_invoice_error_message())

    # 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
    if not grouped:
        new_invoice_vals_list = []
        invoice_grouping_keys = self._get_invoice_grouping_keys()
        invoice_vals_list = sorted(
            invoice_vals_list,
            key=lambda x: [
                x.get(grouping_key) for grouping_key in invoice_grouping_keys
            ]
        )
        for _grouping_keys, invoices in groupby(invoice_vals_list,
                                                key=lambda x: [x.get(grouping_key) for grouping_key in
                                                               invoice_grouping_keys]):
            origins = set()
            payment_refs = set()
            refs = set()
            ref_invoice_vals = None
            for invoice_vals in invoices:
                if not ref_invoice_vals:
                    ref_invoice_vals = invoice_vals
                else:
                    ref_invoice_vals['invoice_line_ids'] += invoice_vals['invoice_line_ids']
                origins.add(invoice_vals['invoice_origin'])
                payment_refs.add(invoice_vals['payment_reference'])
                refs.add(invoice_vals['ref'])
            ref_invoice_vals.update({
                'ref': ', '.join(refs)[:2000],
                'invoice_origin': ', '.join(origins),
                'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
            })
            new_invoice_vals_list.append(ref_invoice_vals)
        invoice_vals_list = new_invoice_vals_list

    # 3) Create invoices.

    # As part of the invoice creation, we make sure the sequence of multiple SO do not interfere
    # in a single invoice. Example:
    # SO 1:
    # - Section A (sequence: 10)
    # - Product A (sequence: 11)
    # SO 2:
    # - Section B (sequence: 10)
    # - Product B (sequence: 11)
    #
    # If SO 1 & 2 are grouped in the same invoice, the result will be:
    # - Section A (sequence: 10)
    # - Section B (sequence: 10)
    # - Product A (sequence: 11)
    # - Product B (sequence: 11)
    #
    # Resequencing should be safe, however we resequence only if there are less invoices than
    # orders, meaning a grouping might have been done. This could also mean that only a part
    # of the selected SO are invoiceable, but resequencing in this case shouldn't be an issue.
    if len(invoice_vals_list) < len(self):
        SaleOrderLine = self.env['sale.order.line']
        for invoice in invoice_vals_list:
            sequence = 1
            for line in invoice['invoice_line_ids']:
                line[2]['sequence'] = SaleOrderLine._get_invoice_line_sequence(new=sequence, old=line[2]['sequence'])
                sequence += 1

    # Manage the creation of invoices in sudo because a salesperson must be able to generate an invoice from a
    # sale order without "billing" access rights. However, he should not be able to create an invoice from scratch.
    moves = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals_list)

    # 4) Some moves might actually be refunds: convert them if the total amount is negative
    # We do this after the moves have been created since we need taxes, etc. to know if the total
    # is actually negative or not
    if final:
        moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_move_type()
    for move in moves:
        if final:
            # Downpayment might have been determined by a fixed amount set by the user.
            # This amount is tax included. This can lead to rounding issues.
            # E.g. a user wants a 100€ DP on a product with 21% tax.
            # 100 / 1.21 = 82.64, 82.64 * 1,21 = 99.99
            # This is already corrected by adding/removing the missing cents on the DP invoice,
            # but must also be accounted for on the final invoice.

            delta_amount = 0
            for order_line in self.order_line:
                if not order_line.is_downpayment:
                    continue
                inv_amt = order_amt = 0
                for invoice_line in order_line.invoice_lines:
                    sign = 1 if invoice_line.move_id.is_inbound() else -1
                    if invoice_line.move_id == move:
                        inv_amt += invoice_line.price_total * sign
                    elif invoice_line.move_id.state != 'cancel':  # filter out canceled dp lines
                        order_amt += invoice_line.price_total * sign
                if inv_amt and order_amt:
                    # if not inv_amt, this order line is not related to current move
                    # if no order_amt, dp order line was not invoiced
                    delta_amount += inv_amt + order_amt

            if not move.currency_id.is_zero(delta_amount):
                receivable_line = move.line_ids.filtered(
                    lambda aml: aml.account_id.account_type == 'asset_receivable')[:1]
                product_lines = move.line_ids.filtered(
                    lambda aml: aml.display_type == 'product' and aml.is_downpayment)
                tax_lines = move.line_ids.filtered(
                    lambda aml: aml.tax_line_id.amount_type not in (False, 'fixed'))
                if tax_lines and product_lines and receivable_line:
                    line_commands = [Command.update(receivable_line.id, {
                        'amount_currency': receivable_line.amount_currency + delta_amount,
                    })]
                    delta_sign = 1 if delta_amount > 0 else -1
                    for lines, attr, sign in (
                            (product_lines, 'price_total', -1 if move.is_inbound() else 1),
                            (tax_lines, 'amount_currency', 1),
                    ):
                        remaining = delta_amount
                        lines_len = len(lines)
                        for line in lines:
                            if move.currency_id.compare_amounts(remaining, 0) != delta_sign:
                                break
                            amt = delta_sign * max(
                                move.currency_id.rounding,
                                abs(move.currency_id.round(remaining / lines_len)),
                            )
                            remaining -= amt
                            line_commands.append(Command.update(line.id, {attr: line[attr] + amt * sign}))
                    move.line_ids = line_commands

        move.message_post_with_source(
            'mail.message_origin_link',
            render_values={'self': move, 'origin': move.line_ids.sale_line_ids.order_id},
            subtype_xmlid='mail.mt_note',
        )
    return moves


SaleOrder._create_invoices = _create_invoices


class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    # def action_register_payment(self):
    #     if not self.invoice_ids:
    #         payment_inv_id = self.env['sale.advance.payment.inv'].create({
    #             'advance_payment_method': 'delivered',
    #         })
    #         payment_inv_id._create_invoices(self)
    #     draft_invoice_id = self.invoice_ids.filtered(lambda invoice: invoice.state == 'draft')
    #     # đối soát
    #     action = self.invoice_ids.action_register_payment()
    #     return action
    def create_invoice(self):
        res = super(SaleOrder, self).create_invoice()
        deposit = 0
        for deposit_id in self.deposit_ids:
            if deposit_id.state == 'posted':
                deposit += deposit_id.amount
        return res

    @api.depends('order_line.invoice_lines', 'sale_service_ids')
    def _get_invoiced(self):
        # The invoice_ids are obtained thanks to the invoice lines of the SO
        # lines, and we also search for possible refunds created directly from
        # existing invoices. This is necessary since such a refund is not
        # directly linked to the SO.k
        for order in self:
            order_invoices = order.order_line.invoice_lines.move_id.filtered(
                lambda r: r.move_type in ('out_invoice', 'out_refund'))
            service_invoices = self.env['account.move.line'].sudo().search(
                [('service_line_ids', 'in', order.sale_service_ids.ids)]).mapped('move_id').filtered(
                lambda r: r.move_type in ('out_invoice', 'out_refund'))
            order.invoice_ids = order_invoices | service_invoices
            order.invoice_count = len(order_invoices | service_invoices)

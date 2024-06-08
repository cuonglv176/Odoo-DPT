from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    approval_ids = fields.One2many('approval.request', 'sale_id', string='Change Price Approval')
    approval_count = fields.Integer(string='Approval count', compute="_compute_approval_count")
    price_status = fields.Selection([
        ('no_price', 'No Price'),
        ('wait_approve', 'Wait Approve'),
        ('approved', 'Approved'),
    ], string='Status', default='no_price', compute="_compute_price_status")

    @api.depends('approval_ids')
    def _compute_price_status(self):
        for rec in self:
            if rec.approval_ids:
                not_approved = rec.approval_ids.filtered(lambda approval: approval.request_status != 'approved')
                if not_approved:
                    price_status = 'wait_approve'
                else:
                    price_status = 'approved'
            else:
                price_status = 'no_price'
            rec.price_status = price_status

    def action_open_change_price_approval(self):
        view_id = self.env.ref('approvals.approval_request_view_kanban').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'approval.request',
            'name': _('Approval request'),
            'view_mode': 'kanban,tree,form',
            'domain': [('sale_id', '=', self.id)],
            'views': [[view_id, 'kanban']],
        }

    @api.depends('approval_ids')
    def _compute_approval_count(self):
        for rec in self:
            rec.approval_count = len(rec.approval_ids)

    def action_change_price(self):
        view_id = self.env.ref('dpt_sale_approvals.view_sale_change_price_form').id
        for sale_service_id in self.sale_service_ids:
            sale_service_id.new_price = sale_service_id.price
        for line in self.order_line:
            line.new_price_unit = line.price_unit
        return {
            'name': "Change Price",
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'target': 'new',
            'res_id': self.id,
            'views': [[view_id, 'form']],
        }

    def send_change_price_request(self):
        category_id = self.env['approval.category'].search([('sequence_code', '=', 'BAOGIA')])
        if not category_id:
            raise ValidationError(_("Please config category approval change price (BAOGIA)"))
        approval_id = self.env['approval.request'].create({
            'request_owner_id': self.env.user.id,
            'category_id': category_id.id,
            'sale_id': self.id,
            'date': datetime.now(),
        })
        for sale_service_id in self.sale_service_ids:
            if sale_service_id.new_price != 0 and sale_service_id.new_price != sale_service_id.price:
                sale_service_id.approval_id = approval_id
        for line in self.order_line:
            if line.new_price_unit != 0 and line.new_price_unit != line.price_unit:
                line.approval_id = approval_id
        view_id = self.env.ref('approvals.approval_request_view_form').id
        approval_id.action_confirm()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'approval.request',
            'name': _('Approval request'),
            'view_mode': 'form',
            'res_id': approval_id.id,
            'views': [[view_id, 'form']],
        }


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    new_price_unit = fields.Monetary(currency_field='currency_id', string='New Price Unit')
    new_price_subtotal = fields.Monetary(currency_field='currency_id', string="New Price Subtotal",
                                         compute="_compute_new_price_subtotal")
    approval_id = fields.Many2one('approval.request', string='Approval Change Price')
    price_status = fields.Selection([
        ('no_price', 'No Price'),
        ('wait_approve', 'Wait Approve'),
        ('approved', 'Approved'),
    ], string='Status', default='no_price', compute="_compute_price_status")

    @api.depends('approval_id')
    def _compute_price_status(self):
        for rec in self:
            if rec.approval_id:
                not_approved = rec.approval_id.filtered(lambda approval: approval.request_status != 'approved')
                if not_approved:
                    price_status = 'wait_approve'
                else:
                    price_status = 'approved'
            else:
                price_status = 'no_price'
            rec.price_status = price_status

    @api.depends('product_uom_qty', 'new_price_unit')
    def _compute_new_price_subtotal(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            amount_untaxed = line.product_uom_qty * line.new_price_unit
            line.update({
                'new_price_subtotal': amount_untaxed,
            })

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    payment_ids = fields.One2many('account.payment', 'purchase_id', string='Payment')
    payment_count = fields.Integer(string='Payment count', compute="_compute_payment_count")
    payment_amount_total = fields.Float(string='Payment Amount', compute="_compute_payment_count")

    def action_open_payment_popup(self):
        view_form_id = self.env.ref('dpt_account_payment_request.dpt_view_account_payment_request_form').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'name': _('Payment'),
            'view_mode': 'form',
            'target': 'new',
            'domain': [('purchase_id', '=', self.id)],
            'views': [[view_form_id, 'form']],
            'context': {
                'default_payment_type': 'outbound',
                'default_partner_type': 'supplier',
                'default_move_journal_types': ('bank', 'cash'),
                'default_purchase_id': self.id,
                'default_sale_id': self.origin_po.id,
                'default_partner_id': self.partner_id.id,
                'default_amount': self.amount_total,
                'default_ref': _(f'Thanh toán cho {self.name}'),
            },
        }

    def action_open_payment(self):
        view_id = self.env.ref('dpt_account_payment_request.dpt_view_account_payment_request_tree').id
        view_form_id = self.env.ref('dpt_account_payment_request.dpt_view_account_payment_request_form').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'name': _('Payment'),
            'view_mode': 'tree,form',
            'domain': [('purchase_id', '=', self.id)],
            'views': [[view_id, 'tree'], [view_form_id, 'form']],
            'context': {
                'default_payment_type': 'outbound',
                'default_partner_type': 'supplier',
                'default_move_journal_types': ('bank', 'cash'),
                'default_purchase_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_ref': _(f'Thanh toán cho {self.name}'),
            },
        }

    @api.depends('payment_ids')
    def _compute_payment_count(self):
        for rec in self:
            rec.payment_count = len(rec.payment_ids)
            payment_amount_total = 0
            for payment_id in rec.payment_ids:
                payment_amount_total += payment_id.amount
            rec.payment_amount_total = payment_amount_total

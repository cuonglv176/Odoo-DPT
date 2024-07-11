from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    deposit_count = fields.Integer(string='Deposit count', compute="_compute_deposit_count")
    deposit_amount_total = fields.Float(string='Deposit Amount', compute="_compute_deposit_count")

    def action_open_deposit(self):
        view_id = self.env.ref('account.view_account_payment_tree').id
        view_form_id = self.env.ref('account.view_account_payment_form').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'name': _('Deposit'),
            'view_mode': 'tree,form',
            'domain': [('origin_po', '=', self.id)],
            'views': [[view_id, 'tree'], [view_form_id, 'form']],
            'context': {
                'default_sale_id': self.origin_po.id,
                'default_partner_id': self.partner_id.id,
                'default_ref': _(f'Đặt Cọc Đơn Hàng {self.name}'),
            },
        }

    @api.depends('origin_po')
    def _compute_deposit_count(self):
        for rec in self:
            deposit_ids = self.env['account.payment'].search[('sale_id', '=', rec.origin_po.id)]
            rec.deposit_count = len(deposit_ids)
            deposit_amount_total = 0
            for deposit_id in deposit_ids:
                deposit_amount_total += deposit_id.amount
            rec.deposit_amount_total = deposit_amount_total

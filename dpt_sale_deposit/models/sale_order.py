from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    deposit_ids = fields.One2many('account.payment', 'sale_id', string='Deposit')
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
            'domain': [('sale_id', '=', self.id)],
            'views': [[view_id, 'tree'], [view_form_id, 'form']],
            'context': {
                'default_sale_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_ref': _(f'Đặt Cọc Đơn Hàng {self.name}'),
            },
        }

    @api.depends('deposit_ids')
    def _compute_deposit_count(self):
        for rec in self:
            rec.deposit_count = len(rec.deposit_ids)
            deposit_amount_total = 0
            for deposit_id in rec.deposit_ids:
                deposit_amount_total += deposit_id.amount
            rec.deposit_amount_total = deposit_amount_total

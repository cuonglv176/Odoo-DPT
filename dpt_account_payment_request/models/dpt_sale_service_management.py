from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class SaleServiceManagement(models.Model):
    _inherit = 'dpt.sale.service.management'

    def action_create_account_payment_with_multiple_service(self):
        view_form_id = self.env.ref('dpt_account_payment_request.dpt_view_account_payment_request_form').id
        account_payment_id = self.env['account.payment'].search([(
            'service_sale_ids', 'in', self.ids
        )])
        if account_payment_id:
            return {
                'name': _('Payment'),
                'type': 'ir.actions.act_window',
                'res_model': 'account.payment',
                'view_mode': 'form',
                'target': 'new',
                'views': [(view_form_id, 'form')],
                'res_id': account_payment_id.id,
            }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'name': _('Payment'),
            'view_mode': 'form',
            'target': 'new',
            'views': [[view_form_id, 'form']],
            'context': {
                'default_payment_type': 'inbound',
                'default_from_so': True,
                'default_code': 'DNTT',
                'default_partner_type': 'supplier',
                'default_service_sale_ids': [(6, 0, self.ids)],
                'default_move_journal_types': ('bank', 'cash'),
                'default_sale_id': self[0].sale_id.id,
                'default_partner_id': self[0].sale_id.partner_id.id,
                'default_amount': sum(self.mapped('amount_total')),
                'default_ref': _(f'Thanh toán cho {self[0].sale_id.name}'),
            },
        }

    def action_create_or_open_approval_request(self):
        view_form_id = self.env.ref('dpt_account_payment_request.dpt_view_account_payment_request_form').id
        account_payment_id = self.env['account.payment'].search([(
            'service_sale_ids', '=', self.id
        )])
        if account_payment_id:
            return {
                'name': _('Payment'),
                'type': 'ir.actions.act_window',
                'res_model': 'account.payment',
                'view_mode': 'form',
                'target': 'new',
                'views': [(view_form_id, 'form')],
                'res_id': account_payment_id.id,
            }
        service_id = self.service_id
        sale_id = self.sale_id
        default_amount_request = 0
        default_account_payment_type_id = service_id.account_payment_type_id
        match default_account_payment_type_id.code:
            case '2' | '3':
                field_data = sale_id.mapped('fields_ids').filtered(
                    lambda f: f.fields_id.code == 'amount_tax_refund_cny'
                )
                if field_data:
                    default_amount_request = sum(field_data.mapped('value_integer'))
            case '4':
                field_data = sale_id.mapped('fields_ids').filtered(
                    lambda f: f.fields_id.code == 'amount_total_tax_refund_cny'
                )
                if field_data:
                    default_amount_request = sum(field_data.mapped('value_integer'))
            case '5':
                default_amount_request = self.price_cny

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'name': _('Payment'),
            'view_mode': 'form',
            'target': 'new',
            'domain': [('sale_id', '=', self.id)],
            'views': [[view_form_id, 'form']],
            'context': {
                'default_payment_type': 'inbound',
                'default_from_so': True,
                'default_code': 'DNTT',
                'default_partner_type': 'supplier',
                'default_move_journal_types': ('bank', 'cash'),
                'default_sale_id': self.sale_id.id,
                'default_partner_id': self.sale_id.partner_id.id,
                'default_service_sale_ids': [(6, 0, self.ids)],
                'default_service_sale_id': self.id,
                'default_qty': self.compute_value,
                'default_price': self.price_cny * self.sale_id.currency_id.rate if self.price_cny != 0 else self.price,
                'default_uom_id': self.uom_id.id,
                'default_price_cny': self.price_cny,
                'default_amount': self.amount_total,
                'default_ref': _(f'Thanh toán cho {self.sale_id.name}'),
                'default_last_rate_currency': self.currency_cny_id.rate,
                'default_partner_bank_id': self.sale_id.partner_id.bank_ids[:1] if self.sale_id.partner_id.bank_ids else None,
                'default_amount_request': default_amount_request,
                'default_type_id': default_account_payment_type_id.id,
            },
        }

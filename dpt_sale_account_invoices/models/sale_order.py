from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


class SalesOrder(models.Model):
    _inherit = 'sale.order'

    purchase_amount_total = fields.Monetary(string='Purchase total', compute="_compute_purchase_amount_total")
    invoice_amount_total = fields.Monetary(string='Invoice total', compute="_compute_invoice_amount_total")
    payment_amount_total = fields.Monetary(string='Payment total', compute="_compute_payment_amount_total")

    @api.depends('invoice_ids', 'invoice_ids.amount_total')
    def _compute_invoice_amount_total(self):
        for rec in self:
            invoice_amount_total = 0
            for invoice_id in rec.invoice_ids:
                if invoice_id.state == 'posted':
                    invoice_amount_total += invoice_id.amount_total
            rec.invoice_amount_total = invoice_amount_total

    @api.depends('amount_total', 'service_total_amount')
    def _compute_payment_amount_total(self):
        for rec in self:
            rec.payment_amount_total = rec.amount_total + rec.service_total_amount

    @api.depends('purchase_ids', 'purchase_ids.amount_untaxed')
    def _compute_purchase_amount_total(self):
        for rec in self:
            purchase_amount_total = 0
            for purchase_id in rec.purchase_ids:
                if purchase_id.purchase_type == 'external':
                    if purchase_id.currency_id.name == 'VND':
                        purchase_amount_total += purchase_id.amount_untaxed
                    else:
                        purchase_amount_total += purchase_id.amount_untaxed * purchase_id.currency_id.rate
            rec.purchase_amount_total = purchase_amount_total

from odoo import models, fields, api, _


class DPTSaleCalculation(models.Model):
    _name = 'dpt.sale.calculation'

    def _default_service_id(self):
        return self.env.context.get('active_id') or self.env.context.get('default_service_id')

    service_id = fields.Many2one('dpt.service.management', default=_default_service_id)
    sale_service_id = fields.Many2one('dpt.sale.service.management')
    calculation_line_ids = fields.One2many('dpt.sale.calculation.line', 'parent_id')
    min_amount_total = fields.Monetary(string="Min Amount", currency_field="currency_id",
                                       compute="_compute_min_amount_total")
    currency_id = fields.Many2one(related="service_id.currency_id")

    def _compute_min_amount_total(self):
        for item in self:
            item.min_amount_total = max(item.calculation_line_ids.mapped('min_amount_total'))

    def action_save(self):
        max_amount = self.calculation_line_ids.sorted(key=lambda t: t.amount_total, reverse=True)[:1]
        self.sale_service_id.write({
            'uom_id': max_amount.uom_id.id,
            'qty': max_amount.qty,
            'price': max_amount.price,
            'price_status': 'approved',
        })

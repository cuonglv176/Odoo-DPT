from odoo import models, fields, api, _


class DPTSaleCalculation(models.Model):
    _name = 'dpt.sale.calculation'

    def _default_service_id(self):
        return self.env.context.get('active_id') or self.env.context.get('default_service_id')

    service_id = fields.Many2one('dpt.service.management', default=_default_service_id)
    calculation_line_ids = fields.One2many('dpt.sale.calculation.line', 'parent_id')
    min_amount_total = fields.Monetary(string="Min Amount", compute="_compute_min_amount_total")

    def _compute_min_amount_total(self):
        for item in self:
            item.min_amount_total = max(item.calculation_line_ids.mapped('min_amount_total'))

    def action_save(self):
        return

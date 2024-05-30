from odoo import models, fields, api, _


class DPTSaleCalculattion(models.Model):
    _name = 'dpt.sale.calculation'

    def _default_service_id(self):
        return self.env.context.get('active_id') or self.env.context.get('default_service_id')

    service_id = fields.Many2one('dpt.service.management', default=_default_service_id)
    service_ids = fields.One2many('dpt.sale.calculation.line', 'parent_id')

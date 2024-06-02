from odoo import fields, models, api


class DPTServiceManagement(models.Model):
    _inherit = 'dpt.service.management'

    pricelist_item_ids = fields.One2many('product.pricelist.item', 'service_id', string='Pricelist')

    def get_active_pricelist(self):
        return self.pricelist_item_ids.filtered(lambda p: not p.date_end or (
                    p.date_start and p.date_end and p.date_start <= fields.Date.today() and p.date_end >= fields.Date.today()))

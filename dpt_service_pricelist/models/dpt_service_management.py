from odoo import fields, models, api


class DPTServiceManagement(models.Model):
    _inherit = 'dpt.service.management'

    pricelist_item_ids = fields.One2many('product.pricelist.item', 'service_id', string='Pricelist')

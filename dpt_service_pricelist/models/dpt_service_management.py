from odoo import fields, models, api


class DPTServiceManagement(models.Model):
    _inherit = 'dpt.service.management'

    pricelist_item_ids = fields.One2many('product.pricelist.item', 'service_id', string='Pricelist')

    def get_active_pricelist(self, partner_id):
        valid_pricelist_ids = self.pricelist_item_ids.filtered(lambda p: not p.date_end or (
                p.date_start and p.date_end and p.date_start <= fields.Date.today() and p.date_end >= fields.Date.today()))
        valid_partner_pricelist_ids = valid_pricelist_ids.filtered(lambda p: p.partner_id == partner_id)
        valid_pricelist_ids -= valid_pricelist_ids.filtered(
            lambda p: not p.partner_id and p.uom_id.id in valid_partner_pricelist_ids.mapped('uom_id').ids)
        return valid_pricelist_ids

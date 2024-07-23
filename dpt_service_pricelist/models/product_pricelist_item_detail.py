from odoo import fields, models, api, _


class ProductPricelistItemDetail(models.Model):
    _name = 'product.pricelist.item.detail'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']

    item_id = fields.Many2one('product.pricelist.item', 'Pricelist Item', tracking=True)
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist', tracking=True)
    amount = fields.Monetary(currency_field='currency_id', string="Amount", digits='Product Price', tracking=True)
    uom_id = fields.Many2one('uom.uom', 'Product Units', tracking=True)
    description = fields.Char('Description', tracking=True)
    min_value = fields.Float('Min Value', tracking=True)
    max_value = fields.Float('Max Value', tracking=True)
    currency_id = fields.Many2one(related='item_id.currency_id')
    service_id = fields.Many2one(related='item_id.service_id')

    def unlink(self):
        # log to front end of deleted bookings
        mapping_delete = {}
        for item in self:
            if mapping_delete.get(item.item_id.service_id):
                mapping_delete[item.item_id.service_id] = mapping_delete.get(item.item_id.service_id) | item
            else:
                mapping_delete[item.item_id.service_id] = item
        for service_id, pricelist_item_detail_ids in mapping_delete.items():
            service_id.message_post(
                body=_("Delete Pricelist Table: %s") % ','.join(pricelist_item_detail_ids.mapped('uom_id').mapped('name')))
        return super(ProductPricelistItemDetail, self).unlink()

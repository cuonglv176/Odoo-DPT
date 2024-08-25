from odoo import fields, models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    sale_purchase_id = fields.Many2one('sale.order', 'Sale', compute="_compute_sale", inverse="_inverse_sale",
                                       store=True, copy=True)
    customer_id = fields.Many2one(related="sale_purchase_id.partner_id", string="Customer")

    @api.depends('purchase_id', 'purchase_id.sale_id')
    def _compute_sale(self):
        for item in self:
            item.sale_id = item.purchase_id.sale_id

    def _inverse_sale(self):
        pass

    def _sanity_check(self, separate_pickings=True):
        pass

    @api.constrains('sale_purchase_id', 'package_ids', 'total_volume', 'total_weight')
    def constrains_picking(self):
        for item in self:
            if not item.sale_purchase_id:
                continue
            item.sale_purchase_id.recompute_weight_volume()
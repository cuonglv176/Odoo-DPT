from odoo import fields, models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    sale_purchase_id = fields.Many2one('sale.order', 'Sale', compute="_compute_sale", inverse="_inverse_sale",
                                       store=True)

    @api.depends('purchase_id', 'purchase_id.sale_id')
    def _compute_sale(self):
        for item in self:
            item.sale_id = item.purchase_id.sale_id

    def _inverse_sale(self):
        pass

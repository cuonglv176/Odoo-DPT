from odoo import fields, models, api, _


class DPTSaleServiceManagement(models.Model):
    _inherit = 'dpt.sale.service.management'

    picking_id = fields.Many2one('stock.picking', 'Picking')

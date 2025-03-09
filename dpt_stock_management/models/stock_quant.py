# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    weight = fields.Float('Weight (kg)', related="lot_id.weight")
    volume = fields.Float('Volume (m3)', related="lot_id.volume")
    total_weight = fields.Float('Total Weight (kg)', related="lot_id.total_weight")
    total_volume = fields.Float('Total Volume (m3)', related="lot_id.total_volume")
    sale_id = fields.Many2one('sale.order', 'Sales', compute="_compute_sale_information")
    employee_cs = fields.Many2one('hr.employee', string='Employee CS', compute="_compute_sale_information")
    partner_id = fields.Many2one('res.partner', string='Khách hàng', compute="_compute_sale_information")

    def _compute_sale_information(self):
        for item in self:
            incoming_picking_id = self.env['stock.picking'].sudo().search(
                [('is_main_incoming', '=', True), ('picking_lot_name', '=', item.lot_id.name)], limit=1)
            sale_id = incoming_picking_id.sale_purchase_id if incoming_picking_id else None
            item.sale_id = sale_id
            item.employee_cs = sale_id.employee_cs if sale_id else None
            item.partner_id = sale_id.partner_id if sale_id else None

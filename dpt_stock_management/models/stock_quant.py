# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    weight = fields.Float('Weight (kg)', related="lot_id.weight")
    volume = fields.Float('Volume (m3)', related="lot_id.volume")
    total_weight = fields.Float('Total Weight (kg)', related="lot_id.total_weight", store=True)
    total_volume = fields.Float('Total Volume (m3)', related="lot_id.total_volume", store=True)
    sale_id = fields.Many2one('sale.order', 'Đơn hàng', compute="_compute_sale_information")
    employee_cs = fields.Many2one('hr.employee', string='Employee CS', compute="_compute_sale_information")
    partner_id = fields.Many2one('res.partner', string='Khách hàng', compute="_compute_sale_information")
    packing_lot_name = fields.Char('Nhóm kiện', compute="_compute_sale_information")
    package_name = fields.Char('Mã Pack', compute="_compute_sale_information")
    inventory_duration = fields.Integer(compute="_compute_inventory_duration", string="Ngày lưu kho")

    def _compute_inventory_duration(self):
        for item in self:
            duration = (fields.Date.today() - item.create_date).days
            item.inventory_duration = duration

    def _compute_sale_information(self):
        for item in self:
            incoming_picking_id = self.env['stock.picking'].sudo().search(
                [('is_main_incoming', '=', True), ('picking_lot_name', '=', item.lot_id.name)], limit=1)
            sale_id = incoming_picking_id.sale_purchase_id if incoming_picking_id else None
            item.sale_id = sale_id
            item.employee_cs = sale_id.employee_cs if sale_id else None
            item.partner_id = sale_id.partner_id if sale_id else None
            item.packing_lot_name = incoming_picking_id.packing_lot_name if incoming_picking_id else None
            uom_id = self.env['uom.uom'].sudo().search(
                [('product_id', '=', item.product_id.id), ('is_package_unit', '=', True)], limit=1)
            item.package_name = f"{item.quantity}{uom_id.packing_code}" if uom_id and item.quantity else ""

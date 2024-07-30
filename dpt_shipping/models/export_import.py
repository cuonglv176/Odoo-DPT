# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _, api


class DptExportImport(models.Model):
    _inherit = "dpt.export.import"

    shipping_slip_id = fields.Many2one('dpt.shipping.slip', string='Shipping Slip')
    type_of_vehicle = fields.Char(compute="_compute_shipping_information", store=True)
    driver_name = fields.Char(compute="_compute_shipping_information", store=True)
    driver_phone_number = fields.Char(compute="_compute_shipping_information", store=True)
    vehicle_license_plate = fields.Char(compute="_compute_shipping_information", store=True)

    @api.depends('shipping_slip_id', 'shipping_slip_id.vehicle_id')
    def _compute_shipping_information(self):
        for item in self:
            item.driver_name = item.shipping_slip_id.vehicle_id.driver_id.name
            item.driver_phone_number = item.shipping_slip_id.vehicle_id.driver_id.phone or item.shipping_slip_id.vehicle_id.driver_id.mobile
            item.vehicle_license_plate = item.shipping_slip_id.vehicle_id.license_plate
            item.type_of_vehicle = item.shipping_slip_id.vehicle_id.license_plate

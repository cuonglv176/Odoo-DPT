# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    is_main_incoming_warehouse = fields.Boolean('Is main incoming Warehouse')
    is_main_outgoing_warehouse = fields.Boolean('Is Main Outgoing Warehouse')

    @api.constrains('is_main_incoming_warehouse')
    def _check_main_incoming_warehouse(self):
        other_main_warehouse_ids = self.env['stock.warehouse'].sudo().search(
            [('is_main_incoming_warehouse', '=', True)])
        if len(other_main_warehouse_ids) > 1:
            raise ValidationError(_('Cannot configurate 2 or more warehouse is main incoming warehouse'))

    @api.constrains('is_main_outgoing_warehouse')
    def _check_main_outgoing_warehouse(self):
        other_main_warehouse_ids = self.env['stock.warehouse'].sudo().search(
            [('is_main_outgoing_warehouse', '=', True)])
        if len(other_main_warehouse_ids) > 1:
            raise ValidationError(_('Cannot configurate 2 or more warehouse is main outgoing warehouse'))

# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    is_main_incoming_warehouse = fields.Boolean('Is main incoming Warehouse')

    @api.constrains('is_main_incoming_warehouse')
    def _check_country(self):
        for record in self:
            other_main_warehouse_ids = self.env['stock.warehouse'].sudo().search(
                [('id', '!=', record._origin.id), ('is_main_incoming_warehouse', '=', True)])
            if other_main_warehouse_ids:
                raise ValidationError(_('Cannot configurate 2 or more warehouse is main incoming warehouse'))

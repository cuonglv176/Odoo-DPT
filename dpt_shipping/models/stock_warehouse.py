# -*- coding: utf-8 -*-
from odoo import _, api, fields, models, SUPERUSER_ID


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    is_tq_transit_warehouse = fields.Boolean('Là kho chuyển TQ')
    is_vn_transit_warehouse = fields.Boolean('Là kho chuyển VN')

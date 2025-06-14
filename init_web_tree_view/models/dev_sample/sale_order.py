# -*- coding: utf-8 -*-
# Copyright 2022 Init, Ltd (https://www.init.vn/)
from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    parent_id = fields.Many2one(
        'sale.order',
        string='Parent',
    )
    child_ids = fields.One2many(
        'sale.order',
        'parent_id',
        string='Children',
    )


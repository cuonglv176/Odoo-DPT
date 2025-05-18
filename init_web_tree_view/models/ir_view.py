# -*- coding: utf-8 -*-
# Copyright 2022 Init, Ltd (https://www.init.vn/)
from odoo import fields, models, api

INIT_TREE_VIEW = ('init_tree', 'InitTree')


class View(models.Model):
    _inherit = 'ir.ui.view'

    type = fields.Selection(
        selection_add=[INIT_TREE_VIEW]
    )

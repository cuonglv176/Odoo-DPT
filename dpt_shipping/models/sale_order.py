# -*- coding: utf-8 -*-
import json
from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_update_picking(self):
        action = self.env.ref('dpt_shipping.dpt_get_picking_so_wizard_action').sudo().read()[0]
        action['context'] = {'default_sale_id': self.id}
        return action

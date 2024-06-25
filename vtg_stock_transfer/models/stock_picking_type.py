# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    def _get_action(self, action_xmlid):
        action = super(StockPickingType, self)._get_action(action_xmlid)
        if self.code != 'internal':
            return action
        action['context']['default_x_transfer_type'] = 'outgoing_transfer'
        action['context']['default_immediate_transfer'] = False
        return action

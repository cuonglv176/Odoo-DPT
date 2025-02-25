# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from ast import literal_eval
from odoo import fields, models, _, api
import logging
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    def write(self, vals):
        res = super(ResCurrency, self).write(vals)
        for currency_rate in self:
            if currency_rate.category == 'import_export':
                line_xnk_ids = self.env['dpt.export.import.line'].search(
                    [('state', 'not in', ('eligible', 'cancelled'))])
                for line_xnk_id in line_xnk_ids:
                    line_xnk_id.compute_dpt_exchange_rate()
            if currency_rate.category == 'basic':
                line_xhd_ids = self.env['dpt.export.import.line'].search(
                    ['|', ('export_import_id', '=', False), ('export_import_id.state', '!=', 'cleared')])
                for line_xhd_id in line_xhd_ids:
                    line_xhd_id.compute_dpt_price_unit()
        return res

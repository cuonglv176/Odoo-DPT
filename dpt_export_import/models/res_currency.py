# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from ast import literal_eval
from odoo import fields, models, _, api
import logging
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    @api.onchange('company_rate')
    def _inverse_company_rate(self):
        last_rate = self.env['res.currency.rate']._get_last_rates_for_companies(
            self.company_id | self.env.company.root_id)
        for currency_rate in self:
            company = currency_rate.company_id or self.env.company.root_id
            currency_rate.rate = currency_rate.company_rate * last_rate[company]
            if currency_rate.category == 'import_export':
                line_xnk_ids = self.env['dpt.export.import.line'].search(
                    [('state', 'not in', ('eligible', 'cancelled'))])
                for line_xnk_id in line_xnk_ids:
                    line_xnk_id.compute_dpt_exchange_rate()
            if currency_rate.category == 'basic':
                line_xhd_ids = self.env['dpt.export.import.line'].search(
                    [('export_import_id', '=', False), ('export_import_id.state', '!=', 'cleared')])
                for line_xhd_id in line_xhd_ids:
                    line_xhd_id.onchange_dpt_price_unit()

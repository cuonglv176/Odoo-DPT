# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move.line'

    sale_order_id = fields.Many2one('sale.order', string='Đơn hàng')

# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class UomUom(models.Model):
    _inherit = 'uom.uom'

    use_for_allocate_expense = fields.Boolean("Sử dụng để phân bổ chi phí", defautl=False)
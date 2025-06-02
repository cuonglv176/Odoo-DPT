# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class DptServiceManagement(models.Model):
    _inherit = 'dpt.service.management'

    use_for_allocate_expense = fields.Boolean('Dịch vụ là dịch vụ xác định đơn vị phân bổ', default=False,
                                              tracking=True,
                                              help='Đánh dấu dịch vụ này là dịch vụ xác định đơn vị phân bổ')

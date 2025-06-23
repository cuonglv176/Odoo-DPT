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
        # Đã loại bỏ logic cập nhật tự động tỷ giá hải quan cho các bản ghi dpt.export.import.line
        # khi tỷ giá thuộc danh mục import_export thay đổi
        return res

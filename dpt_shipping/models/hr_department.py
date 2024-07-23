# -*- coding: utf-8 -*-
import json
from odoo import models, fields, api


class HRDepartment(models.Model):
    _inherit = 'hr.department'

    is_chinese_stock_department = fields.Boolean('Is Chinese Stock Department')

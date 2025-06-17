# -*- coding: utf-8 -*-
from odoo import fields, models

class ResCompany(models.Model):
    """
    Kế thừa model res.company để thêm các trường cấu hình tỷ lệ lợi nhuận.
    Các trường này sẽ được sử dụng để xác định khoảng giá bán cho phép.
    """
    _inherit = 'res.company'

    # dpt_min_profit_margin = fields.Float(
    #     string="Tỷ lệ lợi nhuận tối thiểu (Giá XHĐ)",
    #     default=1.01,
    #     help="Hệ số nhân với giá vốn để tính giá bán tối thiểu. Ví dụ: 1.01 tương đương lợi nhuận 1%."
    # )
    # dpt_max_profit_margin = fields.Float(
    #     string="Tỷ lệ lợi nhuận tối đa (Giá XHĐ)",
    #     default=1.03,
    #     help="Hệ số nhân với giá vốn để tính giá bán tối đa. Ví dụ: 1.03 tương đương lợi nhuận 3%."
    # )
# -*- coding: utf-8 -*-
from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    """
    Kế thừa model res.config.settings để hiển thị các trường cấu hình trong giao diện Cài đặt.
    Các trường này liên kết (related) với các trường trong res.company.
    """
    _inherit = 'res.config.settings'

    # dpt_min_profit_margin = fields.Float(
    #     related='company_id.dpt_min_profit_margin',
    #     readonly=False,
    #     string="Tỷ lệ lợi nhuận tối thiểu (Giá XHĐ)",
    #     help="Hệ số nhân với giá vốn để tính giá bán tối thiểu"
    # )
    # dpt_max_profit_margin = fields.Float(
    #     related='company_id.dpt_max_profit_margin',
    #     readonly=False,
    #     string="Tỷ lệ lợi nhuận tối đa (Giá XHĐ)",
    #     help="Hệ số nhân với giá vốn để tính giá bán tối đa"
    # )
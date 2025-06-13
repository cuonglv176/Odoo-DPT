# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class PriceApprovalWizard(models.TransientModel):
    _name = 'dpt.price.approval.wizard'
    _description = 'Wizard Xác nhận phê duyệt giá'

    export_import_line_id = fields.Many2one('dpt.export.import.line', string='Dòng tờ khai', readonly=True)
    product_id = fields.Many2one(related='export_import_line_id.product_id', string='Sản phẩm', readonly=True)
    current_price = fields.Monetary(string='Giá muốn áp dụng', currency_field='currency_id', readonly=True)
    min_price = fields.Monetary(string='Giá tối thiểu', currency_field='currency_id', readonly=True)
    max_price = fields.Monetary(string='Giá tối đa', currency_field='currency_id', readonly=True)
    system_price = fields.Monetary(string='Giá hệ thống', currency_field='currency_id', readonly=True)
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', readonly=True)
    
    def action_send_approval(self):
        """Gửi yêu cầu phê duyệt giá"""
        self.ensure_one()
        approval_request = self.export_import_line_id._create_price_approval_request()
        # Đóng wizard sau khi tạo yêu cầu phê duyệt
        return {
            'type': 'ir.actions.act_window_close'
        }
    
    def action_cancel(self):
        """Hủy thay đổi giá và quay lại giá hệ thống"""
        self.ensure_one()
        self.export_import_line_id.write({
            'dpt_price_unit': self.system_price,
            'price_outside_range': False
        })
        # Hiện thông báo và đóng wizard
        return {
            'type': 'ir.actions.act_window_close'
        } 
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    def action_approve(self, approver=None):
        """Override phương thức phê duyệt để cập nhật trạng thái của bảng giá"""
        result = super(ApprovalRequest, self).action_approve(approver)

        # Chỉ xử lý phê duyệt thuộc loại "Duyệt Bảng Giá Khách Hàng" (BGKH)
        if self.request_status == 'approved' and self.category_id.sequence_code == 'BGKH':
            if self.reference and self.reference.startswith('product.pricelist,'):
                self.env['product.pricelist']._handle_approval_approved(self)

        return result

    def action_refuse(self, approver=None):
        """Override phương thức từ chối để cập nhật trạng thái của bảng giá"""
        result = super(ApprovalRequest, self).action_refuse(approver)

        # Chỉ xử lý từ chối thuộc loại "Duyệt Bảng Giá Khách Hàng" (BGKH)
        if self.request_status == 'refused' and self.category_id.sequence_code == 'BGKH':
            if self.reference and self.reference.startswith('product.pricelist,'):
                # Lấy lý do từ chối từ message cuối cùng liên quan đến từ chối
                reason = False
                for message in self.message_ids:
                    if "đã từ chối" in message.body or "has refused" in message.body:
                        reason = message.body
                        break

                self.env['product.pricelist']._handle_approval_refused(self, reason)

        return result
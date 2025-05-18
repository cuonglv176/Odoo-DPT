# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ServiceComboRejectWizard(models.TransientModel):
    _name = 'dpt.service.combo.reject.wizard'
    _description = 'Wizard Từ chối phê duyệt'

    combo_id = fields.Many2one('dpt.service.combo', string='Gói combo', required=True)
    rejection_reason = fields.Text(string='Lý do từ chối', required=True)

    def action_confirm_reject(self):
        self.ensure_one()
        if self.combo_id:
            # Cập nhật trạng thái và lý do từ chối
            self.combo_id.write({
                'state': 'rejected',
                'rejection_reason': self.rejection_reason,
            })
            
            # Cập nhật yêu cầu phê duyệt nếu có
            if self.combo_id.approval_id:
                self.combo_id.approval_id.action_refuse(self.rejection_reason)
                
            # Tạo thông báo trên chatter
            self.combo_id.message_post(
                body=_('Đã từ chối phê duyệt với lý do: %s') % self.rejection_reason,
                message_type='notification'
            )
        return {'type': 'ir.actions.act_window_close'}
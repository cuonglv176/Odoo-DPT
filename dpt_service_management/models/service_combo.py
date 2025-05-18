# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


class DPTServiceCombo(models.Model):
    _name = 'dpt.service.combo'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'DPT Service Combo'
    _order = 'create_date DESC'

    name = fields.Char(string='Tên gói combo', required=True, tracking=True)
    code = fields.Char(string='Mã gói', default='COMBO/', copy=False, readonly=True, tracking=True)
    description = fields.Text(string='Mô tả', tracking=True)
    date_start = fields.Date(string='Ngày bắt đầu', tracking=True)
    date_end = fields.Date(string='Ngày kết thúc', tracking=True)
    price = fields.Float(string='Giá gói', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', default=lambda self: self.env.company.currency_id,
                                  tracking=True)
    version = fields.Integer(string='Phiên bản', default=1, readonly=True, tracking=True)
    active = fields.Boolean(string='Đang hoạt động', default=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('active', 'Đang hoạt động'),
        ('expired', 'Hết hạn'),
        ('cancelled', 'Đã hủy')
    ], string='Trạng thái', default='draft', tracking=True)
    service_ids = fields.Many2many('dpt.service.management', string='Dịch vụ trong gói',
                                   domain=[('child_ids', '=', False)],
                                   help="Chỉ chọn dịch vụ không có dịch vụ con")
    total_services = fields.Integer(string='Tổng số dịch vụ', compute='_compute_total_services', store=True)
    total_price = fields.Float(string='Tổng giá trị', compute='_compute_total_price', store=True)

    _sql_constraints = [
        ('code_uniq', 'unique (code)', "Mã gói combo đã tồn tại!")
    ]

    @api.depends('service_ids')
    def _compute_total_services(self):
        for combo in self:
            combo.total_services = len(combo.service_ids)

    @api.depends('service_ids', 'service_ids.price')
    def _compute_total_price(self):
        for combo in self:
            combo.total_price = sum(service.price for service in combo.service_ids)

    @api.model
    def create(self, vals):
        if vals.get('code', 'COMBO/') == 'COMBO/':
            vals['code'] = self._generate_combo_code()
        return super(DPTServiceCombo, self).create(vals)

    def _generate_combo_code(self):
        sequence = self.env['ir.sequence'].next_by_code('dpt.service.combo') or '001'
        return f'COMBO/{sequence}'

    def action_activate(self):
        for combo in self:
            combo.state = 'active'

    def action_cancel(self):
        for combo in self:
            combo.state = 'cancelled'

    def action_draft(self):
        for combo in self:
            combo.state = 'draft'

    def action_create_new_version(self):
        for combo in self:
            new_combo = combo.copy({
                'version': combo.version + 1,
                'state': 'draft',
                'name': f"{combo.name} (v{combo.version + 1})"
            })
            return {
                'name': _('Gói combo dịch vụ'),
                'view_mode': 'form',
                'res_model': 'dpt.service.combo',
                'res_id': new_combo.id,
                'type': 'ir.actions.act_window',
            }

    @api.model
    def _cron_check_expired_combos(self):
        today = fields.Date.today()
        expired_combos = self.search([
            ('state', '=', 'active'),
            ('date_end', '<', today)
        ])
        if expired_combos:
            expired_combos.write({'state': 'expired'})
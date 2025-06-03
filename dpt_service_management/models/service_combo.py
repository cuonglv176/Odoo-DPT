# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError, UserError


class DPTServiceCombo(models.Model):
    _name = 'dpt.service.combo'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'DPT Service Combo'
    _order = 'create_date DESC'

    name = fields.Char(string='Tên gói combo', required=True, tracking=True)
    code = fields.Char(string='Mã gói', default='COMBO/', copy=False, readonly=True, tracking=True)
    description = fields.Text(string='Mô tả', tracking=True)
    quote_type = fields.Selection([
        ('bao_giao', 'Báo giá là bao giao'),
        ('all_in', 'Báo giá là all in')
    ], string='Loại báo giá', default='bao_giao', tracking=True,
       help="Bao giao là bao vận chuyển, all in là tất cả giá")
    date_start = fields.Date(string='Ngày bắt đầu', tracking=True)
    date_end = fields.Date(string='Ngày kết thúc', tracking=True)
    price = fields.Float(string='Giá gói', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Tiền tệ', default=lambda self: self.env.company.currency_id,
                                  tracking=True)
    version = fields.Integer(string='Phiên bản', default=1, readonly=True, tracking=True)
    active = fields.Boolean(string='Đang hoạt động', default=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('pending', 'Chờ phê duyệt'),
        ('rejected', 'Bị từ chối'),
        ('active', 'Đang hoạt động'),
        ('suspended', 'Tạm dừng'),
        ('expired', 'Hết hạn'),
        ('cancelled', 'Đã hủy')
    ], string='Trạng thái', default='draft', tracking=True)
    service_ids = fields.Many2many('dpt.service.management', string='Dịch vụ trong gói',
                                   domain=[('child_ids', '=', False)],
                                   help="Chỉ chọn dịch vụ không có dịch vụ con")
    total_services = fields.Integer(string='Tổng số dịch vụ', compute='_compute_total_services', store=True)
    total_price = fields.Float(string='Tổng giá trị', compute='_compute_total_price', store=True)

    # Thêm trường tài khoản doanh thu và chi phí
    revenue_account_id = fields.Many2one('account.account', string='Tài khoản doanh thu',
                                        domain=[('deprecated', '=', False)],
                                        tracking=True, copy=True)
    expense_account_id = fields.Many2one('account.account', string='Tài khoản chi phí',
                                        domain=[('deprecated', '=', False)],
                                        tracking=True, copy=True)

    # Thêm trường One2many cho các trường thông tin
    required_fields_ids = fields.One2many('dpt.service.management.required.fields', 'combo_id',
                                         string='Các trường thông tin', copy=True, auto_join=True)

    # Thêm các trường liên quan đến phê duyệt
    approval_id = fields.Many2one('approval.request', string='Yêu cầu phê duyệt', copy=False, readonly=True)
    approver_ids = fields.Many2many('res.users', string='Người phê duyệt', compute='_compute_approver_ids', store=False)
    approval_date = fields.Datetime(string='Ngày phê duyệt', readonly=True, copy=False)
    approved_by = fields.Many2one('res.users', string='Phê duyệt bởi', readonly=True, copy=False)
    rejection_reason = fields.Text(string='Lý do từ chối', readonly=True, copy=False)

    # Thêm trường mới để lưu trữ các đơn vị đo lường từ các dịch vụ trong combo
    service_uom_ids = fields.Many2many('uom.uom', string='Đơn vị đo lường', compute='_compute_service_uom_ids')
    service_uom_summary = fields.Text(string='Tổng hợp đơn vị', compute='_compute_service_uom_summary')
    product_id = fields.Many2one('product.product', string='Product')

    _sql_constraints = [
        ('code_uniq', 'unique (code)', "Mã gói combo đã tồn tại!")
    ]

    @api.onchange('service_ids')
    def _onchange_service_ids(self):
        # Tự động lấy các trường thông tin từ dịch vụ
        self.sync_required_fields_from_services()

    def sync_required_fields_from_services(self):
        """Đồng bộ các trường thông tin từ dịch vụ"""
        self.ensure_one()
        if not self.service_ids:
            return

        # Xóa các trường thông tin cũ nếu có
        self.required_fields_ids.unlink()

        # Thu thập tất cả các trường thông tin từ dịch vụ
        required_fields_data = []
        existing_fields = {}  # Để theo dõi các trường đã thêm

        for service in self.service_ids:
            for required_field in service.required_fields_ids:
                field_key = required_field.name or required_field.code

                # Nếu trường này chưa được thêm
                if field_key not in existing_fields:
                    # Tạo dữ liệu cho trường thông tin mới
                    vals = {
                        'name': required_field.name,
                        'description': required_field.description,
                        'fields_type': required_field.fields_type,
                        'field': required_field.field,
                        'type': required_field.type,
                        'using_calculation_price': required_field.using_calculation_price,
                        'uom_id': required_field.uom_id.id if required_field.uom_id else False,
                        'default_compute_from': required_field.default_compute_from,
                        'code': required_field.code,
                        'is_template': required_field.is_template,
                        'combo_id': self.id,
                    }

                    # Nếu trường là fields_id, thêm vào
                    if required_field.fields_id:
                        vals['fields_id'] = required_field.fields_id.id

                    required_fields_data.append(vals)
                    existing_fields[field_key] = True

        # Tạo các bản ghi trường thông tin mới
        if required_fields_data:
            for vals in required_fields_data:
                new_required_field = self.env['dpt.service.management.required.fields'].create(vals)

                # Xử lý các giá trị selection nếu có
                if new_required_field.fields_type == 'selection':
                    for selection in self.env['dpt.sale.order.fields.selection'].search([
                        ('fields_id', '=', vals.get('fields_id'))
                    ]):
                        self.env['dpt.sale.order.fields.selection'].create({
                            'fields_id': new_required_field.id,
                            'name': selection.name,
                        })

    @api.depends('service_ids', 'service_ids.uom_ids')
    def _compute_service_uom_ids(self):
        """Tính toán tất cả các đơn vị đo lường từ các dịch vụ trong combo"""
        for combo in self:
            uom_ids = []
            for service in combo.service_ids:
                for uom in service.uom_ids:
                    if uom.id not in uom_ids:
                        uom_ids.append(uom.id)
            combo.service_uom_ids = [(6, 0, uom_ids)]

    @api.depends('service_ids', 'service_ids.uom_ids')
    def _compute_service_uom_summary(self):
        """Tạo bảng tổng hợp về đơn vị theo dịch vụ"""
        for combo in self:
            summary = {}
            for service in combo.service_ids:
                if service.id not in summary:
                    summary[service.id] = {
                        'service_name': service.name,
                        'uoms': []
                    }
                for uom in service.uom_ids:
                    summary[service.id]['uoms'].append({
                        'uom_name': uom.name,
                        'uom_id': uom.id
                    })
            combo.service_uom_summary = str(summary) if summary else False

    @api.depends('service_ids')
    def _compute_total_services(self):
        for combo in self:
            combo.total_services = len(combo.service_ids)

    @api.depends('service_ids', 'service_ids.price')
    def _compute_total_price(self):
        for combo in self:
            combo.total_services = len(combo.service_ids)

    @api.depends('service_ids', 'service_ids.price')
    def _compute_total_price(self):
        for combo in self:
            combo.total_price = sum(service.price for service in combo.service_ids)

    def _compute_approver_ids(self):
        """Lấy danh sách người phê duyệt dựa vào cấu hình phê duyệt"""
        for record in self:
            # Lấy người phê duyệt từ cấu hình approval type 'service_combo_approval'
            approval_type = self.env['approval.category'].search([('sequence_code', '=', 'SCM')], limit=1)
            approvers = []
            if approval_type:
                for approver in approval_type.user_ids:
                    approvers.append(approver.id)
            record.approver_ids = [(6, 0, approvers)]
    @api.model
    def create(self, vals):
        if vals.get('code', 'COMBO/') == 'COMBO/':
            vals['code'] = self._generate_combo_code()
        return super(DPTServiceCombo, self).create(vals)
    def _generate_combo_code(self):
        sequence = self.env['ir.sequence'].next_by_code('dpt.service.combo') or '001'
        return f'COMBO/{sequence}'

    def action_view_approval(self):
        """Xem chi tiết yêu cầu phê duyệt"""
        self.ensure_one()
        if not self.approval_id:
            return {}

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'approval.request',
            'res_id': self.approval_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_submit_approval(self):
        """Gửi yêu cầu phê duyệt"""
        self.ensure_one()
        if not self.service_ids:
            raise UserError(_('Không thể gửi phê duyệt khi chưa có dịch vụ nào trong gói.'))

        # Kiểm tra xem đã có approval.request cho record này chưa
        if self.approval_id and self.approval_id.request_status != 'refused':
            raise UserError(_('Đã tồn tại yêu cầu phê duyệt cho gói combo này.'))

        # Tìm loại phê duyệt "Duyệt combo dịch vụ"
        approval_type = self.env['approval.category'].search([('sequence_code', '=', 'SCM')], limit=1)
        if not approval_type:
            raise UserError(_('Chưa cấu hình loại phê duyệt "Duyệt combo dịch vụ".'))

        # Tạo yêu cầu phê duyệt mới
        vals = {
            'name': _('Phê duyệt: %s') % self.name,
            'category_id': approval_type.id,
            'date': fields.Datetime.now(),
            'request_owner_id': self.env.user.id,
            'reference': f'dpt.service.combo,{self.id}',
            'request_status': 'pending',
        }
        approval_request = self.env['approval.request'].create(vals)

        # Cập nhật trạng thái và liên kết approval_id
        self.write({
            'state': 'pending',
            'approval_id': approval_request.id,
        })

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'approval.request',
            'res_id': approval_request.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_activate(self):
        for combo in self:
            combo.write({
                'state': 'active',
                'approval_date': fields.Datetime.now(),
                'approved_by': self.env.user.id,
            })

    def action_cancel(self):
        for combo in self:
            combo.state = 'cancelled'

    def action_draft(self):
        for combo in self:
            combo.state = 'draft'

    def action_reject(self):
        """Từ chối phê duyệt"""
        return {
            'name': _('Từ chối phê duyệt'),
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.service.combo.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_combo_id': self.id},
        }

    def action_suspend(self):
        """Tạm dừng gói combo"""
        for combo in self:
            combo.state = 'suspended'

    def action_resume(self):
        """Kích hoạt lại gói đã tạm dừng"""
        for combo in self:
            combo.state = 'active'

    def action_create_new_version(self):
        for combo in self:
            new_combo = combo.copy({
                'version': combo.version + 1,
                'state': 'draft',
                'name': f"{combo.name} (v{combo.version + 1})",
                'approval_id': False,
                'approval_date': False,
                'approved_by': False,
                'rejection_reason': False,
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

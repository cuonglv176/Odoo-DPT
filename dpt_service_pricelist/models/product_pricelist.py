from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import ValidationError, UserError


class ProductPricelist(models.Model):
    _inherit = 'product.pricelist'

    partner_id = fields.Many2one('res.partner', 'Customer', domain=[('customer_rank', '>', 0)], tracking=True)
    # Trường trạng thái
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('pending', 'Chờ phê duyệt'),
        ('rejected', 'Bị từ chối'),
        ('active', 'Đang hoạt động'),
        ('suspended', 'Tạm dừng'),
        ('expired', 'Hết hạn'),
    ], string='Trạng thái', default='draft', tracking=True)

    # Các trường liên quan đến phê duyệt
    approval_id = fields.Many2one('approval.request', string='Yêu cầu phê duyệt', copy=False, readonly=True)
    approver_ids = fields.Many2many('res.users', string='Người phê duyệt', compute='_compute_approver_ids', store=False)
    approval_date = fields.Datetime(string='Ngày phê duyệt', readonly=True, copy=False)
    approved_by = fields.Many2one('res.users', string='Phê duyệt bởi', readonly=True, copy=False)
    rejection_reason = fields.Text(string='Lý do từ chối', readonly=True, copy=False)

    # Thông tin thời gian hiệu lực
    date_start = fields.Date(string='Ngày bắt đầu', tracking=True)
    date_end = fields.Date(string='Ngày kết thúc', tracking=True)

    # Trường combo_item_ids để lưu các item là combo
    combo_item_ids = fields.One2many('product.pricelist.item', 'pricelist_id',
                                  string='Bảng giá Combo',
                                  domain=[('combo_id', '!=', False)])

    def _compute_approver_ids(self):
        """Lấy danh sách người phê duyệt dựa vào cấu hình phê duyệt"""
        for record in self:
            # Lấy người phê duyệt từ cấu hình approval type 'pricelist_approval'
            approval_type = self.env['approval.category'].search([('sequence_code', '=', 'BGKH')], limit=1)
            approvers = []
            if approval_type:
                for approver in approval_type.user_ids:
                    approvers.append(approver.id)
            record.approver_ids = [(6, 0, approvers)]

    @api.model
    def create(self, vals):
        """Override để đảm bảo trạng thái mặc định là draft"""
        if 'state' not in vals:
            vals['state'] = 'draft'
        return super(ProductPricelist, self).create(vals)

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
        if not self.item_ids:
            raise UserError(_('Không thể gửi phê duyệt khi chưa có mức giá nào trong bảng giá.'))

        # Kiểm tra xem đã có approval.request cho record này chưa
        if self.approval_id and self.approval_id.request_status != 'refused':
            raise UserError(_('Đã tồn tại yêu cầu phê duyệt cho bảng giá này.'))

        # Tìm loại phê duyệt "Duyệt bảng giá"
        approval_type = self.env['approval.category'].search([('sequence_code', '=', 'BGKH')], limit=1)
        if not approval_type:
            raise UserError(_('Chưa cấu hình loại phê duyệt "Duyệt bảng giá".'))

        # Tạo yêu cầu phê duyệt mới
        vals = {
            'name': _('Phê duyệt: %s') % self.name,
            'category_id': approval_type.id,
            'pricelist_id': self.id,
            'date': fields.Datetime.now(),
            'request_owner_id': self.env.user.id,
            'reference': f'product.pricelist,{self.id}',
            'request_status': 'new',  # Bắt đầu với trạng thái 'new' thay vì 'pending'
        }
        approval_request = self.env['approval.request'].create(vals)

        # Cập nhật trạng thái và liên kết approval_id
        self.write({
            'state': 'pending',
            'approval_id': approval_request.id,
        })

        # Tự động gửi (submit) approval request
        approval_request.action_confirm()  # Gọi phương thức confirm để chuyển request sang trạng thái "Pending"

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'approval.request',
            'res_id': approval_request.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_suspend(self):
        """Tạm dừng bảng giá"""
        for pricelist in self:
            pricelist.state = 'suspended'

    def action_resume(self):
        """Kích hoạt lại bảng giá đã tạm dừng"""
        for pricelist in self:
            pricelist.state = 'active'

    def action_draft(self):
        """Đặt về trạng thái nháp"""
        for pricelist in self:
            # Xóa approval_id nếu đang ở trạng thái bị từ chối
            if pricelist.state == 'rejected':
                pricelist.write({
                    'state': 'draft',
                    'approval_id': False,
                    'rejection_reason': False,
                })
            else:
                pricelist.state = 'draft'

    def action_add_combo_services(self):
        """Thêm tự động dịch vụ từ các combo đã chọn vào tab dịch vụ"""
        self.ensure_one()
        services_added = 0

        # Duyệt qua các combo đã chọn
        for combo_item in self.combo_item_ids:
            combo = combo_item.combo_id
            if not combo:
                continue

            # Lấy danh sách dịch vụ thuộc combo
            services = combo.service_ids

            # Cho mỗi dịch vụ trong combo, thêm vào bảng giá dịch vụ
            for service in services:
                # Kiểm tra xem dịch vụ đã tồn tại trong bảng giá dịch vụ chưa
                existing_item = self.env['product.pricelist.item'].search([
                    ('pricelist_id', '=', self.id),
                    ('service_id', '=', service.id),
                    ('combo_id', '=', False)
                ], limit=1)

                if not existing_item:
                    # Tạo bảng giá mới cho dịch vụ
                    self.env['product.pricelist.item'].create({
                        'pricelist_id': self.id,
                        'service_id': service.id,
                        'partner_id': combo_item.partner_id.id,
                        'currency_id': combo_item.currency_id.id,
                        'compute_price': 'fixed',
                        'fixed_price': 0.0,  # Giá mặc định, người dùng có thể điều chỉnh sau
                        'date_start': combo_item.date_start,
                        'date_end': combo_item.date_end,
                    })
                    services_added += 1

        # Hiển thị thông báo
        message = _(f'Đã thêm {services_added} dịch vụ từ combo vào tab Dịch vụ')
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Thêm dịch vụ thành công'),
                'message': message,
                'sticky': False,
                'next': {'type': 'ir.actions.client', 'tag': 'reload'},
            }
        }

    @api.model
    def _cron_check_expired_pricelists(self):
        """Kiểm tra và cập nhật trạng thái cho bảng giá đã hết hạn"""
        today = fields.Date.today()
        expired_pricelists = self.search([
            ('state', '=', 'active'),
            ('date_end', '<', today)
        ])
        if expired_pricelists:
            expired_pricelists.write({'state': 'expired'})

    # Phương thức xử lý khi phê duyệt được chấp nhận
    @api.model
    def _handle_approval_approved(self, approval_request):
        """Xử lý khi yêu cầu phê duyệt được chấp nhận"""
        if approval_request.reference and ',' in approval_request.reference:
            model_name, res_id = approval_request.reference.split(',')
            if model_name == 'product.pricelist':
                pricelist = self.browse(int(res_id))
                if pricelist.exists():
                    pricelist.write({
                        'state': 'active',
                        'approval_date': fields.Datetime.now(),
                        'approved_by': self.env.user.id,
                    })
        return True

    # Phương thức xử lý khi phê duyệt bị từ chối
    @api.model
    def _handle_approval_refused(self, approval_request, reason):
        """Xử lý khi yêu cầu phê duyệt bị từ chối"""
        if approval_request.reference and ',' in approval_request.reference:
            model_name, res_id = approval_request.reference.split(',')
            if model_name == 'product.pricelist':
                pricelist = self.browse(int(res_id))
                if pricelist.exists():
                    pricelist.write({
                        'state': 'rejected',
                        'rejection_reason': reason,
                    })
        return True

    def write(self, vals):
        for record in self:
            if record.state == 'active':
                # Chỉ cho phép thay đổi trạng thái
                if vals.keys() != ['state']:
                    raise UserError(_("Không thể chỉnh sửa bảng giá ở trạng thái 'Đang hoạt động'. "
                                    "Vui lòng chuyển về trạng thái khác để sửa đổi."))
        return super(ProductPricelist, self).write(vals)
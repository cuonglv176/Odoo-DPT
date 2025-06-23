from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import calendar


class CreateInterestCalculationWizard(models.TransientModel):
    _name = 'create.interest.calculation.wizard'
    _description = 'Create Interest Calculation Wizard'

    partner_ids = fields.Many2many(
        'res.partner',
        string='Customers',
        domain=[('is_company', '=', True), ('customer_rank', '>', 0)],
        help="Leave empty to create for all customers with overdue amounts"
    )

    period_start = fields.Date(
        string='Period Start',
        required=True,
        default=lambda self: datetime.now().replace(day=1).date()
    )

    period_end = fields.Date(
        string='Period End',
        required=True,
        default=lambda self: (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    )

    calculation_date = fields.Date(
        string='Calculation Date',
        default=fields.Date.today,
        required=True
    )

    auto_calculate = fields.Boolean(
        string='Auto Calculate Interest',
        default=True,
        help="Automatically calculate interest after creation"
    )

    only_overdue = fields.Boolean(
        string='Only Customers with Overdue',
        default=True,
        help="Only create calculations for customers with overdue amounts"
    )

    def action_create_calculations(self):
        """Tạo bảng tính lãi"""
        # Xác định danh sách khách hàng
        if self.partner_ids:
            partners = self.partner_ids
        else:
            domain = [('is_company', '=', True), ('customer_rank', '>', 0)]
            if self.only_overdue:
                domain.append(('overdue_amount', '>', 0))
            partners = self.env['res.partner'].search(domain)

        if not partners:
            raise UserError(_("No customers found matching the criteria."))

        created_records = self.env['interest.calculation']

        for partner in partners:
            # Kiểm tra xem đã có bản ghi cho kỳ này chưa
            existing = self.env['interest.calculation'].search([
                ('partner_id', '=', partner.id),
                ('period_start', '=', self.period_start),
                ('period_end', '=', self.period_end)
            ])

            if existing:
                continue  # Bỏ qua nếu đã có

            # Tạo bản ghi mới
            record = self.env['interest.calculation'].create({
                'partner_id': partner.id,
                'calculation_date': self.calculation_date,
                'period_start': self.period_start,
                'period_end': self.period_end,
            })

            created_records |= record

        # Tự động tính toán nếu được chọn
        if self.auto_calculate:
            created_records.action_calculate_interest()

        if not created_records:
            raise UserError(_("No new interest calculations were created. Records may already exist for this period."))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Created Interest Calculations'),
            'res_model': 'interest.calculation',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', created_records.ids)],
            'context': {
                'search_default_calculated': 1 if self.auto_calculate else 0,
                'search_default_draft': 0 if self.auto_calculate else 1
            }
        }

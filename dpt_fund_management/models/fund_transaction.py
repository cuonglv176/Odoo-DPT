# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class DptFundTransaction(models.Model):
    _name = 'dpt.fund.transaction'
    _description = 'Giao dịch Quỹ'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char('Mô tả', required=True, tracking=True)
    date = fields.Date('Ngày giao dịch', required=True, default=fields.Date.context_today, tracking=True)
    fund_account_id = fields.Many2one('dpt.fund.account', string='Tài khoản quỹ',
                                      required=True, tracking=True)

    transaction_type = fields.Selection([
        ('income', 'Thu'),
        ('expense', 'Chi')
    ], string='Loại giao dịch', required=True, tracking=True)

    amount = fields.Monetary('Số tiền', currency_field='currency_id', required=True, tracking=True)
    currency_id = fields.Many2one('res.currency', string='Tiền tệ',
                                  related='fund_account_id.currency_id', store=True)

    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Đã xác nhận'),
        ('posted', 'Đã ghi sổ')
    ], string='Trạng thái', default='draft', tracking=True)
    import_source = fields.Selection([
        ('manual', 'Nhập Thủ Công'),
        ('bank_excel', 'Import Excel Ngân Hàng'),
        ('api', 'API Ngân Hàng'),
    ], string='Nguồn Dữ Liệu', default='manual')

    import_reference = fields.Char('Mã Import', help="Mã tham chiếu từ file import")

    # Accounting fields
    debit_account_id = fields.Many2one('account.account', string='Tài khoản nợ')
    credit_account_id = fields.Many2one('account.account', string='Tài khoản có')
    journal_entry_id = fields.Many2one('account.move', string='Bút toán', readonly=True)

    # Exchange rate fields
    exchange_rate_id = fields.Many2one('dpt.exchange.rate', string='Tỷ giá')
    original_currency_id = fields.Many2one('res.currency', string='Tiền tệ gốc')
    original_amount = fields.Monetary('Số tiền gốc', currency_field='original_currency_id')

    @api.constrains('amount')
    def _check_amount_positive(self):
        for record in self:
            if record.amount <= 0:
                raise ValidationError("Số tiền phải lớn hơn 0!")

    @api.constrains('debit_account_id', 'credit_account_id', 'transaction_type')
    def _check_accounts(self):
        for record in self:
            if record.transaction_type == 'expense' and not record.debit_account_id:
                raise ValidationError("Giao dịch chi phải có tài khoản nợ!")
            if record.transaction_type == 'income' and not record.credit_account_id:
                raise ValidationError("Giao dịch thu phải có tài khoản có!")

    def action_confirm(self):
        """Xác nhận giao dịch"""
        for record in self:
            if record.state != 'draft':
                raise UserError("Chỉ có thể xác nhận giao dịch ở trạng thái Nháp!")
            record.state = 'confirmed'

    def action_post(self):
        """Ghi sổ giao dịch"""
        for record in self:
            if record.state != 'confirmed':
                raise UserError("Chỉ có thể ghi sổ giao dịch đã được xác nhận!")

            # Tạo bút toán kế toán
            record._create_journal_entry()
            record.state = 'posted'

    def _create_journal_entry(self):
        """Tạo bút toán kế toán"""
        self.ensure_one()

        if not self.fund_account_id.account_id:
            raise UserError(f"Quỹ {self.fund_account_id.name} chưa được cấu hình tài khoản kế toán!")

        # Chuẩn bị dữ liệu bút toán
        move_vals = {
            'move_type': 'entry',
            'date': self.date,
            'ref': self.name,
            'journal_id': self._get_default_journal().id,
            'line_ids': []
        }

        # Tạo dòng bút toán
        if self.transaction_type == 'income':
            # Thu tiền: Nợ quỹ, Có tài khoản thu
            move_vals['line_ids'].extend([
                (0, 0, {
                    'name': self.name,
                    'account_id': self.fund_account_id.account_id.id,
                    'debit': self.amount,
                    'credit': 0.0,
                    'currency_id': self.currency_id.id,
                }),
                (0, 0, {
                    'name': self.name,
                    'account_id': self.credit_account_id.id,
                    'debit': 0.0,
                    'credit': self.amount,
                    'currency_id': self.currency_id.id,
                })
            ])
        else:  # expense
            # Chi tiền: Nợ tài khoản chi, Có quỹ
            move_vals['line_ids'].extend([
                (0, 0, {
                    'name': self.name,
                    'account_id': self.debit_account_id.id,
                    'debit': self.amount,
                    'credit': 0.0,
                    'currency_id': self.currency_id.id,
                }),
                (0, 0, {
                    'name': self.name,
                    'account_id': self.fund_account_id.account_id.id,
                    'debit': 0.0,
                    'credit': self.amount,
                    'currency_id': self.currency_id.id,
                })
            ])

        # Tạo và ghi sổ bút toán
        move = self.env['account.move'].create(move_vals)
        move.action_post()

        self.journal_entry_id = move.id

    def _get_default_journal(self):
        """Lấy nhật ký mặc định"""
        journal = self.env['account.journal'].search([
            ('type', '=', 'general'),
            ('company_id', '=', self.env.company.id)
        ], limit=1)

        if not journal:
            raise UserError("Không tìm thấy nhật ký tổng hợp!")

        return journal

    def action_view_journal_entry(self):
        """Xem bút toán kế toán"""
        self.ensure_one()
        if not self.journal_entry_id:
            raise UserError("Giao dịch chưa có bút toán kế toán!")

        return {
            'type': 'ir.actions.act_window',
            'name': 'Bút toán kế toán',
            'res_model': 'account.move',
            'res_id': self.journal_entry_id.id,
            'view_mode': 'form',
            'target': 'current'
        }

    @api.model
    def create(self, vals):
        # Auto generate name if not provided
        if not vals.get('name'):
            transaction_type = vals.get('transaction_type', '')
            if transaction_type == 'income':
                prefix = 'THU'
            else:
                prefix = 'CHI'

            sequence = self.env['ir.sequence'].next_by_code('dpt.fund.transaction') or '001'
            vals['name'] = f'{prefix}/{sequence}'

        return super().create(vals)

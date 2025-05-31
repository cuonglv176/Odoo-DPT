from odoo import models, fields, api
from odoo.exceptions import ValidationError


class DptPendingTransfer(models.Model):
    _name = 'dpt.pending.transfer'
    _description = 'Tiền đang chuyển'
    _inherit = ['mail.thread']
    _order = 'date_sent desc'

    name = fields.Char('Mã giao dịch', compute='_compute_name', store=True)
    transfer_id = fields.Many2one('dpt.fund.transfer', 'Lệnh chuyển tiền', required=True, tracking=True)

    amount = fields.Float('Số tiền', required=True, tracking=True)
    currency_id = fields.Many2one('res.currency', 'Tiền tệ', required=True, tracking=True)

    date_sent = fields.Date('Ngày gửi', required=True, tracking=True)
    date_received = fields.Date('Ngày nhận', tracking=True)
    expected_date = fields.Date('Ngày dự kiến nhận', compute='_compute_expected_date', store=True)

    days_pending = fields.Integer('Số ngày chờ', compute='_compute_days_pending', store=True)
    is_overdue = fields.Boolean('Quá hạn', compute='_compute_is_overdue', store=True)

    state = fields.Selection([
        ('pending', 'Đang chuyển'),
        ('received', 'Đã nhận'),
        ('lost', 'Mất tiền'),
        ('cancelled', 'Đã hủy')
    ], default='pending', tracking=True)

    # Thông tin ngân hàng
    bank_reference = fields.Char('Mã tham chiếu ngân hàng')
    bank_fee = fields.Float('Phí ngân hàng')

    notes = fields.Text('Ghi chú')

    @api.depends('transfer_id')
    def _compute_name(self):
        for record in self:
            if record.transfer_id:
                record.name = f"PENDING-{record.transfer_id.name}"
            else:
                record.name = "Tiền đang chuyển"

    @api.depends('date_sent', 'currency_id')
    def _compute_expected_date(self):
        for record in self:
            if record.date_sent:
                # VND -> CNY: 1-2 ngày, CNY -> VND: 2-3 ngày
                if record.currency_id.name == 'VND':
                    days_to_add = 2
                else:
                    days_to_add = 3
                record.expected_date = record.date_sent + fields.timedelta(days=days_to_add)
            else:
                record.expected_date = False

    @api.depends('date_sent', 'date_received', 'state')
    def _compute_days_pending(self):
        for record in self:
            if record.state == 'pending' and record.date_sent:
                record.days_pending = (fields.Date.today() - record.date_sent).days
            elif record.state == 'received' and record.date_sent and record.date_received:
                record.days_pending = (record.date_received - record.date_sent).days
            else:
                record.days_pending = 0

    @api.depends('expected_date', 'state')
    def _compute_is_overdue(self):
        for record in self:
            if record.state == 'pending' and record.expected_date:
                record.is_overdue = fields.Date.today() > record.expected_date
            else:
                record.is_overdue = False

    def action_mark_received(self):
        """Đánh dấu đã nhận tiền"""
        self.state = 'received'
        self.date_received = fields.Date.today()
        if self.transfer_id:
            self.transfer_id.action_confirm_received()

    def action_mark_lost(self):
        """Đánh dấu mất tiền"""
        self.state = 'lost'
        # Tạo giao dịch ghi nhận mất tiền
        self._create_loss_transaction()

    def _create_loss_transaction(self):
        """Tạo giao dịch ghi nhận mất tiền"""
        loss_account = self.env['account.account'].search([('code', '=', '642')], limit=1)
        if not loss_account:
            raise ValidationError('Không tìm thấy tài khoản chi phí mất tiền (642)!')

        # Tạo giao dịch ghi nhận mất tiền
        loss_transaction = self.env['dpt.fund.transaction'].create({
            'name': f'Mất tiền chuyển - {self.transfer_id.name}',
            'date': fields.Date.today(),
            'fund_account_id': self.transfer_id.from_fund_id.id,
            'amount': self.amount,
            'transaction_type': 'expense',
            'debit_account_id': loss_account.id,
        })
        loss_transaction.action_confirm()
        loss_transaction.action_post()

    @api.model
    def check_overdue_transfers(self):
        """Cron job kiểm tra tiền chuyển quá hạn"""
        overdue_transfers = self.search([
            ('state', '=', 'pending'),
            ('is_overdue', '=', True)
        ])

        for transfer in overdue_transfers:
            # Gửi thông báo
            transfer.message_post(
                body=f"Cảnh báo: Tiền chuyển {transfer.name} đã quá hạn {transfer.days_pending} ngày!",
                subject="Cảnh báo tiền chuyển quá hạn"
            )

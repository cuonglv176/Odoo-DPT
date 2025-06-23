from odoo import models, fields, api, _
from odoo.osv.expression import AND, OR
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError


def number_to_vietnamese(n):
    units = ["", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín"]
    teens = ["mười", "mười một", "mười hai", "mười ba", "mười bốn", "mười lăm", "mười sáu", "mười bảy", "mười tám",
             "mười chín"]
    tens = ["", "", "hai mươi", "ba mươi", "bốn mươi", "năm mươi", "sáu mươi", "bảy mươi", "tám mươi", "chín mươi"]
    thousands = ["", "nghìn", "triệu", "tỷ"]

    def convert_hundreds(n):
        if n == 0:
            return ""
        elif n < 10:
            return units[n]
        elif n < 20:
            return teens[n - 10]
        elif n < 100:
            return tens[n // 10] + (" " + units[n % 10] if n % 10 != 0 else "")
        else:
            return units[n // 100] + " trăm" + (" " + convert_hundreds(n % 100) if n % 100 != 0 else "")

    if n == 0:
        return "không"

    result = ""
    thousand_counter = 0

    while n > 0:
        if n % 1000 != 0:
            result = convert_hundreds(n % 1000) + " " + thousands[thousand_counter] + " " + result
        n //= 1000
        thousand_counter += 1

    return result.strip()


def convert_currency_to_text(amount):
    whole_part = int(amount)
    fractional_part = int(round((amount - whole_part) * 100))

    whole_part_words = number_to_vietnamese(whole_part)
    fractional_part_words = number_to_vietnamese(fractional_part)

    return f"{whole_part_words} đồng và {fractional_part_words} xu" if fractional_part_words != 'không' else f"{whole_part_words} đồng"


class AccountPaymentType(models.Model):
    _name = 'dpt.account.payment.type'

    name = fields.Char(string='Name')
    is_bypass = fields.Boolean(string='Bỏ qua người quản lý', default=False)
    is_ke_toan_truong = fields.Boolean(string='Kế toán trưởng duyệt cuối', default=False)
    rule_ids = fields.One2many('dpt.account.payment.type.rule', 'type_id', string='Rules')
    default_partner_id = fields.Many2one('res.partner', "Default Partner")
    is_cn_payment = fields.Boolean('Là thanh toán phí nội địa TQ')
    show_transfer_money = fields.Boolean('Hiển thị Phí chuyển tiền')
    show_refund_date = fields.Boolean('Hiển thị Ngày hoàn ứng')
    show_user_detail = fields.Boolean('Hiển thị Chi tiết User')
    show_journal = fields.Boolean('Hiển thị Sổ nhật ký')


class AccountPaymentTypeRule(models.Model):
    _name = 'dpt.account.payment.type.rule'
    _order = 'sequence'

    sequence = fields.Integer(string='Sequence', default=1)
    department_id = fields.Many2one('hr.department', string='Department Request')
    type_id = fields.Many2one('dpt.account.payment.type')
    user_id = fields.Many2one('res.users', string='User Approve')
    type_compare = fields.Selection([('higher', 'Higher'),
                                     ('equal', 'Equal'),
                                     ('lower', 'Lower')], string='Type Compare', default='equal')
    value_compare = fields.Float(string='Value Compare')


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    code = fields.Char(string='Payment Code', default='NEW', copy=False, index=True, tracking=True)
    user_id = fields.Many2one('res.users', string='User Request', default=lambda self: self.env.user, tracking=True)
    department_id = fields.Many2one('hr.department', string='Department Request', tracking=True)
    type_id = fields.Many2one('dpt.account.payment.type', string='Type Request')
    purchase_id = fields.Many2one('purchase.order', string='Purchase')
    approval_id = fields.Many2one('approval.request', string='Approval Payment Request')
    request_status = fields.Selection([
        ('new', 'To Submit'),
        ('pending', 'Submitted'),
        ('approved', 'Approved'),
        ('refused', 'Refused'),
        ('cancel', 'Cancel'),
    ], string='Status approval', default="new", related="approval_id.request_status")
    service_sale_ids = fields.Many2many('dpt.sale.service.management', string='Sale lines')
    service_sale_id = fields.Many2one('dpt.sale.service.management', string='Sale line')
    from_po = fields.Boolean()
    from_so = fields.Boolean()
    payment_user_type = fields.Selection([
        ('customer', 'Khách hàng'),
        ('company', 'Công ty'),
    ], string='Bên thanh toán')
    payment_user = fields.Selection([
        ('ltv', 'LTV'),
        ('dpt', 'DPT'),
    ], string='Pháp nhân thanh toán')
    active = fields.Boolean(default=True)
    detail_ids = fields.One2many('dpt.account.payment.detail', 'payment_id', string='Chi tiết thanh toán Dịch vụ')
    detail_product_ids = fields.One2many('dpt.account.payment.detail', 'payment_product_id',
                                         string='Chi tiết thanh toán Sản phẩm')
    last_rate_currency = fields.Float('Last Rate Currency')
    acc_number = fields.Char(related="partner_bank_id.acc_number")
    acc_holder_name = fields.Char(related="partner_bank_id.acc_holder_name")
    bank_id = fields.Many2one(related="partner_bank_id.bank_id")
    amount_in_text = fields.Char('Amount in Text', compute="_compute_amount_in_text")
    refund_date = fields.Date(string='Ngày hoàn ứng')
    amount = fields.Monetary(currency_field='company_currency_id')
    amount_request = fields.Monetary(string='Số tiền ngoại tệ', currency_field='currency_id')
    user_view_ids = fields.Many2many('res.users', compute="get_list_users_view", store=True)
    payment_due = fields.Datetime(string='Thời hạn thanh toán')
    journal_type = fields.Selection([
        ('sale', 'Sales'),
        ('purchase', 'Purchase'),
        ('cash', 'Cash'),
        ('bank', 'Bank'),
        ('general', 'Miscellaneous'),
    ], required=True,
        inverse='_inverse_type',
        help="Select 'Sale' for customer invoices journals.\n" \
             "Select 'Purchase' for vendor bills journals.\n" \
             "Select 'Cash' or 'Bank' for journals that are used in customer or vendor payments.\n" \
             "Select 'General' for miscellaneous operations journals.", related="journal_id.type")
    lock_status = fields.Selection([
        ('open', 'Open'),
        ('locked', 'Locked'),
    ], default='open', compute="_compute_look_status")
    dpt_user_partner_id = fields.Many2one('res.partner', string='User Khách', domain=[('dpt_user_name', '!=', False)])
    # dpt_user_name = fields.Char(string='User Khách')
    dpt_type_of_partner = fields.Selection([('employee', 'Nhân viên'),
                                            ('customer', 'Khách hàng'),
                                            ('vendor', 'Nhà cung cấp'),
                                            ('shipping_address', 'Địa chỉ giao hàng'),
                                            ('payment_address', 'Địa chỉ thanh toán'),
                                            ('other', 'Khác')], string='Loại liên hệ')

    hide_in_cn_payment = fields.Boolean('Ẩn với thanh toán phí nội địa TQ', compute="compute_hide_in_cn_payment")
    show_transfer_money = fields.Boolean(related="type_id.show_transfer_money")
    show_refund_date = fields.Boolean(related="type_id.show_refund_date")
    show_user_detail = fields.Boolean(related="type_id.show_user_detail")
    show_journal = fields.Boolean(related="type_id.show_journal")
    transfer_amount = fields.Float('Phí chuyển tiền')

    @api.depends('type_id', 'type_id.is_cn_payment')
    def compute_hide_in_cn_payment(self):
        for item in self:
            if not item.type_id.is_cn_payment:
                item.hide_in_cn_payment = False
            else:
                show_groups = ["dpt_security.group_dpt_accountant", "dpt_security.group_dpt_accountant",
                               "dpt_security.group_dpt_ke_toan_truong", "dpt_security.group_dpt_ke_toan_tong_hop",
                               "dpt_security.group_dpt_ke_toan_hang_hoa", "dpt_security.group_dpt_director"]
                if self.env.user.id == item.create_uid:
                    item.hide_in_cn_payment = True
                if any([self.env.user.has_group(group) for group in show_groups]):
                    item.hide_in_cn_payment = False
                else:
                    item.hide_in_cn_payment = True

    def _compute_look_status(self):
        for rec in self:
            lock_status = 'open'
            if self.env.user != rec.create_uid or rec.request_status == 'approved':
                lock_status = 'locked'
            accountant_groups = ["dpt_security.group_dpt_accountant", "dpt_security.group_dpt_accountant",
                                 "dpt_security.group_dpt_ke_toan_truong", "dpt_security.group_dpt_ke_toan_tong_hop",
                                 "dpt_security.group_dpt_ke_toan_hang_hoa"]
            if any([self.env.user.has_group(item) for item in accountant_groups]):
                lock_status = 'open'
            rec.lock_status = lock_status

    @api.onchange('partner_id')
    def onchange_dpt_type_of_partner(self):
        if self.partner_id:
            self.dpt_type_of_partner = self.partner_id.dpt_type_of_partner

    @api.onchange('sale_id')
    def onchange_user_partner(self):
        if self.sale_id and self.sale_id.partner_id.dpt_user_name:
            self.dpt_user_partner_id = self.sale_id.partner_id

    def un_lock(self):
        if self.env.user.id != self.create_uid:
            raise UserError(f"Chỉ người tạo mới có quyền mở khóa, vui lòng liên hệ {self.create_uid.name}")
        if self.request_status == 'approved':
            raise UserError(f"Đơn đã được duyệt không được sửa")
        self.lock_status = 'open'

    def locked(self):
        self.lock_status = 'locked'

    @api.depends('user_id', 'approval_id', 'approval_id.approver_ids')
    def get_list_users_view(self):
        for rec in self:
            user_view_ids = []
            user_view_ids.append(rec.user_id.id)
            for approver_id in rec.approval_id.approver_ids:
                user_view_ids.append(approver_id.user_id.id)
            rec.user_view_ids = [(6, 0, user_view_ids)]

    @api.onchange('last_rate_currency', 'amount_request', 'transfer_amount', 'transfer_amount_rate')
    def onchange_update_amount(self):
        self.amount = self.amount_request * self.last_rate_currency + self.transfer_amount if self.transfer_amount_rate else self.amount_request * self.last_rate_currency

    @api.depends('amount')
    def _compute_amount_in_text(self):
        for item in self:
            item.amount_in_text = convert_currency_to_text(item.amount)

    @api.onchange('service_sale_id')
    def onchange_service_sale_create_detail(self):
        if self.service_sale_id:
            price = self.service_sale_id.price
            qty = 1 if self.service_sale_id.compute_value == 0 else self.service_sale_id.compute_value
            self.detail_ids = [(0, 0, {
                'service_id': self.service_sale_id.service_id.id,
                'description': '',
                'qty': qty,
                'uom_id': self.service_sale_id.uom_id.id,
                'price': price,
                'price_cny': self.service_sale_id.price_cny,
                'amount_total': price * qty,
            })]

    @api.onchange('purchase_id')
    def onchange_create_detail(self):
        if self.purchase_id:
            detail_ids_records = []
            detail_product_ids_records = []
            self.detail_product_ids = None
            self.detail_ids = None
            for order_line in self.purchase_id.order_line:
                price_cny = 0
                price = 0
                if self.purchase_id.currency_id.name != 'VND':
                    price_cny = order_line.price_unit
                    # price = order_line.price_unit * self.purchase_id.currency_id.rate
                    price = order_line.price_unit * self.purchase_id.last_rate_currency
                else:
                    price = order_line.price_unit
                detail_product_ids_records.append((0, 0, {
                    'product_id': order_line.product_id.id,
                    'description': order_line.name,
                    'qty': order_line.product_qty,
                    'uom_id': order_line.product_uom.id,
                    'price': price,
                    'price_cny': price_cny,
                    'amount_total': price * order_line.product_qty,

                }))
            self.detail_product_ids = detail_product_ids_records
            for sale_service_id in self.purchase_id.sale_service_ids:
                price = 0
                if sale_service_id.price_cny != 0:
                    # price = sale_service_id.price_cny * sale_service_id.currency_cny_id.rate
                    price = sale_service_id.price_cny * sale_service_id.purchase_id.last_rate_currency
                else:
                    price = sale_service_id.price
                if sale_service_id.qty == 0:
                    qty = 1
                else:
                    qty = sale_service_id.qty
                detail_ids_records.append((0, 0, {
                    'service_id': sale_service_id.service_id.id,
                    'description': '',
                    'qty': qty,
                    'uom_id': sale_service_id.uom_id.id,
                    'price': price,
                    'price_cny': sale_service_id.price_cny,
                    'amount_total': price * qty,
                }))
            self.detail_ids = detail_ids_records

    def send_payment_request_request(self):
        category_id = self.env['approval.category'].search([('sequence_code', '=', 'DNTT')])
        if not category_id:
            raise ValidationError(_("Please config category approval change price (DNTT)"))
        create_values = {
            'request_owner_id': self.env.user.id,
            'category_id': category_id.id,
            # 'sale_id': self.id,
            'payment_id': self.id,
            'date': datetime.now(),
        }
        approval_id = self.env['approval.request'].create(create_values)
        approval_id._compute_approver_ids()
        list_approver = self._compute_approver_list()
        if list_approver:
            approval_id.approver_ids = list_approver
        approval_id.action_confirm()
        self.approval_id = approval_id
        view_id = self.env.ref('approvals.approval_request_view_form').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'approval.request',
            'name': _('Approval request'),
            'view_mode': 'form',
            'res_id': approval_id.id,
            'views': [[view_id, 'form']],
        }

    @api.onchange('type_id')
    def onchange_type_id(self):
        if self.type_id:
            self.partner_id = self.type_id.default_partner_id

    def _compute_approver_list(self):
        list_approver = []
        list_exist = []
        for rec in self:
            sequence = 10
            sorted_rules = rec.type_id.rule_ids.sorted(key=lambda r: r.sequence)
            for r in sorted_rules:
                if r.user_id.id in list_exist:
                    continue
                diff_value = rec.amount
                required = True
                if r.type_compare == 'equal' and diff_value == r.value_compare:
                    required = True
                elif r.type_compare == 'higher' and diff_value > 0 and diff_value >= r.value_compare:
                    required = True
                elif r.type_compare == 'lower' and diff_value < 0 and abs(diff_value) >= r.value_compare:
                    required = True
                list_approver.append((0, 0, {
                    'sequence': sequence,
                    'user_id': r.user_id.id,
                    'required': required
                }))
                list_exist.append(r.user_id.id)
                sequence += 1
        return list_approver

    @api.onchange('user_id')
    def onchange_user_get_department(self):
        self.department_id = self.user_id.department_id

    def _generate_account_code(self):
        sequence = self.env['ir.sequence'].next_by_code('account.payment') or '00'
        return f'{sequence}'

    @api.model
    def create(self, vals):
        if vals.get('code', 'NEW') == 'NEW':
            vals['code'] = self._generate_account_code()
        res = super(AccountPayment, self).create(vals)
        return res

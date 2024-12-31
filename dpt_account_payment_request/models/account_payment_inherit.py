from odoo import models, fields, api, _
from odoo.osv.expression import AND, OR
from datetime import datetime
from odoo.exceptions import ValidationError


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
    rule_ids = fields.One2many('dpt.account.payment.type.rule', 'type_id', string='Rules')


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
        if self.sale_id:
            create_values.update({

            })
        approval_id = self.env['approval.request'].create(create_values)
        list_approver = self._compute_approver_list()
        if list_approver:
            approval_id.approver_ids = None
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

    def _compute_approver_list(self):
        list_approver = []
        list_exist = []
        for rec in self:
            for r in rec.type_id.rule_ids:
                if r.user_id.id in list_exist:
                    continue
                diff_value = rec.amount
                if r.type_compare == 'equal' and diff_value == 0:
                    required = True
                elif r.type_compare == 'higher' and diff_value > 0 and diff_value >= r.value_compare:
                    required = True
                elif r.type_compare == 'lower' and diff_value < 0 and abs(diff_value) >= r.value_compare:
                    required = True
                else:
                    required = False
                if not required:
                    continue
                list_approver.append((0, 0, {
                    'sequence': r.sequence,
                    'user_id': r.user_id.id,
                    'required': required
                }))
                list_exist.append(r.user_id.id)
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
        return super(AccountPayment, self).create(vals)

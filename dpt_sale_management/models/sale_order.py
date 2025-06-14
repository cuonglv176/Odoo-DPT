from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError
import xlrd, xlwt
import xlsxwriter
import base64
import io as stringIOModule
from odoo.modules.module import get_module_resource
import logging

_logger = logging.getLogger(__name__)
COLUMN = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q']

SALE_ORDER_STATE = [
    ('draft', "Quotation"),
    ('wait_price', "Wait Price"),
    ('sent', "Quotation Sent"),
    ('sale', "Sales Order"),
    ('cancel', "Cancelled"),
]


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # re-define
    state = fields.Selection(
        selection=SALE_ORDER_STATE,
        string="Status",
        readonly=True, copy=False, index=True,
        tracking=3,
        default='draft')

    service_combo_ids = fields.One2many('dpt.sale.order.service.combo', 'sale_id', string='Combo dịch vụ thực tế',
                                        inverse='onchange_get_fields_form_combo_service',
                                        tracking=True)
    sale_service_ids = fields.One2many('dpt.sale.service.management', 'sale_id', string='Service thực tế',
                                       tracking=True,
                                       inverse='onchange_get_fields_form_combo_service')

    planned_service_combo_ids = fields.One2many('dpt.sale.order.service.combo', 'planned_sale_id',
                                                inverse='onchange_get_fields_form_combo_service',
                                                string='Combo dịch vụ dự kiến',
                                                tracking=True)
    planned_sale_service_ids = fields.One2many('dpt.sale.service.management', 'planned_sale_id',
                                               string='Service dự kiến', tracking=True,
                                               inverse='onchange_get_fields_form_combo_service')
    settle_by = fields.Selection([
        ('planned', 'Tất toán theo dự kiến'),
        ('actual', 'Tất toán theo thực tế')
    ], string='Phương thức tất toán', default='actual', tracking=True,
        help='Chọn phương thức tất toán theo dự kiến hoặc thực tế')
    fields_ids = fields.One2many('dpt.sale.order.fields', 'sale_id', string='Fields')
    service_total_untax_amount = fields.Float(compute='_compute_service_amount')
    service_tax_amount = fields.Float(compute='_compute_service_amount')
    service_total_amount = fields.Float(compute='_compute_service_amount')
    # Nuevo campo para el total planificado
    planned_service_total_amount = fields.Float(string='Tổng dự kiến', compute='_compute_planned_service_amount')

    update_pricelist = fields.Boolean('Update Pricelist')
    show_action_calculation = fields.Boolean('Show Action Calculation', compute='compute_show_action_calculation')
    weight = fields.Float('Weight')
    volume = fields.Float('Volume')
    type_so_route = fields.Selection([('office_route', 'Office Route'),
                                      ('unoffice_route', 'Unoffice Route')], string='Type SO Route')
    line_transfer = fields.Selection([('road', 'Road'),
                                      ('sea', 'Sea'),
                                      ('flying', 'Flying')], string='Line Transfer')
    employee_sale = fields.Many2one('hr.employee', string='Employee Sale')
    employee_cs = fields.Many2one('hr.employee', string='Employee CS')
    times_of_quotation = fields.Integer(default=0, string='Số lần báo giá')
    is_quotation = fields.Boolean(default=False, compute='compute_show_is_quotation')
    active = fields.Boolean('Active', default=True)
    confirm_service_ticket = fields.Boolean('Xác nhận tạo ticket cho dịch vụ', default=False,
                                            help='Đánh dấu để tạo ticket cho tất cả dịch vụ')
    quote_type = fields.Selection([
        ('thuong', 'Báo giá thường'),
        ('dac_biet', 'Báo giá đặc biệt')
    ], string='Loại báo giá', default='thuong', tracking=True)

    @api.depends('planned_sale_service_ids.amount_total')
    def _compute_planned_service_amount(self):
        for record in self:
            record.planned_service_total_amount = sum(record.planned_sale_service_ids.mapped('amount_total')) + sum(
                record.planned_service_combo_ids.mapped('amount_total'))

    @api.onchange('sale_service_ids', 'planned_sale_service_ids', 'service_combo_ids', 'planned_service_combo_ids')
    def onchange_get_fields_form_combo_service(self):
        fields_dict = {}
        sale_order = self.env['sale.order'].browse(self.origin) if self.origin else False
        list_exist = sale_order.fields_ids.fields_id.ids if sale_order else []
        list_onchange = [item.fields_id.id for item in self.fields_ids]
        # Xử lý tất cả các dịch vụ và combo
        all_items = []
        # 1. Dịch vụ thực tế (ưu tiên cao nhất)
        for sale_service in self.sale_service_ids:
            if sale_service and sale_service.service_id:
                all_items.append(('service', sale_service, sale_service.service_id, 'actual'))
        # 2. Combo dịch vụ thực tế (ưu tiên thứ hai)
        for combo in self.service_combo_ids:
            if combo and combo.combo_id:
                all_items.append(('combo', combo, combo.combo_id, 'actual'))
        # 3. Dịch vụ dự kiến (ưu tiên thứ ba)
        actual_service_ids = set(service.service_id.id for service in self.sale_service_ids if service.service_id)
        for planned_service in self.planned_sale_service_ids:
            if planned_service and planned_service.service_id and planned_service.service_id.id not in actual_service_ids:
                all_items.append(('service', planned_service, planned_service.service_id, 'planned'))
        # 4. Combo dịch vụ dự kiến (ưu tiên thấp nhất)
        actual_combo_ids = set(combo.combo_id.id for combo in self.service_combo_ids if combo.combo_id)
        for planned_combo in self.planned_service_combo_ids:
            if planned_combo and planned_combo.combo_id and planned_combo.combo_id.id not in actual_combo_ids:
                all_items.append(('combo', planned_combo, planned_combo.combo_id, 'planned'))
        # Duyệt qua từng mục để xử lý
        for item_type, item, model_item, item_status in all_items:
            required_fields = model_item.required_fields_ids
            for req_field in required_fields:
                # Nếu req_field không tồn tại, bỏ qua
                if not req_field:
                    continue
                # Tạo key duy nhất để tránh trùng lặp
                # Sử dụng kết hợp giữa field_id và model_id (service hoặc combo)
                field_key = (req_field.id, model_item.id, item_type)
                # Nếu đã xử lý field này cho item này (từ thực tế), bỏ qua
                if field_key in fields_dict and item_status == 'planned':
                    continue
                rec = None
                # Kiểm tra nếu trường đã tồn tại với cùng fields_id và model_id
                if item_type == 'service':
                    existing_field = self.fields_ids.filtered(
                        lambda f: f.fields_id.id == req_field.id and f.service_id.id == model_item.id
                    )
                else:  # combo
                    existing_field = self.fields_ids.filtered(
                        lambda f: f.fields_id.id == req_field.id and f.combo_id.id == model_item.id
                    )
                if existing_field:
                    rec = {
                        'sequence': 1 if existing_field.fields_id.type == 'required' else 0,
                        'fields_id': req_field.id,
                        'sale_id': self.id,
                        'value_char': existing_field.value_char,
                        'value_integer': existing_field.value_integer,
                        'value_date': existing_field.value_date,
                        'selection_value_id': existing_field.selection_value_id.id if existing_field.selection_value_id else False,
                    }
                    # Thêm service hoặc combo vào tùy theo loại item
                    if item_type == 'service':
                        rec.update({
                            'sale_service_id': item.id,
                            'service_id': model_item.id,
                        })
                    else:  # combo
                        rec.update({
                            'combo_id': model_item.id,
                        })
                # Ưu tiên lấy dữ liệu từ sale order nếu trường tồn tại trong đó
                elif req_field.id in list_exist and sale_order:
                    for field_data in sale_order.fields_ids:
                        if field_data.fields_id.id == req_field.id:
                            rec = {
                                'sequence': 1 if field_data.fields_id.type == 'required' else 0,
                                'fields_id': req_field.id,
                                'sale_id': self.id,
                                'value_char': field_data.value_char,
                                'value_integer': field_data.value_integer,
                                'value_date': field_data.value_date,
                                'selection_value_id': field_data.selection_value_id.id if field_data.selection_value_id else False,
                            }
                            # Thêm service hoặc combo vào tùy theo loại item
                            if item_type == 'service':
                                rec.update({
                                    'sale_service_id': item.id,
                                    'service_id': model_item.id,
                                })
                            else:  # combo
                                rec.update({
                                    'combo_id': model_item.id,
                                })
                            break
                # Nếu không có trong sale order, kiểm tra từ dữ liệu của record hiện tại
                elif req_field.id in list_onchange:
                    for field_data in self.fields_ids:
                        if field_data.fields_id.id == req_field.id:
                            rec = {
                                'sequence': 1 if field_data.fields_id.type == 'required' else 0,
                                'fields_id': req_field.id,
                                'sale_id': self.id,
                                'value_char': field_data.value_char,
                                'value_integer': field_data.value_integer,
                                'value_date': field_data.value_date,
                                'selection_value_id': field_data.selection_value_id.id if field_data.selection_value_id else False,
                            }
                            # Thêm service hoặc combo vào tùy theo loại item
                            if item_type == 'service':
                                rec.update({
                                    'sale_service_id': item.id,
                                    'service_id': model_item.id,
                                })
                            else:  # combo
                                rec.update({
                                    'combo_id': model_item.id,
                                })
                            break
                # Nếu không có dữ liệu từ các nguồn trên, tạo giá trị mặc định
                if not rec:
                    rec = {
                        'sequence': 1 if req_field.type == 'required' else 0,
                        'fields_id': req_field.id,
                        'sale_id': self.id,
                    }
                    # Thêm service hoặc combo vào tùy theo loại item
                    if item_type == 'service':
                        rec.update({
                            'sale_service_id': item.id,
                            'service_id': model_item.id,
                        })
                    else:  # combo
                        rec.update({
                            'combo_id': model_item.id,
                        })
                    default_value = req_field.get_default_value(so=self)
                    if default_value:
                        rec.update(default_value)
                # Lưu vào dictionary, ưu tiên dịch vụ/combo thực tế hơn dự kiến
                if field_key not in fields_dict or item_status == 'actual':
                    fields_dict[field_key] = rec

        # Kết hợp và sắp xếp kết quả
        if fields_dict:
            sorted_vals = sorted(fields_dict.values(), key=lambda x: x["sequence"], reverse=True)
            self.fields_ids = [(5, 0, 0)]  # Xóa dữ liệu cũ
            self.fields_ids = [(0, 0, item) for item in sorted_vals]
        else:
            # Nếu không còn dịch vụ/combo nào thì xóa hết fields_ids
            if not self.sale_service_ids and not self.planned_sale_service_ids and not self.service_combo_ids and not self.planned_service_combo_ids:
                self.fields_ids = [(5, 0, 0)]

        # Gọi hàm cập nhật thêm
        self.onchange_get_data_required_fields()

    @api.onchange('planned_service_combo_ids')
    def onchange_planned_service_combo_ids(self):
        self.service_combo_ids = self.planned_service_combo_ids

    @api.onchange('planned_sale_service_ids')
    def onchange_planned_sale_service_ids(self):
        self.sale_service_ids = self.planned_sale_service_ids

    @api.depends('sale_service_ids', 'sale_service_ids.service_id', 'sale_service_ids.service_id.pricelist_item_ids')
    def compute_show_is_quotation(self):
        for rec in self:
            is_quotation = False
            for sale_service_id in rec.sale_service_ids:
                if not sale_service_id.service_id.pricelist_item_ids:
                    is_quotation = True
            rec.is_quotation = is_quotation

    @api.onchange('order_line')
    def onchange_calculation_tax(self):
        for r in self.sale_service_ids:
            if r.service_id.code in ('SERV-2407-0058', 'SERV-2407-0059', 'SERV-2407-0057'):
                if r.service_id.code == 'SERV-2407-0058':
                    r.price = sum(self.order_line.mapped('import_tax_amount'))
                elif r.service_id.code == 'SERV-2407-0059':
                    r.price = sum(self.order_line.mapped('other_tax_amount'))
                elif r.service_id.code == 'SERV-2407-0057':
                    r.price = sum(self.order_line.mapped('vat_tax_amount'))
                r.amount_total = r.price * r.compute_value

    @api.onchange('partner_id')
    def _onchange_partner_id_user(self):
        if self.partner_id.user_id.id != self._uid:
            self.user_id = self._uid

    @api.onchange('partner_id', 'user_id')
    def onchange_user_id(self):
        self = self.sudo()
        if self.partner_id.user_id:
            self.employee_sale = self.partner_id.user_id.employee_id
        else:
            self.employee_sale = self.user_id.employee_id
        if self.partner_id.cs_user_id:
            self.employee_cs = self.partner_id.cs_user_id.employee_id
        else:
            self.employee_cs = self.user_id.employee_id

    @api.onchange('weight', 'volume', 'order_line')
    def onchange_weight_volume(self):
        for fields_id in self.fields_ids:
            if fields_id.fields_id.default_compute_from == 'weight_in_so' and fields_id.fields_id.fields_type == 'integer':
                fields_id.value_integer = self.weight
            if fields_id.fields_id.default_compute_from == 'volume_in_so' and fields_id.fields_id.fields_type == 'integer':
                fields_id.value_integer = self.volume
            if fields_id.fields_id.default_compute_from == 'declared_price_in_so' and fields_id.fields_id.fields_type == 'integer':
                fields_id.value_integer = sum(self.order_line.mapped('declared_unit_price'))

    @api.model
    def create(self, vals_list):
        res = super(SaleOrder, self).create(vals_list)
        res.check_required_fields()
        res.onchange_calculation_tax()
        res.action_calculation()
        return res

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        self.check_required_fields()
        if self.state != 'sale':
            self.onchange_calculation_tax()
        if vals.get('state') == 'sale':
            self.action_update_fields()
        if 'sale_service_ids' in vals or 'planned_sale_service_ids' in vals or 'service_combo_ids' in vals or 'planned_service_combo_ids' in vals:
            self.action_calculation()
            self.onchange_get_fields_form_combo_service()
        return res

    def action_unlock(self):
        self.with_context(onchange_sale_service_ids=True).locked = False

    def action_lock(self):
        self = self.with_context(onchange_sale_service_ids=True)
        for order in self:
            tx = order.sudo().transaction_ids._get_last()
            if tx and tx.state == 'pending' and tx.provider_id.code == 'custom' and tx.provider_id.custom_mode == 'wire_transfer':
                tx._set_done()
                tx.write({'is_post_processed': True})
        self.locked = True

    def check_required_fields(self):
        for r in self.fields_ids:
            if r.env.context.get('onchange_sale_service_ids', False):
                continue
            if r.fields_id.type == 'required' and r.fields_type == 'integer' and r.value_integer <= 0:
                raise ValidationError(_("Please fill required fields: %s!!!") % r.fields_id.display_name)
            if r.fields_id.type == 'required' and r.fields_type == 'char' and not r.value_char:
                raise ValidationError(_("Please fill required fields: %s!!!") % r.fields_id.display_name)
            if r.fields_id.type == 'required' and r.fields_type == 'date' and not r.value_date:
                raise ValidationError(_("Please fill required fields: %s!!!") % r.fields_id.display_name)
            if r.fields_id.type == 'required' and r.fields_type == 'selection' and not r.selection_value_id:
                raise ValidationError(_("Please fill required fields: %s!!!") % r.fields_id.display_name)

    def get_combo_price_from_pricelist(self, sale_combo_id):
        """Lấy giá combo từ bảng giá"""
        self.ensure_one()
        if not sale_combo_id or not self.partner_id:
            return False
        today = fields.Date.today()

        # Domain chung cho cả hai lần tìm kiếm
        base_domain = [
            ('combo_id', '=', sale_combo_id.combo_id.id),
            ('pricelist_id.state', '=', 'active'),
            '|', ('date_start', '<=', today), ('date_start', '=', False),
            '|', ('date_end', '>=', today), ('date_end', '=', False),
        ]

        # 1. Ưu tiên tìm bảng giá theo khách hàng cụ thể
        partner_domain = base_domain + [('partner_id', '=', self.partner_id.id)]
        combo_pricelist_id = self.env['product.pricelist.item'].search(partner_domain, limit=1)

        # 2. Nếu không có, tìm bảng giá chung (không gán cho khách hàng nào)
        if not combo_pricelist_id:
            general_domain = base_domain + [('partner_id', '=', False)]
            combo_pricelist_id = self.env['product.pricelist.item'].search(general_domain, limit=1)

        if not combo_pricelist_id:
            raise ValidationError(
                _("Combo chưa có bảng giá hoạt động hoặc không tìm thấy bảng giá phù hợp: %s!!!") % sale_combo_id.combo_id.name)

        return combo_pricelist_id

    def _compute_combo_price(self, sale_combo_combo_ids, type='combo'):
        for combo in sale_combo_combo_ids:
            combo_pricelist_id = self.get_combo_price_from_pricelist(combo)
            compute_value = 1
            compute_uom_id = combo_pricelist_id.uom_id
            if not combo_pricelist_id:
                continue
            compute_field_qty_id = self.fields_ids.filtered(
                lambda f: f.using_calculation_price and f.combo_id.id == combo.combo_id.id
                          and f.uom_id.id == combo_pricelist_id.uom_id.id)[:1]
            compute_value = compute_field_qty_id.value_integer

            if combo_pricelist_id.compute_price == 'fixed':
                combo.price = combo_pricelist_id.fixed_price

            elif combo_pricelist_id.compute_price == 'percentage':
                price_base = 0
                if combo_pricelist_id.percent_based_on == 'product_total_amount':
                    price_base = sum(self.order_line.mapped('price_subtotal'))
                elif combo_pricelist_id.percent_based_on == 'declaration_total_amount':
                    price_base = sum(self.order_line.mapped('declared_unit_total'))
                elif combo_pricelist_id.percent_based_on == 'purchase_total_amount':
                    purchase_ids = self.purchase_ids.filtered(lambda po: po.purchase_type == 'external')
                    for order_line in purchase_ids.mapped('order_line'):
                        price_base += order_line.price_subtotal * order_line.order_id.last_rate_currency
                elif combo_pricelist_id.percent_based_on == 'invoice_total_amount':
                    pass
                combo.price = combo_pricelist_id.percent_price * price_base
            elif combo_pricelist_id.compute_price == 'table':
                compute_field_ids = self.fields_ids.filtered(
                    lambda f: f.using_calculation_price and f.combo_id.id == combo.combo_id.id)
                price = 0
                total_amount = 0
                for compute_field_id in compute_field_ids:
                    value_integer = compute_field_id.value_integer
                    if not compute_field_id.value_integer:
                        continue
                    detail_price_ids = combo_pricelist_id.pricelist_table_detail_ids.filtered(
                        lambda ptd: ptd.compute_uom_id.id == compute_field_id.uom_id.id)
                    _logger.info(detail_price_ids)
                    for detail_price_id in detail_price_ids:
                        if detail_price_id.min_value <= compute_field_id.value_integer <= detail_price_id.max_value:
                            if detail_price_id.price_type == 'unit_price':
                                if (detail_price_id.amount * value_integer) > total_amount:
                                    price = detail_price_id.amount
                                    total_amount = detail_price_id.amount * compute_field_id.value_integer
                                    compute_uom_id = detail_price_id.compute_uom_id.id
                                    compute_value = compute_field_id.value_integer
                            else:
                                if (detail_price_id.amount * value_integer) > total_amount:
                                    price = detail_price_id.amount
                                    total_amount = detail_price_id.amount * compute_field_id.value_integer
                                    compute_uom_id = detail_price_id.compute_uom_id.id
                                    compute_value = compute_field_id.value_integer
                            if price < combo_pricelist_id.min_amount:
                                price = combo_pricelist_id.min_amount
                                compute_uom_id = compute_field_id.uom_id.id
                                compute_value = compute_field_id.value_integer
                        else:
                            raise ValidationError(_("Báo giá đã vượt ngưỡng trong bảng giá vui lòng check lại"))

                combo.price = price
                combo.qty = compute_value
            amount_total, amount_planned_total = self._get_service_allin_baogiao()
            if type == 'combo':
                combo.price = combo.price - ((amount_total / combo.qty) if combo.qty else 0)
            if type == 'planned_combo':
                combo.price = combo.price - ((amount_planned_total / combo.qty) if combo.qty else 0)
            combo.compute_uom_id = compute_uom_id

    def _get_service_allin_baogiao(self):
        amount_total = 0
        amount_planned_total = 0
        if self.quote_type == 'dac_biet':
            sale_service_ids = self.sale_service_ids.filtered(lambda sale_service: sale_service.is_bao_giao)
            for sale_service_id in sale_service_ids:
                amount_total += sale_service_id.amount_total
            planned_sale_service_ids = self.planned_sale_service_ids.filtered(
                lambda sale_service: sale_service.is_bao_giao)
            for planned_sale_service_id in planned_sale_service_ids:
                amount_planned_total += planned_sale_service_id.amount_total
        # elif self.quote_type == 'all_in':
        #     sale_service_ids = self.sale_service_ids.filtered(lambda sale_service: sale_service.is_allin)
        #     for sale_service_id in sale_service_ids:
        #         amount_total += sale_service_id.amount_total
        #     planned_sale_service_ids = self.planned_sale_service_ids.filtered(
        #         lambda planned_sale_service: planned_sale_service.is_allin)
        #     for planned_sale_service_id in planned_sale_service_ids:
        #         amount_planned_total += planned_sale_service_id.amount_total
        return amount_total, amount_planned_total

    def _compute_service_price(self, service_ids):
        for sale_service_id in service_ids:
            if sale_service_id.combo_id and sale_service_id.price > 0 and sale_service_id.price_status == 'calculated':
                continue
            if not sale_service_id.uom_id:
                continue
            approved = sale_service_id.approval_id.filtered(
                lambda approval: approval.request_status in ('approved', 'refused'))
            if approved:
                continue
            current_uom_id = sale_service_id.uom_id
            selected_uoms = self.env['uom.uom'].browse([current_uom_id.id]) if current_uom_id else self.env['uom.uom']
            service_price_ids = sale_service_id.service_id.get_active_pricelist(
                partner_id=self.partner_id,
                selected_uoms=selected_uoms
            )
            if current_uom_id:
                service_price_ids = service_price_ids.filtered(
                    lambda sp: sp.uom_id.id == current_uom_id.id and (
                            sp.partner_id and sp.partner_id.id == self.partner_id.id or not sp.partner_id
                    )
                )
            if not service_price_ids:
                continue
            max_price = 0
            price_list_item_id = None
            compute_value = 1
            compute_uom_id = None
            for service_price_id in service_price_ids:
                # Giá cố định
                if service_price_id.compute_price == 'fixed':
                    price = max(service_price_id.currency_id.rate * service_price_id.fixed_price,
                                service_price_id.min_amount)
                    if price > max_price:
                        max_price = price
                        price_list_item_id = service_price_id

                # Giá theo phần trăm
                elif service_price_id.compute_price == 'percentage':
                    price_base = 0

                    # Xác định giá trị cơ sở để tính phần trăm
                    if service_price_id.percent_based_on == 'product_total_amount':
                        price_base = sum(self.order_line.mapped('price_subtotal'))
                    elif service_price_id.percent_based_on == 'declaration_total_amount':
                        price_base = sum(self.order_line.mapped('declared_unit_total'))
                    elif service_price_id.percent_based_on == 'purchase_total_amount':
                        purchase_ids = self.purchase_ids.filtered(lambda po: po.purchase_type == 'external')
                        price_base = 0
                        for order_line in purchase_ids.mapped('order_line'):
                            price_base += order_line.price_subtotal * order_line.order_id.last_rate_currency
                    elif service_price_id.percent_based_on == 'invoice_total_amount':
                        # Tổng giá trị xuất hoá đơn - thêm xử lý ở đây nếu có
                        pass

                    # Tính giá từ phần trăm
                    if price_base:
                        price = max(
                            service_price_id.currency_id.rate * (price_base * service_price_id.percent_price / 100),
                            service_price_id.min_amount)
                        if price and price > max_price:
                            max_price = price
                            price_list_item_id = service_price_id

                # Giá theo bảng
                elif service_price_id.compute_price == 'table':
                    # Tìm các trường để tính giá
                    compute_field_ids = self.fields_ids.filtered(
                        lambda f: f.using_calculation_price and
                                  f.service_id.id == sale_service_id.service_id.id)

                    for compute_field_id in compute_field_ids:
                        # Kiểm tra nếu compute_field_id không có giá trị
                        if not compute_field_id.value_integer:
                            continue

                        # Xử lý giá không tích lũy
                        if not service_price_id.is_accumulated:
                            detail_price_ids = service_price_id.pricelist_table_detail_ids.filtered(
                                lambda ptd: ptd.uom_id.id == compute_field_id.uom_id.id and
                                            compute_field_id.value_integer >= ptd.min_value and
                                            (not ptd.max_value or compute_field_id.value_integer <= ptd.max_value)
                            )

                            for detail_price_id in detail_price_ids:
                                # Tính giá dựa trên kiểu giá (đơn giá hoặc khoảng giá)
                                if detail_price_id.price_type == 'unit_price':
                                    price = compute_field_id.value_integer * detail_price_id.amount
                                else:  # fixed_range
                                    price = detail_price_id.amount

                                # Áp dụng is_price nếu cần
                                if not service_price_id.is_price:
                                    price = detail_price_id.amount

                                price = max(service_price_id.currency_id.rate * price, service_price_id.min_amount)

                                if price > max_price:
                                    max_price = price
                                    price_list_item_id = service_price_id
                                    # Check if the unit is m3 or kg and use the corresponding field from the sale order
                                    uom = self.env['uom.uom'].browse(compute_field_id.uom_id.id)
                                    if uom.name == 'm3' and self.volume:
                                        # Use volume field from sale order
                                        compute_value = self.volume
                                    elif uom.name == 'kg' and self.weight:
                                        # Use weight field from sale order
                                        compute_value = self.weight
                                    else:
                                        # Use the field value as before
                                        compute_value = compute_field_id.value_integer
                                    compute_uom_id = compute_field_id.uom_id.id

                        # Xử lý giá tích lũy
                        else:
                            detail_price_ids = service_price_id.pricelist_table_detail_ids.filtered(
                                lambda ptd: ptd.uom_id.id == compute_field_id.uom_id.id
                            ).sorted(key=lambda r: r.min_value)

                            total_price = 0
                            has_applicable = False

                            for detail_price_id in detail_price_ids:
                                # Bỏ qua nếu giá trị nhỏ hơn min_value
                                if detail_price_id.min_value > compute_field_id.value_integer:
                                    continue

                                has_applicable = True

                                # Tính giá theo khoảng
                                if detail_price_id.max_value:
                                    applicable_value = min(compute_field_id.value_integer,
                                                           detail_price_id.max_value) - detail_price_id.min_value + 1
                                else:
                                    applicable_value = compute_field_id.value_integer - detail_price_id.min_value + 1

                                # Áp dụng giá theo kiểu
                                if detail_price_id.price_type == 'unit_price':
                                    price = applicable_value * detail_price_id.amount
                                else:  # fixed_range
                                    price = detail_price_id.amount

                                # Kiểm tra is_price
                                if not service_price_id.is_price and detail_price_id.price_type == 'fixed_range':
                                    price = detail_price_id.amount

                                total_price += service_price_id.currency_id.rate * price

                            # Chỉ cập nhật nếu có mức giá áp dụng được
                            if has_applicable and max(total_price, service_price_id.min_amount) > max_price:
                                max_price = max(total_price, service_price_id.min_amount)
                                price_list_item_id = service_price_id
                                # Check if the unit is m3 or kg and use the corresponding field from the sale order
                                uom = self.env['uom.uom'].browse(compute_field_id.uom_id.id)
                                if uom.name == 'm3' and self.volume:
                                    # Use volume field from sale order
                                    compute_value = self.volume
                                elif uom.name == 'kg' and self.weight:
                                    # Use weight field from sale order
                                    compute_value = self.weight
                                else:
                                    # Use the field value as before
                                    compute_value = compute_field_id.value_integer
                                compute_uom_id = compute_field_id.uom_id.id

            # Cập nhật trạng thái giá
            price_status = sale_service_id.price_status or 'no_price'
            if sale_service_id.service_id.pricelist_item_ids and price_status == 'no_price':
                price_status = 'calculated'

            # Cập nhật thông tin giá và đơn vị cho dịch vụ
            if price_list_item_id or service_price_ids:
                final_uom_id = price_list_item_id.uom_id.id if price_list_item_id and price_list_item_id.uom_id else (
                    service_price_ids[:1].uom_id.id if service_price_ids and service_price_ids[
                                                                             :1].uom_id else current_uom_id.id
                )
                # Tính giá đơn vị nếu có compute_value
                unit_price = max_price
                if price_list_item_id and price_list_item_id.is_price and compute_value > 0:
                    # Kiểm tra nếu đơn vị là m3 hoặc kg
                    if compute_uom_id:
                        uom = self.env['uom.uom'].browse(compute_uom_id)
                        if uom.name not in ['m3', 'kg']:
                            # Đối với các đơn vị khác, vẫn chia như cũ
                            unit_price = max_price / compute_value
                    else:
                        unit_price = max_price / compute_value

                # Cập nhật vào dịch vụ
                sale_service_id.with_context(from_pricelist=True).write({
                    'uom_id': final_uom_id,
                    'price': unit_price,
                    'qty': compute_value if price_list_item_id and price_list_item_id.is_price else 1,
                    'pricelist_item_id': price_list_item_id.id if price_list_item_id else (
                        service_price_ids[:1].id if service_price_ids else None),
                    'price_in_pricelist': max_price,
                    'compute_value': compute_value,
                    'compute_uom_id': compute_uom_id,
                    'price_status': price_status,
                })

    def action_calculation(self):
        """Tính toán giá dịch vụ dựa trên loại báo giá"""
        # Lọc dịch vụ theo loại báo giá
        combo_ids = self._filter_services_by_quote_type(self.service_combo_ids)
        planned_combo_ids = self._filter_services_by_quote_type(self.planned_service_combo_ids)
        service_ids = self._filter_services_by_quote_type(self.sale_service_ids)
        planned_service_ids = self._filter_services_by_quote_type(self.planned_sale_service_ids)

        # Tính giá cho các dịch vụ đã lọc
        self._compute_combo_price(combo_ids, 'combo')
        self._compute_combo_price(planned_combo_ids, 'planned_combo')
        self._compute_service_price(service_ids)
        self._compute_service_price(planned_service_ids)
        self.onchange_calculation_tax()

    def _filter_services_by_quote_type(self, service_records):
        """
        Lọc dịch vụ dựa trên loại báo giá được chọn

        Args:
            service_records: Recordset dịch vụ cần lọc

        Returns:
            Recordset các dịch vụ phù hợp với loại báo giá
        """
        if not service_records:
            return service_records

        # Với báo giá thường, trả về tất cả dịch vụ
        if self.quote_type == 'thuong':
            return service_records

        filtered_services = self.env[service_records._name]

        for service in service_records:
            service_model = None

            # Xác định dịch vụ từ sale_service hoặc combo
            if hasattr(service, 'service_id') and service.service_id:
                service_model = service.service_id
            elif hasattr(service, 'combo_id') and service.combo_id:
                # Xử lý combo (trong trường hợp này, chúng ta sẽ để lại combo)
                filtered_services |= service
                continue

            if service_model:
                # Báo giá bao giao: bỏ qua các dịch vụ có is_bao_giao = True
                if self.quote_type == 'dac_biet' and not service_model.is_bao_giao:
                    filtered_services |= service

                # # Báo giá all in: bỏ qua các dịch vụ có is_allin = True
                # elif self.quote_type == 'all_in' and not service_model.is_allin:
                #     filtered_services |= service

        return filtered_services

    @api.onchange('partner_id')
    def onchange_get_data_required_fields(self):
        if self.partner_id.service_field_ids:
            for sale_service_id in self.fields_ids:
                if sale_service_id.fields_id.is_template:
                    for partner_service_field_id in self.partner_id.service_field_ids:
                        if sale_service_id.fields_id.code == partner_service_field_id.code:
                            sale_service_id.write({
                                'value_char': partner_service_field_id.value_char,
                                'value_integer': partner_service_field_id.value_integer,
                                'value_date': partner_service_field_id.value_date,
                                'selection_value_id': partner_service_field_id.selection_value_id.id,
                            })

    def action_update_fields(self):
        for field_id in self.fields_ids:
            if field_id.fields_id.is_template:
                partner_field_id = self.env['dpt.partner.required.fields'].search(
                    [('partner_id', '=', self.partner_id.id), ('code', '=', field_id.fields_id.code)])
                if not partner_field_id:
                    self.env['dpt.partner.required.fields'].create({
                        'name': field_id.fields_id.name,
                        'description': field_id.fields_id.description,
                        'fields_type': field_id.fields_id.fields_type,
                        'uom_id': field_id.fields_id.uom_id.id,
                        'code': field_id.fields_id.code,
                        'value_char': field_id.value_char,
                        'value_integer': field_id.value_integer,
                        'value_date': field_id.value_date,
                        'selection_value_id': field_id.selection_value_id.id,
                        'partner_id': self.partner_id.id,
                    })
                else:
                    partner_field_id.write({
                        'value_char': field_id.value_char,
                        'value_integer': field_id.value_integer,
                        'value_date': field_id.value_date,
                        'selection_value_id': field_id.selection_value_id.id,
                    })

    def send_quotation_department(self):
        self.times_of_quotation = self.times_of_quotation + 1
        self.state = 'wait_price'

    @api.depends('sale_service_ids.amount_total', 'service_combo_ids.amount_total')
    def _compute_service_amount(self):
        for record in self:
            # Tính tổng tiền dịch vụ riêng lẻ (không thuộc combo)
            service_untax_amount = sum(
                record.sale_service_ids.filtered(lambda s: not s.combo_id).mapped('amount_total'))
            # Tính tổng tiền combo
            combo_untax_amount = sum(record.service_combo_ids.mapped('amount_total'))
            # Tổng tiền chưa thuế = tổng dịch vụ riêng lẻ + tổng combo
            total_untax_amount = service_untax_amount + combo_untax_amount
            # Tính thuế (giả sử 8% như trong code ban đầu)
            tax_amount = total_untax_amount * 8 / 100
            record.service_total_untax_amount = total_untax_amount
            record.service_tax_amount = tax_amount
            record.service_total_amount = total_untax_amount  # Hoặc total_untax_amount + tax_amount nếu bạn muốn tính cả thuế

    def compute_show_action_calculation(self):
        # only show action calculation when current user is in the same department
        for item in self:
            not_compute_price_service_ids = True or item.sale_service_ids.filtered(
                lambda ss: ss.department_id.id in self.env.user.employee_ids.mapped('department_id').ids)
            item.show_action_calculation = True if not_compute_price_service_ids else False

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        sale = super(SaleOrder, self).copy(default)
        sale.sale_service_ids = self.sale_service_ids
        sale.fields_ids = self.fields_ids
        return sale

    def export_excel_quotation_popup(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.quotation.print.wizard',
            'views': [(False, 'form')],
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id
            },
        }

    def export_excel_quotation_total(self):

        output = stringIOModule.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        # workbook = xlsxwriter.Workbook('Báo_Giá_Dịch_Vụ.xlsx')
        worksheet = workbook.add_worksheet()
        worksheet.set_column('A:A', 1)
        worksheet.set_column('B:B', 17)
        worksheet.set_column('C:C', 30)
        worksheet.set_column('E:E', 14)

        # Định dạng tiêu đề
        bold = workbook.add_format({'bold': True})

        bold_format = workbook.add_format({'bold': True})

        normal_format = workbook.add_format({'font_size': 8})

        employee_contact_format = workbook.add_format({'align': 'right'})

        merge_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter'
        })
        special_format = workbook.add_format({
            'bold': True,
            'bg_color': '#f9cb9c'
        })
        header_sp_format = workbook.add_format({
            'bold': True,
            'font_color': '#f0681e',
            'font_size': 14
        })
        # Header
        worksheet.insert_image('B2', get_module_resource('dpt_sale_management', 'static/src/img', 'logo.png'),
                               {'x_scale': 0.10, 'y_scale': 0.06})
        worksheet.write('C2', 'CÔNG TY TNHH DPT VINA HOLDINGS - 棋速', header_sp_format)
        worksheet.write('C3', 'Địa chỉ văn phòng: Số 6A, Ngõ 183, Hoàng Văn Thái, Khương Trung, Thanh Xuân, Hà Nội')
        worksheet.write('C4', 'MST: 0109366059')
        # Title
        worksheet.merge_range('A5:F5', 'BÁO GIÁ DỊCH VỤ', merge_format)
        worksheet.write('B7', 'Khách hàng:', bold_format)
        worksheet.write('C7', self.partner_id.name or '', bold_format)
        worksheet.write('D7', 'Địa chỉ:', bold_format)
        worksheet.write('E7', self.partner_id.street or '', bold_format)
        worksheet.write('B8', 'Mặt hàng:', bold_format)
        worksheet.merge_range('B9:F9', 'Cám ơn quý khách đã quan tâm tới dịch vụ của Kỳ Tốc Logistics.'
                                       ' Chúng tôi xin được gửi tới quý khách giá cước cho hàng nhập của quý khách như sau',
                              )
        # [Hàng hóa] title cột
        worksheet.write('C10', 'Tên hàng hóa', bold_format)
        worksheet.write('D10', 'Số lượng', bold_format)
        worksheet.write('E10', 'Đơn giá', bold_format)
        worksheet.write('F10', 'Thành tiền', bold_format)
        worksheet.write('G10', 'Note', bold_format)

        # [Hàng hóa] data
        data = []
        for r in self.order_line:
            data.append((r.product_id.name, r.product_uom_qty, "{:,}".format(r.price_unit), "{:,}".format(r.price_subtotal), ''))
        data.append(('Thể tích (m3)', "{:,}".format(self.volume),
                     "{:,}".format(
                         sum(self.planned_service_combo_ids.filtered(lambda p: p.compute_uom_id.name == 'm3').mapped(
                             'price'))),
                     "{:,}".format(
                         sum(self.planned_service_combo_ids.filtered(lambda p: p.compute_uom_id.name == 'm3').mapped(
                             'amount_total'))), ''))
        data.append(('Khối lượng (kg)', "{:,}".format(self.weight),
                     "{:,}".format(
                         sum(self.planned_service_combo_ids.filtered(lambda p: p.compute_uom_id.name == 'kg').mapped(
                             'price'))),
                     "{:,}".format(
                         sum(self.planned_service_combo_ids.filtered(lambda p: p.compute_uom_id.name == 'kg').mapped(
                             'amount_total'))), ''))

        # Bắt đầu từ hàng thứ hai, viết dữ liệu vào worksheet
        row = 10
        for item, quantity, cost, amount_total, note in data:
            format = None
            if item == 'Tổng tiền hàng + cước nội địa TQ':
                format = special_format
            worksheet.write(row, 2, item, format)
            worksheet.write(row, 3, quantity, format)
            worksheet.write(row, 4, cost, format)
            worksheet.write(row, 5, amount_total, format)
            worksheet.write(row, 6, note, format)
            row += 1

        # [Hàng hóa] Merge cells cho cột 'Tên hàng hóa'
        worksheet.merge_range(f'B10:B{row}', 'Hàng hóa', merge_format)
        # worksheet.add_table('B11:F42')

        # [Thuế]
        # [Thuế] Title data
        data = []
        nk_tax_amount = 0
        for r in self.order_line:
            data.append(
                (f'NK CO Form E_{r.product_id.name}', '', f'{r.import_tax_rate * 100}%', "{:,}".format(r.import_tax_amount), ''))
            nk_tax_amount += r.import_tax_amount
        vat_tax_amount = 0
        for r in self.order_line:
            data.append((f'VAT_{r.product_id.name}', '', f"{r.vat_tax_rate * 100}%", "{:,}".format(r.vat_tax_amount), ''))
            vat_tax_amount += r.vat_tax_amount
        start = row
        for item, quantity, cost, amount_total, note in data:
            worksheet.write(row, 2, item)
            worksheet.write(row, 3, quantity)
            worksheet.write(row, 4, cost)
            worksheet.write(row, 5, amount_total)
            worksheet.write(row, 6, note)
            row += 1
        worksheet.merge_range(f'B{start + 1}:B{row}', 'Thuế', merge_format)

        # [Báo giá chi tiết]
        # [Báo giá chi tiết] Data
        # data = []
        # for r in self.sale_service_ids:
        #     data.append((r.service_id.name, r.compute_value, r.price, ''))
        start = row
        data.append(('Tổng chi phí vận chuyển theo kg', 'VND/lô', '',
                     "{:,}".format(
                         sum(self.planned_service_combo_ids.filtered(lambda p: p.compute_uom_id.name == 'kg').mapped(
                             'amount_total'))), ''))
        data.append(('Tổng chi phí vận chuyển theo m3', 'VND/lô', '',
                     "{:,}".format(
                         sum(self.planned_service_combo_ids.filtered(lambda p: p.compute_uom_id.name == 'm3').mapped(
                             'amount_total'))), ''))
        for item, quantity, cost, amount_total, note in data:
            format = None
            if item in ('Tổng chi phí vận chuyển theo kg', 'Tổng chi phí vận chuyển theo m3'):
                format = special_format
            worksheet.write(row, 2, item, format)
            worksheet.write(row, 3, quantity, format)
            worksheet.write(row, 4, cost, format)
            worksheet.write(row, 5, amount_total, format)
            worksheet.write(row, 6, note, format)
            row += 1
        worksheet.merge_range(f'B{start + 1}:B{row}', 'Cước vận chuyển', merge_format)

        worksheet.write(f'B{row + 2}', 'Liên hệ:', employee_contact_format)
        worksheet.write(f'C{row + 2}', f'Chuyên viên: {self.employee_sale.name or ""}')
        worksheet.write(f'C{row + 3}', f'SĐT: {self.employee_sale.mobile_phone or self.employee_sale.work_phone or ""}')
        worksheet.write(f'C{row + 4}', f'Email: {self.employee_sale.work_email or ""}')
        worksheet.write(f'E{row + 2}', 'CÔNG TY TNHH DPT VINA HOLDINGS')
        worksheet.write(f'H7', f"Tỷ giá tệ từ hệ thống: {self.currency_id.search([('name', '=', 'CNY')]).rate}")
        worksheet.write(f'H8', f"Tỷ giá USD từ hệ thống: {self.currency_id.search([('name', '=', 'USD')]).rate}")
        workbook.close()
        xls = output.getvalue()
        vals = {
            'name': f'Bao_gia_{self.name}' + '.xls',
            'datas': base64.b64encode(xls),
            'type': 'binary',
            'res_model': 'sale.order',
            'res_id': self.id,
        }
        file_xls = self.env['ir.attachment'].create(vals)
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/' + str(file_xls.id) + '?download=true',
            'target': 'new',
        }

    def export_excel_quotation_service(self):

        output = stringIOModule.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        # workbook = xlsxwriter.Workbook('Báo_Giá_Dịch_Vụ.xlsx')
        worksheet = workbook.add_worksheet()
        worksheet.set_column('A:A', 1)
        worksheet.set_column('B:B', 17)
        worksheet.set_column('C:C', 30)
        worksheet.set_column('E:E', 14)

        # Định dạng tiêu đề
        bold = workbook.add_format({'bold': True})

        bold_format = workbook.add_format({'bold': True})

        normal_format = workbook.add_format({'font_size': 8})

        employee_contact_format = workbook.add_format({'align': 'right'})

        merge_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter'
        })
        special_format = workbook.add_format({
            'bold': True,
            'bg_color': '#f9cb9c'
        })
        header_sp_format = workbook.add_format({
            'bold': True,
            'font_color': '#f0681e',
            'font_size': 14
        })
        # Header
        worksheet.insert_image('B2', get_module_resource('dpt_sale_management', 'static/src/img', 'logo.png'),
                               {'x_scale': 0.10, 'y_scale': 0.06})
        worksheet.write('C2', 'CÔNG TY TNHH DPT VINA HOLDINGS - 棋速', header_sp_format)
        worksheet.write('C3', 'Địa chỉ văn phòng: Số 6A, Ngõ 183, Hoàng Văn Thái, Khương Trung, Thanh Xuân, Hà Nội')
        worksheet.write('C4', 'MST: 0109366059')
        # Title
        worksheet.merge_range('A5:F5', 'BÁO GIÁ DỊCH VỤ', merge_format)
        worksheet.write('B7', 'Khách hàng:', bold_format)
        worksheet.write('D7', 'Địa chỉ:', bold_format)
        worksheet.write('B8', 'Mặt hàng:', bold_format)
        worksheet.merge_range('B9:F9', 'Cám ơn quý khách đã quan tâm tới dịch vụ của Kỳ Tốc Logistics.'
                                       ' Chúng tôi xin được gửi tới quý khách giá cước cho hàng nhập của quý khách như sau',
                              )
        # [Hàng hóa] title cột
        worksheet.write('C10', 'Tên hàng hóa', bold_format)
        worksheet.write('D10', 'Số lượng', bold_format)
        worksheet.write('E10', 'Đơn giá', bold_format)
        worksheet.write('F10', 'Thành tiền', bold_format)
        worksheet.write('G10', 'Note', bold_format)

        # [Hàng hóa] data
        data = []
        for r in self.order_line:
            data.append((r.product_id.name, r.product_uom_qty, "{:,}".format(r.price_unit),
                         "{:,}".format(r.price_subtotal), ''))
        row = 10

        # [Thuế]
        # [Thuế] Title data
        data = []
        nk_tax_amount = 0
        for r in self.order_line:
            data.append(
                (f'NK CO Form E_{r.product_id.name}', '', f'{r.import_tax_rate * 100}%', "{:,}".format(r.import_tax_amount), ''))
            nk_tax_amount += r.import_tax_amount
        vat_tax_amount = 0
        for r in self.order_line:
            data.append((f'VAT_{r.product_id.name}', '', f"{r.vat_tax_rate * 100}%", "{:,}".format(r.vat_tax_amount), ''))
            vat_tax_amount += r.vat_tax_amount
        start = row
        for item, quantity, cost, amount_total, note in data:
            worksheet.write(row, 2, item)
            worksheet.write(row, 3, quantity)
            worksheet.write(row, 4, cost)
            worksheet.write(row, 5, amount_total)
            worksheet.write(row, 6, note)
            row += 1
        worksheet.merge_range(f'B{start + 1}:B{row}', 'Thuế', merge_format)

        # [Báo giá chi tiết]
        # [Báo giá chi tiết] Data
        data = []
        total = 0
        for r in self.sale_service_ids:
            if r.service_id:
                data.append(
                    (r.service_id.name, r.compute_value, "{:,}".format(r.price), "{:,}".format(r.amount_total), ''))
                total += r.amount_total
        start = row
        data.append(('Tổng chi phí vận chuyển', '', '', "{:,}".format(self.service_total_amount), ''))
        for item, quantity, cost, amount_total, note in data:
            format = None
            if str(item) in ('Tổng chi phí vận chuyển'):
                format = special_format
            worksheet.write(row, 2, item, format)
            worksheet.write(row, 3, quantity, format)
            worksheet.write(row, 4, cost, format)
            worksheet.write(row, 5, amount_total, format)
            worksheet.write(row, 6, note, format)
            row += 1
        worksheet.merge_range(f'B{start + 1}:B{row}', 'Báo giá chi tiết', merge_format)

        worksheet.write(f'B{row + 2}', 'Liên hệ:', employee_contact_format)
        worksheet.write(f'C{row + 2}', f'Chuyên viên: {self.employee_sale.name or ""}')
        worksheet.write(f'C{row + 3}', f'SĐT: {self.employee_sale.mobile_phone or self.employee_sale.work_phone or ""}')
        worksheet.write(f'C{row + 4}', f'Email: {self.employee_sale.work_email or ""}')
        worksheet.write(f'E{row + 2}', 'CÔNG TY TNHH DPT VINA HOLDINGS')
        worksheet.write(f'H7', f"Tỷ giá tệ từ hệ thống: {self.currency_id.search([('name', '=', 'CNY')]).rate}")
        worksheet.write(f'H8', f"Tỷ giá USD từ hệ thống: {self.currency_id.search([('name', '=', 'USD')]).rate}")
        workbook.close()
        xls = output.getvalue()
        vals = {
            'name': f'Bao_gia_{self.name}' + '.xls',
            'datas': base64.b64encode(xls),
            # 'datas_fname': 'Template_ngan_sach.xls',
            'type': 'binary',
            'res_model': 'sale.order',
            'res_id': self.id,
        }
        file_xls = self.env['ir.attachment'].create(vals)
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/' + str(file_xls.id) + '?download=true',
            'target': 'new',
        }

    def export_excel_quotation_product(self):

        output = stringIOModule.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        # workbook = xlsxwriter.Workbook('Báo_Giá_Dịch_Vụ.xlsx')
        worksheet = workbook.add_worksheet()
        worksheet.set_column('A:A', 1)
        worksheet.set_column('B:B', 17)
        worksheet.set_column('C:C', 30)
        worksheet.set_column('E:E', 14)

        # Định dạng tiêu đề
        bold = workbook.add_format({'bold': True})

        bold_format = workbook.add_format({'bold': True})

        normal_format = workbook.add_format({'font_size': 8})

        employee_contact_format = workbook.add_format({'align': 'right'})

        merge_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'valign': 'vcenter'
        })
        special_format = workbook.add_format({
            'bold': True,
            'bg_color': '#f9cb9c'
        })
        header_sp_format = workbook.add_format({
            'bold': True,
            'font_color': '#f0681e',
            'font_size': 14
        })
        # Header
        worksheet.insert_image('B2', get_module_resource('dpt_sale_management', 'static/src/img', 'logo.png'),
                               {'x_scale': 0.10, 'y_scale': 0.06})
        worksheet.write('C2', 'CÔNG TY TNHH DPT VINA HOLDINGS - 棋速', header_sp_format)
        worksheet.write('C3', 'Địa chỉ văn phòng: Số 6A, Ngõ 183, Hoàng Văn Thái, Khương Trung, Thanh Xuân, Hà Nội')
        worksheet.write('C4', 'MST: 0109366059')
        # Title
        worksheet.merge_range('A5:F5', 'BÁO GIÁ DỊCH VỤ', merge_format)
        worksheet.write('B7', 'Khách hàng:', bold_format)
        worksheet.write('D7', 'Địa chỉ:', bold_format)
        worksheet.write('B8', 'Mặt hàng:', bold_format)
        worksheet.merge_range('B9:F9', 'Cám ơn quý khách đã quan tâm tới dịch vụ của Kỳ Tốc Logistics.'
                                       ' Chúng tôi xin được gửi tới quý khách giá cước cho hàng nhập của quý khách như sau',
                              )
        # [Hàng hóa] title cột
        worksheet.write('B10', 'Mã HS', bold_format)
        worksheet.write('C10', 'Tên hàng hóa', bold_format)
        worksheet.write('D10', 'Số lượng', bold_format)
        worksheet.write('E10', 'Đơn giá', bold_format)
        worksheet.write('F10', 'Thành tiền', bold_format)
        worksheet.write('G10', 'Note', bold_format)

        # [Hàng hóa] data
        data = []
        data.append(('Thể tích (m3)', "{:,}".format(self.volume),
                     "{:,}".format(
                         sum(self.planned_service_combo_ids.filtered(lambda p: p.compute_uom_id.name == 'm3').mapped(
                             'price'))), "{:,}".format(
            sum(self.planned_service_combo_ids.filtered(lambda p: p.compute_uom_id.name == 'm3').mapped(
                'amount_total'))), ''))
        data.append(('Khối lượng (kg)', "{:,}".format(self.weight),
                     "{:,}".format(
                         sum(self.planned_service_combo_ids.filtered(lambda p: p.compute_uom_id.name == 'kg').mapped(
                             'price'))), "{:,}".format(
            sum(self.planned_service_combo_ids.filtered(lambda p: p.compute_uom_id.name == 'kg').mapped(
                'amount_total'))), ''))

        # Bắt đầu từ hàng thứ hai, viết dữ liệu vào worksheet
        row = 10
        for item, quantity, cost, amount_total, note in data:
            worksheet.write(row, 2, item, None)
            worksheet.write(row, 3, quantity, None)
            worksheet.write(row, 4, cost, None)
            worksheet.write(row, 5, amount_total, None)
            worksheet.write(row, 6, note, None)
            row += 1

        # [Hàng hóa] Merge cells cho cột 'Tên hàng hóa'
        worksheet.merge_range(f'B11:B{row}', 'Hàng hóa', merge_format)

        # [Báo giá chi tiết]
        # [Báo giá chi tiết] Data
        data = []
        for r in self.order_line:
            data.append((r.product_id.name, r.product_uom_qty, "{:,}".format(r.price_unit),
                         "{:,}".format(r.price_subtotal), ''))
        start = row
        for item, quantity, cost, amount_total, note in data:
            format = None
            if item in ('Tổng chi phí vận chuyển theo kg', 'Tổng chi phí vận chuyển theo m3'):
                format = special_format
            worksheet.write(row, 2, item, format)
            worksheet.write(row, 3, quantity, format)
            worksheet.write(row, 4, cost, format)
            worksheet.write(row, 5, amount_total, format)
            worksheet.write(row, 6, note, format)
            row += 1
        worksheet.merge_range(f'B{start + 1}:B{row}', 'Báo giá chi tiết', merge_format)

        worksheet.write(f'B{row + 2}', 'Liên hệ:', employee_contact_format)
        worksheet.write(f'C{row + 2}', f'Chuyên viên: {self.employee_sale.name or ""}')
        worksheet.write(f'C{row + 3}', f'SĐT: {self.employee_sale.mobile_phone or self.employee_sale.work_phone or ""}')
        worksheet.write(f'C{row + 4}', f'Email: {self.employee_sale.work_email or ""}')
        worksheet.write(f'E{row + 2}', 'CÔNG TY TNHH DPT VINA HOLDINGS')
        worksheet.write(f'H7', f"Tỷ giá tệ từ hệ thống: {self.currency_id.search([('name', '=', 'CNY')]).rate}")
        worksheet.write(f'H8', f"Tỷ giá USD từ hệ thống: {self.currency_id.search([('name', '=', 'USD')]).rate}")

        workbook.close()
        xls = output.getvalue()
        vals = {
            'name': f'Bao_gia_{self.name}' + '.xls',
            'datas': base64.b64encode(xls),
            # 'datas_fname': 'Template_ngan_sach.xls',
            'type': 'binary',
            'res_model': 'sale.order',
            'res_id': self.id,
        }
        file_xls = self.env['ir.attachment'].create(vals)
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/' + str(file_xls.id) + '?download=true',
            'target': 'new',
        }

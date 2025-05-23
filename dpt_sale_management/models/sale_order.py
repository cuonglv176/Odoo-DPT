from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError
import xlrd, xlwt
import xlsxwriter
import base64
import io as stringIOModule
from odoo.modules.module import get_module_resource
import logging

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

    # Valores reales
    service_combo_ids = fields.One2many('dpt.sale.order.service.combo', 'sale_id', string='Combo dịch vụ thực tế',
                                        tracking=True)
    sale_service_ids = fields.One2many('dpt.sale.service.management', 'sale_id', string='Service thực tế',
                                       tracking=True,
                                       inverse='onchange_sale_service_ids')

    # Valores planificados (nuevos campos)
    planned_service_combo_ids = fields.One2many('dpt.sale.order.service.combo', 'planned_sale_id',
                                                string='Combo dịch vụ dự kiến', tracking=True)
    planned_sale_service_ids = fields.One2many('dpt.sale.service.management', 'planned_sale_id',
                                               string='Service dự kiến', tracking=True)
    # Thêm trường mới cho việc tất toán và chốt giá
    settle_by = fields.Selection([
        ('planned', 'Tất toán theo dự kiến'),
        ('actual', 'Tất toán theo thực tế')
    ], string='Phương thức tất toán', default='actual', tracking=True,
        help='Chọn phương thức tất toán theo dự kiến hoặc thực tế')
    # Campos existentes
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

    # Método para calcular el total planificado
    @api.depends('planned_sale_service_ids.amount_total')
    def _compute_planned_service_amount(self):
        for record in self:
            record.planned_service_total_amount = sum(record.planned_sale_service_ids.mapped('amount_total'))

    # Thêm phương thức onchange_service_combo_ids vào class SaleOrder
    @api.onchange('service_combo_ids')
    def onchange_service_combo_ids(self):
        """Tự động tạo dịch vụ khi combo được thêm vào order"""
        # Xác định các combo mới được thêm vào
        current_combo_ids = self.service_combo_ids.ids if self.service_combo_ids else []
        existing_combo_ids = []
        for service in self.sale_service_ids:
            if service.combo_id and service.combo_id.id not in existing_combo_ids:
                existing_combo_ids.append(service.combo_id.id)
        # Tìm các combo mới được thêm vào
        new_combo_ids = [combo_id for combo_id in current_combo_ids if combo_id not in existing_combo_ids]
        # Tìm các combo bị xóa đi
        removed_combo_ids = [combo_id for combo_id in existing_combo_ids if combo_id not in current_combo_ids]
        # Xóa các dịch vụ thuộc combo bị xóa
        if removed_combo_ids:
            services_to_remove = self.sale_service_ids.filtered(lambda s: s.combo_id.id in removed_combo_ids)
            self.sale_service_ids -= services_to_remove
        # Thêm dịch vụ từ các combo mới
        if new_combo_ids:
            new_services = []
            for combo_id in new_combo_ids:
                combo = self.env['dpt.sale.order.service.combo'].browse(combo_id)
                services = combo.get_combo_services()
                for service_data in services:
                    new_services.append((0, 0, {
                        'service_id': service_data['service_id'],
                        'price': service_data['price'],
                        'uom_id': service_data['uom_id'],
                        'qty': service_data['qty'],
                        'combo_id': combo.id,
                        'price_status': 'calculated',
                        'department_id': service_data['department_id'],
                    }))
            if new_services:
                self.sale_service_ids = [(4, service.id) for service in self.sale_service_ids] + new_services

    # Nuevo método para manejar combos planificados
    @api.onchange('planned_service_combo_ids')
    def onchange_planned_service_combo_ids(self):
        """Tự động tạo dịch vụ khi combo được thêm vào order (cho dự kiến)"""
        # Xác định các combo mới được thêm vào
        current_combo_ids = self.planned_service_combo_ids.ids if self.planned_service_combo_ids else []
        existing_combo_ids = []
        for service in self.planned_sale_service_ids:
            if service.combo_id and service.combo_id.id not in existing_combo_ids:
                existing_combo_ids.append(service.combo_id.id)
        # Tìm các combo mới được thêm vào
        new_combo_ids = [combo_id for combo_id in current_combo_ids if combo_id not in existing_combo_ids]
        # Tìm các combo bị xóa đi
        removed_combo_ids = [combo_id for combo_id in existing_combo_ids if combo_id not in current_combo_ids]
        # Xóa các dịch vụ thuộc combo bị xóa
        if removed_combo_ids:
            services_to_remove = self.planned_sale_service_ids.filtered(lambda s: s.combo_id.id in removed_combo_ids)
            self.planned_sale_service_ids -= services_to_remove
        # Thêm dịch vụ từ các combo mới
        if new_combo_ids:
            new_services = []
            for combo_id in new_combo_ids:
                combo = self.env['dpt.sale.order.service.combo'].browse(combo_id)
                services = combo.get_combo_services()
                for service_data in services:
                    new_services.append((0, 0, {
                        'service_id': service_data['service_id'],
                        'price': service_data['price'],
                        'uom_id': service_data['uom_id'],
                        'qty': service_data['qty'],
                        'combo_id': combo.id,
                        'price_status': 'calculated',
                        'department_id': service_data['department_id'],
                        'planned_sale_id': self.id,
                    }))
            if new_services:
                self.planned_sale_service_ids = [(4, service.id) for service in
                                                 self.planned_sale_service_ids] + new_services

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
        # if not self.employee_sale:
        self = self.sudo()
        if self.partner_id.user_id:
            self.employee_sale = self.partner_id.user_id.employee_id
        else:
            self.employee_sale = self.user_id.employee_id
        # if not self.employee_cs:
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
        return res

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        self.check_required_fields()
        if self.state != 'sale':
            self.onchange_calculation_tax()
        if vals.get('state') == 'sale':
            self.action_update_fields()
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
            # if r.fields_id.type == 'options' or (
            #         r.fields_id.type == 'required' and (
            #         r.value_char or r.value_integer > 0 or r.value_date or r.selection_value_id)):
            #     continue
            # else:
            #     raise ValidationError(_("Please fill required fields!!!"))

    @api.onchange('sale_service_ids', 'planned_sale_service_ids')
    def onchange_sale_service_ids(self):
        fields_dict = {}
        sale_order = self.env['sale.order'].browse(self.origin)
        list_exist = sale_order.fields_ids.fields_id.ids
        list_onchange = [item.fields_id.id for item in self.fields_ids]

        # Kết hợp cả dịch vụ thực tế và dự kiến để xử lý
        all_services = []
        # Dịch vụ thực tế
        for sale_service in self.sale_service_ids:
            if sale_service and sale_service.service_id:
                all_services.append((sale_service, 'actual'))

        # Dịch vụ dự kiến
        for planned_service in self.planned_sale_service_ids:
            if planned_service and planned_service.service_id:
                all_services.append((planned_service, 'planned'))

        # Duyệt qua từng dịch vụ để xử lý
        for sale_service, service_type in all_services:
            for req_field in sale_service.service_id.required_fields_ids:
                # Nếu req_field không tồn tại, bỏ qua
                if not req_field:
                    continue

                # Tạo key duy nhất để tránh trùng lặp
                field_key = (req_field.id, sale_service.id)
                if field_key in fields_dict:
                    continue

                rec = None
                # Kiểm tra nếu trường đã tồn tại với cùng sale_service_id
                existing_field = self.fields_ids.filtered(
                    lambda f: f.fields_id.id == req_field.id and f.sale_service_id.id == sale_service.id
                )
                if existing_field:
                    rec = {
                        'sequence': 1 if existing_field.type == 'required' else 0,
                        'fields_id': req_field.id,
                        'sale_id': self.id,
                        'value_char': existing_field.value_char,
                        'value_integer': existing_field.value_integer,
                        'value_date': existing_field.value_date,
                        'selection_value_id': existing_field.selection_value_id.id if existing_field.selection_value_id else False,
                        'sale_service_id': sale_service.id,
                        'service_id': sale_service.service_id.id,  # Thêm service_id để dễ dàng xử lý
                    }

                # Ưu tiên lấy dữ liệu từ sale order nếu trường tồn tại trong đó
                elif req_field.id in list_exist:
                    for field_data in sale_order.fields_ids:
                        if field_data.fields_id.id == req_field.id:
                            rec = {
                                'sequence': 1 if field_data.type == 'required' else 0,
                                'fields_id': req_field.id,
                                'sale_id': self.id,
                                'value_char': field_data.value_char,
                                'value_integer': field_data.value_integer,
                                'value_date': field_data.value_date,
                                'selection_value_id': field_data.selection_value_id.id if field_data.selection_value_id else False,
                                'sale_service_id': sale_service.id,
                                'service_id': sale_service.service_id.id,
                            }
                            break
                # Nếu không có trong sale order, kiểm tra từ dữ liệu của record hiện tại
                elif req_field.id in list_onchange:
                    for field_data in self.fields_ids:
                        if field_data.fields_id.id == req_field.id:
                            rec = {
                                'sequence': 1 if field_data.type == 'required' else 0,
                                'fields_id': req_field.id,
                                'sale_id': self.id,
                                'value_char': field_data.value_char,
                                'value_integer': field_data.value_integer,
                                'value_date': field_data.value_date,
                                'selection_value_id': field_data.selection_value_id.id if field_data.selection_value_id else False,
                                'sale_service_id': sale_service.id,
                                'service_id': sale_service.service_id.id,
                            }
                            break

                # Nếu không có dữ liệu từ hai nguồn trên, tạo giá trị mặc định
                if not rec:
                    rec = {
                        'sequence': 1 if req_field.type == 'required' else 0,
                        'fields_id': req_field.id,
                        'sale_id': self.id,
                        'sale_service_id': sale_service.id,
                        'service_id': sale_service.service_id.id,
                    }
                    default_value = req_field.get_default_value(so=self)
                    if default_value:
                        rec.update(default_value)

                # Lưu vào dictionary
                fields_dict[field_key] = rec

        # Kết hợp và sắp xếp kết quả
        if fields_dict:
            sorted_vals = sorted(fields_dict.values(), key=lambda x: x["sequence"], reverse=True)
            self.fields_ids = [(5, 0, 0)]  # Xóa dữ liệu cũ
            self.fields_ids = [(0, 0, item) for item in sorted_vals]
        else:
            # Nếu không còn dịch vụ nào thì xóa hết fields_ids
            if not self.sale_service_ids and not self.planned_sale_service_ids:
                self.fields_ids = [(5, 0, 0)]

        # Gọi hàm cập nhật thêm
        self.onchange_get_data_required_fields()

    def get_combo_price_from_pricelist(self, combo_id):
        """Lấy giá combo từ bảng giá"""
        self.ensure_one()
        if not combo_id or not self.partner_id:
            return False, 0.0

        # Tìm bảng giá ưu tiên của khách hàng
        pricelist = self.env['product.pricelist'].search([
            ('partner_id', '=', self.partner_id.id),
            ('state', '=', 'active')
        ], limit=1)

        # Nếu không có bảng giá riêng, tìm bảng giá chung
        if not pricelist:
            pricelist = self.env['product.pricelist'].search([
                ('partner_id', '=', False),
                ('state', '=', 'active')
            ], limit=1)

        if not pricelist:
            return False, 0.0

        # Tìm mục giá cho combo này
        today = fields.Date.today()
        # Trực tiếp lấy combo_id.combo_id thay vì combo_id.combo_id.id
        combo_item = self.env['product.pricelist.item'].search([
            ('pricelist_id', '=', pricelist.id),
            ('combo_id', '=', combo_id.combo_id.id),
            '|', ('date_start', '<=', today), ('date_start', '=', False),
            '|', ('date_end', '>=', today), ('date_end', '=', False)
        ], limit=1)

        if not combo_item:
            return False, 0.0

        return combo_item, combo_item.fixed_price

    def distribute_combo_price(self):
        """Phân bổ giá combo cho các dịch vụ theo tỉ lệ"""
        # Đánh dấu các dịch vụ đã xử lý để tránh xử lý lại
        processed_services = self.env['dpt.sale.service.management']

        for combo in self.service_combo_ids:
            # Lấy giá combo từ bảng giá
            combo_item, combo_price = self.get_combo_price_from_pricelist(combo)
            if not combo_item or combo_price <= 0:
                continue

            # Cập nhật giá combo từ bảng giá
            combo.price = combo_price

            # Lấy các dịch vụ thuộc combo này
            services = self.sale_service_ids.filtered(lambda s: s.combo_id.id == combo.id)
            if not services:
                continue

            # Tính tổng giá gốc của các dịch vụ trong combo
            total_original_price = sum(service.service_id.price for service in services)

            # Phân bổ giá cho từng dịch vụ
            for service in services:
                # Tìm trường dpt.sale.order.fields phù hợp để lấy giá trị số lượng
                compute_value = 1
                compute_uom_id = False

                # Nếu có uom_id trong bảng giá
                if combo_item.uom_id:
                    # Tìm field có cùng uom_id và thuộc service này
                    compute_field = self.fields_ids.filtered(
                        lambda f: f.uom_id.id == combo_item.uom_id.id and
                                  f.using_calculation_price and
                                  f.service_id.id == service.service_id.id and
                                  f.fields_type == 'integer')

                    if compute_field:
                        compute_value = compute_field.value_integer or 1
                        compute_uom_id = compute_field.uom_id.id

                # Tính giá phân bổ
                if total_original_price <= 0:
                    # Nếu tổng giá gốc bằng 0, phân bổ đều
                    distributed_price = combo_price / len(services)
                else:
                    # Phân bổ theo tỉ lệ giá gốc
                    ratio = service.service_id.price / total_original_price
                    distributed_price = combo_price * ratio

                # Cập nhật đơn giá và số lượng
                service.with_context(from_pricelist=True).write({
                    'price': distributed_price / compute_value if combo_item.is_price else distributed_price,
                    'price_in_pricelist': distributed_price,
                    'compute_value': compute_value,
                    'compute_uom_id': compute_uom_id,
                    'price_status': 'calculated',
                    'pricelist_item_id': combo_item.id,
                })

                # Đánh dấu dịch vụ đã xử lý
                processed_services |= service

        # Tương tự cho các combo dự kiến
        for planned_combo in self.planned_service_combo_ids:
            combo_item, combo_price = self.get_combo_price_from_pricelist(planned_combo)
            if not combo_item or combo_price <= 0:
                continue

            # Cập nhật giá combo từ bảng giá
            planned_combo.price = combo_price

            planned_services = self.planned_sale_service_ids.filtered(lambda s: s.combo_id.id == planned_combo.id)
            if not planned_services:
                continue

            total_original_price = sum(service.service_id.price for service in planned_services)

            # Phân bổ giá cho từng dịch vụ dự kiến
            for service in planned_services:
                # Tìm trường dpt.sale.order.fields phù hợp để lấy giá trị số lượng
                compute_value = 1
                compute_uom_id = False

                # Nếu có uom_id trong bảng giá
                if combo_item.uom_id:
                    # Tìm field có cùng uom_id và thuộc service này
                    compute_field = self.fields_ids.filtered(
                        lambda f: f.uom_id.id == combo_item.uom_id.id and
                                  f.using_calculation_price and
                                  f.service_id.id == service.service_id.id and
                                  f.fields_type == 'integer')

                    if compute_field:
                        compute_value = compute_field.value_integer or 1
                        compute_uom_id = compute_field.uom_id.id

                # Tính giá phân bổ
                if total_original_price <= 0:
                    # Nếu tổng giá gốc bằng 0, phân bổ đều
                    distributed_price = combo_price / len(planned_services)
                else:
                    # Phân bổ theo tỉ lệ giá gốc
                    ratio = service.service_id.price / total_original_price
                    distributed_price = combo_price * ratio

                # Cập nhật đơn giá và số lượng
                service.with_context(from_pricelist=True).write({
                    'price': distributed_price / compute_value if combo_item.is_price else distributed_price,
                    'price_in_pricelist': distributed_price,
                    'compute_value': compute_value,
                    'compute_uom_id': compute_uom_id,
                    'price_status': 'calculated',
                    'pricelist_item_id': combo_item.id,
                })

                # Đánh dấu dịch vụ đã xử lý
                processed_services |= service

        return processed_services

    def action_calculation(self):
        # Trước tiên phân bổ giá cho các dịch vụ thuộc combo
        processed_services = self.distribute_combo_price()

        # Sau đó tính giá cho các dịch vụ không thuộc combo hoặc chưa có giá
        for sale_service_id in self.sale_service_ids:
            # Bỏ qua các dịch vụ đã được xử lý từ combo
            if sale_service_id in processed_services:
                continue

            # Bỏ qua các dịch vụ đã có giá từ combo
            if sale_service_id.combo_id and sale_service_id.price > 0 and sale_service_id.price_status == 'calculated':
                continue

            if not sale_service_id.uom_id:
                continue

            approved = sale_service_id.approval_id.filtered(
                lambda approval: approval.request_status in ('approved', 'refused'))
            if approved:
                continue

            current_uom_id = sale_service_id.uom_id
            service_price_ids = sale_service_id.service_id.get_active_pricelist(partner_id=self.partner_id)
            if current_uom_id:
                service_price_ids = service_price_ids.filtered(lambda sp: sp.uom_id.id == current_uom_id.id and (
                        sp.partner_id and sp.partner_id.id == self.partner_id.id or not sp.partner_id))
            if not service_price_ids:
                continue
            max_price = 0
            price_list_item_id = None
            compute_value = 1
            compute_uom_id = None

            # Logic tính giá giữ nguyên như trước
            for service_price_id in service_price_ids:
                if service_price_id.compute_price == 'fixed':
                    price = max(service_price_id.currency_id.rate * service_price_id.fixed_price,
                                service_price_id.min_amount)
                    if price > max_price:
                        max_price = price
                        price_list_item_id = service_price_id
                elif service_price_id.compute_price == 'percentage':
                    # Logic phần trăm giữ nguyên
                    price_base = 0
                    price = 0
                    if service_price_id.percent_based_on == 'product_total_amount':
                        price_base = sum(self.order_line.mapped('price_subtotal'))
                    elif service_price_id.percent_based_on == 'declaration_total_amount':
                        price_base = sum(self.order_line.mapped('declared_unit_total'))
                    elif service_price_id.percent_based_on == 'purchase_total_amount':
                        purchase_ids = self.purchase_ids.filtered(lambda po: po.purchase_type == 'external')
                        price_base = 0
                        for order_line in purchase_ids.mapped('order_line'):
                            price_base += order_line.price_subtotal * order_line.order_id.last_rate_currency
                    if price_base:
                        price = max(
                            service_price_id.currency_id.rate * (price_base * service_price_id.percent_price / 100),
                            service_price_id.min_amount)
                    if price and price > max_price:
                        max_price = price
                        price_list_item_id = service_price_id
                elif service_price_id.compute_price == 'table':
                    # Logic bảng giá giữ nguyên
                    compute_field_ids = self.fields_ids.filtered(
                        lambda f: f.using_calculation_price and f.service_id.id == sale_service_id.service_id.id)
                    for compute_field_id in compute_field_ids:
                        if not service_price_id.is_accumulated:
                            detail_price_ids = service_price_id.pricelist_table_detail_ids.filtered(lambda
                                                                                                        ptd: ptd.uom_id.id == compute_field_id.uom_id.id and compute_field_id.value_integer >= ptd.min_value and compute_field_id.value_integer <= ptd.max_value)
                            for detail_price_id in detail_price_ids:
                                price = compute_field_id.value_integer * detail_price_id.amount if service_price_id.is_price else detail_price_id.amount
                                price = max(service_price_id.currency_id.rate * price, service_price_id.min_amount)
                                if price > max_price:
                                    max_price = price
                                    price_list_item_id = service_price_id
                                    compute_value = compute_field_id.value_integer
                                    compute_uom_id = compute_field_id.uom_id.id
                        else:
                            detail_price_ids = service_price_id.pricelist_table_detail_ids.filtered(
                                lambda ptd: ptd.uom_id.id == compute_field_id.uom_id.id)
                            total_price = 0
                            for detail_price_id in detail_price_ids.sorted(key=lambda r: r.min_value):
                                if detail_price_id.min_value > compute_field_id.value_integer:
                                    continue
                                if detail_price_id.max_value:
                                    price = (min(compute_field_id.value_integer,
                                                 detail_price_id.max_value) - detail_price_id.min_value + 1) * detail_price_id.amount if service_price_id.is_price else detail_price_id.amount
                                else:
                                    price = (
                                                    compute_field_id.value_integer - detail_price_id.min_value + 1) * detail_price_id.amount if service_price_id.is_price else detail_price_id.amount
                                total_price += service_price_id.currency_id.rate * price
                            if max(total_price, service_price_id.min_amount) > max_price:
                                max_price = max(total_price, service_price_id.min_amount)
                                price_list_item_id = service_price_id
                                compute_value = compute_field_id.value_integer
                                compute_uom_id = compute_field_id.uom_id.id

            price_status = sale_service_id.price_status or 'no_price'
            if sale_service_id.service_id.pricelist_item_ids and price_status == 'no_price':
                price_status = 'calculated'

            sale_service_id.with_context(from_pricelist=True).write({
                'uom_id': price_list_item_id.uom_id.id if price_list_item_id else (
                    service_price_ids[:1].uom_id.id if service_price_ids and service_price_ids[:1].uom_id else None),
                'price': max_price / compute_value if price_list_item_id and price_list_item_id.is_price else max_price,
                'qty': 1,
                'pricelist_item_id': price_list_item_id.id if price_list_item_id else (
                    service_price_ids[:1].id if service_price_ids else None),
                'price_in_pricelist': max_price,
                'compute_value': compute_value,
                'compute_uom_id': compute_uom_id,
                'price_status': price_status,
            })
        # Tương tự cho planned_sale_service_ids
        for planned_service_id in self.planned_sale_service_ids:
            # Bỏ qua các dịch vụ đã được xử lý từ combo
            if planned_service_id in processed_services:
                continue

            # Bỏ qua dịch vụ dự kiến đã có giá từ combo
            if planned_service_id.combo_id and planned_service_id.price > 0 and planned_service_id.price_status == 'calculated':
                continue

            # Áp dụng logic tương tự như với sale_service_ids
            # ...
        self.onchange_calculation_tax()

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

    @api.depends('sale_service_ids.amount_total')
    def _compute_service_amount(self):
        untax_amount = 0
        tax_amount = 0
        for r in self.sale_service_ids:
            untax_amount += r.amount_total
            tax_amount += r.amount_total * 8 / 100
        self.service_total_untax_amount = untax_amount
        self.service_tax_amount = tax_amount
        self.service_total_amount = untax_amount

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

    def export_excel_quotation(self):

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
        worksheet.write('E10', 'Chi phí (VND)', bold_format)
        worksheet.write('F10', 'Note', bold_format)

        # [Hàng hóa] data
        data = []
        for r in self.order_line:
            data.append((r.product_id.name, r.product_uom_qty, r.price_subtotal, ''))
        data.append(('Cước vận chuyển nội địa TQ', '', '', ''))
        data.append(('Tổng tiền hàng + cước nội địa TQ', '', '', ''))
        data.append(('Thể tích (m3)', self.volume, '', ''))
        data.append(('Khối lượng (kg)', self.weight, '', ''))
        data.append(('Phí vận chuyển/ m3', '', '', ''))
        data.append(('Phí vận chuyển/ kg', '', '', ''))

        # Bắt đầu từ hàng thứ hai, viết dữ liệu vào worksheet
        row = 10
        for item, quantity, cost, note in data:
            format = None
            if item == 'Tổng tiền hàng + cước nội địa TQ':
                format = special_format
            worksheet.write(row, 2, item, format)
            worksheet.write(row, 3, quantity, format)
            worksheet.write(row, 4, cost, format)
            worksheet.write(row, 5, note, format)
            row += 1

        # [Hàng hóa] Merge cells cho cột 'Tên hàng hóa'
        worksheet.merge_range(f'B10:B{row}', 'Hàng hóa', merge_format)
        # worksheet.add_table('B11:F42')

        # [Thuế]
        # [Thuế] Title data
        data = []
        nk_tax_amount = 0
        for r in self.order_line:
            data.append((f'NK CO Form E_{r.product_id.name}', r.import_tax_rate, r.import_tax_amount, ''))
            nk_tax_amount += r.import_tax_amount
        vat_tax_amount = 0
        for r in self.order_line:
            data.append((f'VAT_{r.product_id.name}', r.vat_tax_rate, r.vat_tax_amount, ''))
            vat_tax_amount += r.vat_tax_amount
        start = row
        for item, quantity, cost, note in data:
            worksheet.write(row, 2, item)
            worksheet.write(row, 3, quantity)
            worksheet.write(row, 4, cost)
            worksheet.write(row, 5, note)
            row += 1
        worksheet.merge_range(f'B{start + 1}:B{row}', 'Thuế', merge_format)

        # [Báo giá chi tiết]
        # [Báo giá chi tiết] Data
        data = []
        for r in self.sale_service_ids:
            data.append((r.service_id.name, r.compute_value, r.price, ''))
        start = row
        data.append(('Tổng chi phí vận chuyển theo kg', 'VND/lô', '', ''))
        data.append(('Tổng chi phí vận chuyển theo m3', 'VND/lô', '', ''))
        data.append(('Chi phí theo kg', 'VND/kg', '', ''))
        data.append(('Chi phí theo m3', 'VND/m3', '', ''))
        for r in self.order_line:
            data.append((f'Tổng chi phí/{r.product_id.name}', 'VND/sản phẩm', '', ''))
        for item, quantity, cost, note in data:
            format = None
            if item in ('Tổng chi phí vận chuyển theo kg', 'Tổng chi phí vận chuyển theo m3'):
                format = special_format
            worksheet.write(row, 2, item, format)
            worksheet.write(row, 3, quantity, format)
            worksheet.write(row, 4, cost, format)
            worksheet.write(row, 5, note, format)
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

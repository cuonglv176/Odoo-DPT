from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError
import xlrd, xlwt
import xlsxwriter
import base64
import io as stringIOModule
from odoo.modules.module import get_module_resource

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
    sale_service_ids = fields.One2many('dpt.sale.service.management', 'sale_id', string='Service', tracking=True,
                                       inverse='onchange_sale_service_ids')
    fields_ids = fields.One2many('dpt.sale.order.fields', 'sale_id', string='Fields')
    service_total_untax_amount = fields.Float(compute='_compute_service_amount')
    service_tax_amount = fields.Float(compute='_compute_service_amount')
    service_total_amount = fields.Float(compute='_compute_service_amount')
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
        if self.partner_id.user_id:
            self.employee_sale = self.partner_id.user_id.employee_id
        else:
            self.employee_sale = self.user_id.employee_id
        # if not self.employee_cs:
        if self.partner_id.cs_user_id:
            self.employee_cs = self.partner_id.cs_user_id.employee_id
        else:
            self.employee_sale = self.user_id.employee_id

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

    # @api.onchange('sale_service_ids')
    # def onchange_sale_service_ids(self):
    #     val = []
    #     sequence = 0
    #     list_exist = self.env['sale.order'].browse(self.origin).fields_ids
    #     list_onchange = self.fields_ids
    #     list_sale_service_id = []
    #     service_id = []
    #     fields_id = []
    #     for sale_service_id in self.sale_service_ids:
    #         # if sale_service_id.service_id.id in list_sale_service_id:
    #         #     continue
    #         for required_fields_id in sale_service_id.service_id.required_fields_ids:
    #             if sale_service_id.id in list_sale_service_id and required_fields_id.id in fields_id:
    #                 continue
    #             if required_fields_id.id in list_exist.fields_id.ids and sale_service_id.id in list_exist.sale_service_id.ids:
    #                 for field_data in list_exist:
    #                     if field_data.fields_id.id == required_fields_id.id:
    #                         val.append({
    #                             'sequence': 1 if field_data.type == 'required' else 0,
    #                             'fields_id': required_fields_id.id,
    #                             'sale_id': self.id,
    #                             'value_char': field_data.value_char,
    #                             'sale_service_id': sale_service_id.id,
    #                             'value_integer': field_data.value_integer,
    #                             'value_date': field_data.value_date,
    #                             'selection_value_id': field_data.selection_value_id.id,
    #                         })
    #             elif required_fields_id.id in list_onchange.fields_id.ids:
    #                 for field_data in self.fields_ids:
    #                     if field_data.fields_id.id == required_fields_id.id:
    #                         val.append({
    #                             'sequence': 1 if field_data.type == 'required' else 0,
    #                             'fields_id': required_fields_id.id,
    #                             'sale_id': self.id,
    #                             'sale_service_id': sale_service_id.id,
    #                             'value_char': field_data.value_char,
    #                             'value_integer': field_data.value_integer,
    #                             'value_date': field_data.value_date,
    #                             'selection_value_id': field_data.selection_value_id.id,
    #
    #                         })
    #             if val:
    #                 result = [item for item in val if item['fields_id'] == required_fields_id.id]
    #                 if not result:
    #                     x = {
    #                         'sequence': 1 if required_fields_id.type == 'required' else 0,
    #                         'fields_id': required_fields_id.id,
    #                     }
    #                     default_value = required_fields_id.get_default_value(so=self)
    #                     if default_value:
    #                         x.update(default_value)
    #                     val.append(x)
    #             else:
    #                 x = {
    #                     'sequence': 1 if required_fields_id.type == 'required' else 0,
    #                     'fields_id': required_fields_id.id,
    #                 }
    #                 default_value = required_fields_id.get_default_value(so=self)
    #                 if default_value:
    #                     x.update(default_value)
    #                 val.append(x)
    #             list_sale_service_id.append(sale_service_id.id)
    #             service_id.append(sale_service_id.service_id.id)
    #             fields_id.append(required_fields_id.id)
    #     if val:
    #         val = sorted(val, key=lambda x: x["sequence"], reverse=True)
    #         self.fields_ids = None
    #         self.fields_ids = [(0, 0, item) for item in val]
    #     if not self.sale_service_ids:
    #         self.fields_ids = [(5, 0, 0)]
    #     self.onchange_get_data_required_fields()

    @api.onchange('sale_service_ids')
    def onchange_sale_service_ids(self):
        fields_dict = {}
        sale_order = self.env['sale.order'].browse(self.origin)
        list_exist = sale_order.fields_ids.fields_id.ids
        list_onchange = [item.fields_id.id for item in self.fields_ids]

        # Duyệt qua từng sale_service và xử lý nếu sale_service và service_id của nó tồn tại
        for sale_service in self.sale_service_ids:
            if not sale_service or not sale_service.service_id:
                continue  # Bỏ qua nếu sale_service không hợp lệ

            for req_field in sale_service.service_id.required_fields_ids:
                # Nếu req_field không tồn tại, bỏ qua
                if not req_field:
                    continue

                # Nếu trường đã được xử lý rồi thì bỏ qua (tránh trùng lặp)
                if (req_field.id, sale_service.id) in fields_dict:
                    continue

                rec = None
                # Kiểm tra nếu trường đã tồn tại với cùng sale_service_id
                existing_field = self.fields_ids.filtered(
                    lambda f: f.fields_id.id == req_field.id and f.sale_service_id.id == sale_service.id
                )
                if existing_field:
                    continue  # Nếu đã tồn tại, bỏ qua

                # Ưu tiên lấy dữ liệu từ sale order nếu trường tồn tại trong đó
                if req_field.id in list_exist:
                    for field_data in sale_order.fields_ids:
                        if field_data.fields_id.id == req_field.id:
                            rec = {
                                'sequence': 1 if field_data.type == 'required' else 0,
                                'fields_id': req_field.id,
                                'sale_id': self.id,
                                'value_char': field_data.value_char,
                                'value_integer': field_data.value_integer,
                                'value_date': field_data.value_date,
                                'selection_value_id': field_data.selection_value_id.id,
                                'sale_service_id': sale_service.id,
                            }
                            break
                # Nếu không có trong sale order, kiểm tra từ dữ liệu của record hiện tại (onchange)
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
                                'selection_value_id': field_data.selection_value_id.id,
                                'sale_service_id': sale_service.id,
                            }
                            break

                # Nếu không có dữ liệu từ hai nguồn trên, tạo giá trị mặc định
                if not rec:
                    rec = {
                        'sequence': 1 if req_field.type == 'required' else 0,
                        'fields_id': req_field.id,
                        'sale_id': self.id,
                        'sale_service_id': sale_service.id,
                    }
                    default_value = req_field.get_default_value(so=self)
                    if default_value:
                        rec.update(default_value)

                # Lưu vào dictionary với key là (req_field.id, sale_service.id) để tránh trùng lặp
                fields_dict[(req_field.id, sale_service.id)] = rec

        if fields_dict:
            sorted_vals = sorted(fields_dict.values(), key=lambda x: x["sequence"], reverse=True)
            self.fields_ids = [(5, 0, 0)]  # Xóa dữ liệu cũ
            self.fields_ids = [(0, 0, item) for item in sorted_vals]
        else:
            # Nếu không còn sale_service nào thì xóa hết fields_ids
            if not self.sale_service_ids:
                self.fields_ids = [(5, 0, 0)]

        # Gọi hàm cập nhật thêm nếu cần
        self.onchange_get_data_required_fields()

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order_id in self:
            # if order_id.sale_service_ids.filtered(lambda ss: ss.price_in_pricelist != ss.price):
            #     raise ValidationError(_('Please approve new price!'))
            if not order_id.update_pricelist:
                continue
            for sale_service_id in order_id.sale_service_ids.filtered(lambda ss: ss.price_in_pricelist != ss.price):
                if not sale_service_id.uom_id:
                    raise ValidationError(_("Please insert Units"))
                pricelist_id = self.env['product.pricelist'].sudo().search([('partner_id', '=', self.partner_id.id)])
                if not pricelist_id:
                    pricelist_id = self.env['product.pricelist'].sudo().create({
                        'name': 'Bảng giá của khách hàng %s' % self.partner_id.name,
                        'partner_id': self.partner_id.id,
                        'currency_id': sale_service_id.currency_id.id,
                    })
                price_list_item_id = self.env['product.pricelist.item'].sudo().search(
                    [('pricelist_id', '=', pricelist_id.id), ('service_id', '=', sale_service_id.service_id.id),
                     ('uom_id', '=', sale_service_id.uom_id.id), ('partner_id', '=', self.partner_id.id)])
                if not price_list_item_id:
                    self.env['product.pricelist.item'].sudo().create({
                        'partner_id': self.partner_id.id,
                        'pricelist_id': pricelist_id.id,
                        'service_id': sale_service_id.service_id.id,
                        'uom_id': sale_service_id.uom_id.id,
                        'compute_price': 'fixed',
                        'fixed_price': sale_service_id.price,
                        'is_price': False,
                    })
                else:
                    price_list_item_id.write({
                        'compute_price': 'fixed',
                        'fixed_price': sale_service_id.price,
                        'is_price': False,
                    })
            order_id.action_update_fields()
        return res

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

    def action_calculation(self):
        # self.sale_service_ids._compute_price_status()
        # get default based on pricelist
        # for sale_service_id in self.sale_service_ids.filtered(
        #         lambda ss: ss.department_id.id == self.env.user.employee_ids[:1].department_id.id):

        for sale_service_id in self.sale_service_ids:
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
            for service_price_id in service_price_ids:
                if service_price_id.compute_price == 'fixed':
                    price = max(service_price_id.currency_id.rate * service_price_id.fixed_price,
                                service_price_id.min_amount)
                    if price > max_price:
                        max_price = price
                        price_list_item_id = service_price_id
                elif service_price_id.compute_price == 'percentage':
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
                    compute_field_ids = self.fields_ids.filtered(
                        lambda f: f.using_calculation_price and f.service_id.id == sale_service_id.service_id.id)
                    # compute_field_ids = self.fields_ids.filtered(
                    #     lambda f: f.using_calculation_price and f.sale_service_id.id == sale_service_id.id)
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
        self.onchange_calculation_tax()

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


class SaleOrderField(models.Model):
    _name = 'dpt.sale.order.fields'

    def _default_sequence(self):
        if self.type == 'required':
            return 1
        return 0

    sequence = fields.Integer(default=_default_sequence, compute='_compute_sequence', store=True)
    sale_id = fields.Many2one('sale.order', string='Sale Order')
    service_id = fields.Many2one(related='fields_id.service_id')
    fields_id = fields.Many2one('dpt.service.management.required.fields', string='Fields')
    value_char = fields.Char(string='Value Char')
    value_integer = fields.Float(string='Value Integer')
    value_date = fields.Date(string='Value Date')
    selection_value_id = fields.Many2one('dpt.sale.order.fields.selection', string='Selection Value')
    type = fields.Selection(selection=[
        ("required", "Required"),
        ("options", "Options")
    ], string='Type Fields', default='options', related='fields_id.type')
    fields_type = fields.Selection([
        ('char', 'Char'),
        ('integer', 'Integer'),
        ('date', 'Date'),
        ('selection', 'Selection'),
    ], string='Fields type', default='char', related='fields_id.fields_type')
    using_calculation_price = fields.Boolean(related='fields_id.using_calculation_price')
    uom_id = fields.Many2one(related="fields_id.uom_id")
    sale_service_id = fields.Many2one('dpt.sale.service.management')
    sale_service_id_key = fields.Integer(related='sale_service_id.id')

    @api.onchange('sale_id')
    def onchange_get_data_required_fields(self):
        if self.sale_id.partner_id.service_field_ids:
            if self.fields_id.is_template:
                for partner_service_field_id in self.sale_id.partner_id.service_field_ids:
                    if self.fields_id.code == partner_service_field_id.code:
                        self.value_char = partner_service_field_id.value_char
                        self.value_integer = partner_service_field_id.value_integer
                        self.value_date = partner_service_field_id.value_date
                        self.selection_value_id = partner_service_field_id.selection_value_id.id

    def check_required_fields(self):
        for r in self:
            if r.env.context.get('onchange_sale_service_ids', False):
                continue
            if r.fields_id.type == 'required' and r.value_integer <= 0 and r.fields_type == 'integer':
                raise ValidationError(_("Please fill required fields: %s!!!") % r.fields_id.display_name)
            if r.fields_id.type == 'required' and r.value_char == '' and r.fields_type == 'char':
                raise ValidationError(_("Please fill required fields: %s!!!") % r.fields_id.display_name)
            if r.fields_id.type == 'required' and not r.value_date and r.fields_type == 'date':
                raise ValidationError(_("Please fill required fields: %s!!!") % r.fields_id.display_name)
            if r.fields_id.type == 'required' and not r.selection_value_id and r.fields_type == 'selection':
                raise ValidationError(_("Please fill required fields: %s!!!") % r.fields_id.display_name)

    def write(self, vals):
        res = super(SaleOrderField, self).write(vals)
        if 'value_char' in vals or 'value_integer' in vals or 'value_date' in vals:
            # self.sale_id.action_calculation()
            self.check_required_fields()
        return res

    @api.model
    def create(self, vals_list):
        res = super(SaleOrderField, self).create(vals_list)
        res.check_required_fields()
        return res

    @api.depends('fields_id', 'fields_id.type')
    def _compute_sequence(self):
        for r in self:
            if r.type == 'required':
                r.sequence = 1
            else:
                r.sequence = 0

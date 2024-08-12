from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError
import xlrd, xlwt
import xlsxwriter
import base64
import io as stringIOModule

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
    sale_service_ids = fields.One2many('dpt.sale.service.management', 'sale_id', string='Service')
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
        self.check_required_fields()
        return res

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        self.check_required_fields()
        return res

    def check_required_fields(self):
        for r in self.fields_ids:
            if r.env.context.get('onchange_sale_service_ids', False):
                continue
            if r.fields_id.type == 'options' or (
                    r.fields_id.type == 'required' and (
                    r.value_char or r.value_integer or r.value_date or r.selection_value_id)):
                continue
            else:
                raise ValidationError(_("Please fill required fields!!!"))

    @api.onchange('sale_service_ids')
    def onchange_sale_service_ids(self):
        val = []
        sequence = 0
        list_exist = self.env['sale.order'].browse(self.id.origin).fields_ids.fields_id.ids
        list_onchange = [item.fields_id.id for item in self.fields_ids]
        list_sale_service_id = []
        for sale_service_id in self.sale_service_ids:
            if sale_service_id.service_id.id in list_sale_service_id:
                continue
            for required_fields_id in sale_service_id.service_id.required_fields_ids:
                if required_fields_id.id in list_exist:
                    for field_data in self.env['sale.order'].browse(self.id.origin).fields_ids:
                        if field_data.fields_id.id == required_fields_id.id:
                            val.append({
                                'sequence': 1 if field_data.type == 'required' else 0,
                                'fields_id': required_fields_id.id,
                                'sale_id': self.id,
                                'value_char': field_data.value_char,
                                'value_integer': field_data.value_integer,
                                'value_date': field_data.value_date,
                                'selection_value_id': field_data.selection_value_id.id,

                            })
                elif required_fields_id.id in list_onchange:
                    for field_data in self.fields_ids:
                        if field_data.fields_id.id == required_fields_id.id:
                            val.append({
                                'sequence': 1 if field_data.type == 'required' else 0,
                                'fields_id': required_fields_id.id,
                                'sale_id': self.id,
                                'value_char': field_data.value_char,
                                'value_integer': field_data.value_integer,
                                'value_date': field_data.value_date,
                                'selection_value_id': field_data.selection_value_id.id,

                            })
                if val:
                    result = [item for item in val if item['fields_id'] == required_fields_id.id]
                    if not result:
                        x = {
                            'sequence': 1 if required_fields_id.type == 'required' else 0,
                            'fields_id': required_fields_id.id,
                        }
                        default_value = required_fields_id.get_default_value(so=self)
                        if default_value:
                            x.update(default_value)
                        val.append(x)
                else:
                    x = {
                        'sequence': 1 if required_fields_id.type == 'required' else 0,
                        'fields_id': required_fields_id.id,
                    }
                    default_value = required_fields_id.get_default_value(so=self)
                    if default_value:
                        x.update(default_value)
                    val.append(x)
            list_sale_service_id.append(sale_service_id.service_id.id)
        if val:
            val = sorted(val, key=lambda x: x["sequence"], reverse=True)
            self.fields_ids = None
            self.fields_ids = [(0, 0, item) for item in val]
        if not self.sale_service_ids:
            self.fields_ids = [(5, 0, 0)]

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order_id in self:
            if order_id.sale_service_ids.filtered(lambda ss: ss.price_in_pricelist != ss.price):
                raise ValidationError(_('Please approve new price!'))
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
        return res

    def send_quotation_department(self):
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
        # get default based on pricelist
        # for sale_service_id in self.sale_service_ids.filtered(
        #         lambda ss: ss.department_id.id == self.env.user.employee_ids[:1].department_id.id):

        for sale_service_id in self.sale_service_ids:
            if not sale_service_id.uom_id:
                continue
            current_uom_id = sale_service_id.uom_id
            service_price_ids = sale_service_id.service_id.get_active_pricelist(partner_id=self.partner_id)
            if current_uom_id:
                service_price_ids = service_price_ids.filtered(lambda sp: sp.uom_id.id == current_uom_id.id and (sp.partner_id and sp.partner_id.id == self.partner_id.id or not sp.partner_id))
            if not service_price_ids:
                continue
            max_price = 0
            price_list_item_id = None
            compute_value = 0
            compute_uom_id = None
            for service_price_id in service_price_ids:
                if service_price_id.compute_price == 'fixed_price':
                    price = max(service_price_id.currency_id._convert(service_price_id.fixed_price,
                                                                      to_currency=self.env.company.currency_id,
                                                                      company=self.env.company,
                                                                      date=fields.Date.today()),
                                service_price_id.min_amount)
                    if price > max_price:
                        max_price = price
                        price_list_item_id = service_price_id
                elif service_price_id.compute_price == 'percentage':
                    price_base = 0
                    price = 0
                    if service_price_id.percent_based_on == 'product_total_amount':
                        price_base = sum(self.order_line.mapped('price_total'))
                    elif service_price_id.percent_based_on == 'declaration_total_amount':
                        price_base = sum(self.order_line.mapped('declared_unit_total'))
                    if price_base:
                        price = max(service_price_id.currency_id._convert(
                            from_amount=price_base * service_price_id.percent_price / 100,
                            to_currency=self.env.company.currency_id,
                            company=self.env.company,
                            date=fields.Date.today(),
                        ), service_price_id.min_amount)
                    if price and price > max_price:
                        max_price = price
                        price_list_item_id = service_price_id
                elif service_price_id.compute_price == 'table':
                    compute_field_ids = self.fields_ids.filtered(
                        lambda f: f.using_calculation_price and f.service_id.id == sale_service_id.service_id.id)
                    for compute_field_id in compute_field_ids:
                        if not service_price_id.is_accumulated:
                            detail_price_ids = service_price_id.pricelist_table_detail_ids.filtered(lambda
                                                                                                        ptd: ptd.uom_id.id == compute_field_id.uom_id.id and compute_field_id.value_integer >= ptd.min_value and compute_field_id.value_integer <= ptd.max_value)
                            for detail_price_id in detail_price_ids:
                                price = compute_field_id.value_integer * detail_price_id.amount if service_price_id.is_price else detail_price_id.amount
                                price = max(service_price_id.currency_id._convert(
                                    from_amount=price,
                                    to_currency=self.env.company.currency_id,
                                    company=self.env.company,
                                    date=fields.Date.today(),
                                ), service_price_id.min_amount)
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
                                total_price += service_price_id.currency_id._convert(
                                    from_amount=price,
                                    to_currency=self.env.company.currency_id,
                                    company=self.env.company,
                                    date=fields.Date.today(),
                                )
                            if max(total_price, service_price_id.min_amount) > max_price:
                                max_price = max(total_price, service_price_id.min_amount)
                                price_list_item_id = service_price_id
                                compute_value = compute_field_id.value_integer
                                compute_uom_id = compute_field_id.uom_id.id

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
            })

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
        worksheet.insert_image('B2', 'dpt_sale_management/static/src/img/logo.png', {'x_scale': 0.10, 'y_scale': 0.06})
        worksheet.write('C2', 'CÔNG TY TNHH DPT VINA HOLDINGS - 棋速', header_sp_format)
        worksheet.write('C3', 'Địa chỉ văn phòng: Số 6A, Ngõ 183, Hoàng Văn Thái, Khương Trung, Thanh Xuân, Hà Nội')
        worksheet.write('C4', 'MST: 0109366059')
        # Title
        worksheet.merge_range('A5:F5', 'BÁO GIÁ DỊCH VỤ', merge_format)
        worksheet.write('B7', 'Khách hàng:', bold_format)
        worksheet.write('D7', 'Khách hàng:', bold_format)
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
        data.append(('Cuộc vận chuyển nội địa TQ', '', '', ''))
        data.append(('Tổng tiền hàng + cước nội địa TQ', '', '', ''))
        data.append(('Thể tích (m3)', '', '', ''))
        data.append(('Khối lượng (kg)', '', '', ''))
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
        worksheet.merge_range(f'B{start+1}:B{row}', 'Thuế', merge_format)

        # [Báo giá chi tiết]
        # [Báo giá chi tiết] Data
        data = []
        for r in self.order_line:
            data.append((f'Tổng chi phí/{r.product_id.name}', 'VND/sản phẩm', '', ''))
        start = row
        data.append(('Giá trị kê khai dự kiến', 'VND/lô', '', ''))
        data.append(('Thuế NK', 'VND/lô', nk_tax_amount, ''))
        data.append(('Thuế VAT', 'VND/lô', vat_tax_amount, ''))
        data.append(('Phí uỷ thác nhập khẩu', 'VND/lô', '', ''))
        data.append(('Phí đầu mục', 'VND/lô', '', ''))
        data.append(('Phí nâng hạ', 'VND/lô', '', ''))
        data.append(('Cước VC BT-HN (kg)', 'VND/lô', '', ''))
        data.append(('Cước VC BT-HN (m3)', 'VND/lô', '', ''))
        data.append(('Giao hàng chặng cuối', 'VND/lô', '', ''))
        data.append(('Tổng chi phí vận chuyển theo kg', 'VND/lô', '', ''))
        data.append(('Tổng chi phí vận chuyển theo m3', 'VND/lô', '', ''))
        data.append(('Chi phí theo kg', 'VND/kg', '', ''))
        data.append(('Chi phí theo m3', 'VND/m3', '', ''))
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

        worksheet.write(f'B{row+2}', 'Liên hệ:')
        worksheet.write(f'C{row+2}', f'Chuyên viên:')
        worksheet.write(f'C{row+3}', f'SĐT:')
        worksheet.write(f'C{row+4}', f'Email:')
        worksheet.write(f'E{row+2}', 'CÔNG TY TNHH DPT VINA HOLDINGS')
        worksheet.write(f'H7', 'Tỷ giá tệ từ hệ thống:')
        worksheet.write(f'H8', 'Tỷ giá USD từ hệ thống:')

        # Thêm tiêu đề và thông tin công ty
        # worksheet.write('A1', 'CÔNG TY TNHH DPT VINA HOLDINGS', bold)
        # worksheet.write('A2', 'Địa chỉ văn phòng: Số 6A, Ngõ 183, Hoàng Văn Thái, Khương Trung, Thanh Xuân, Hà Nội')
        # worksheet.write('A3', 'MST: 0109366059')
        #
        # # Thêm tiêu đề báo giá
        # worksheet.write('A5', 'BÁO GIÁ DỊCH VỤ', bold)
        # worksheet.write('A6', 'Hiệu lực từ 24/05/2024 đến 31/05/2024 (Thời gian đến 7 ngày)')
        # worksheet.write('A7', '(Tỷ giá áp dụng mức tỷ giá tại ngày thanh toán)')
        #
        # # Thêm thông tin khách hàng
        # worksheet.write('A9', 'Khách hàng:')
        # worksheet.write('A10', 'Mặt hàng:')
        # worksheet.write('A11', 'Địa chỉ:')
        # worksheet.write('A12', 'Tỷ giá tệ từ hệ thống:')
        # worksheet.write('A13', 'Tỷ giá usd từ hệ thống:')
        #
        # # Thêm bảng giá cước
        # worksheet.write('A15', 'Tên hàng hóa', bold)
        # worksheet.write('B15', 'Số lượng', bold)
        # worksheet.write('C15', 'Chi phí (VND)', bold)
        # worksheet.write('D15', 'Note', bold)
        #
        # # Thêm dữ liệu hàng hóa
        # data = [
        #     ['Sản phẩm 1', 10, 13642000],
        #     ['Sản phẩm 2', 20, 27284000],
        #     ['Sản phẩm 3', 15, 20463000],
        #     ['Cước vận chuyển nội địa TQ', '', 544261]
        # ]
        #
        # row = 15
        # for item, quantity, cost in data:
        #     worksheet.write(row, 0, item)
        #     worksheet.write(row, 1, quantity)
        #     worksheet.write(row, 2, cost)
        #     row += 1
        #
        # # Thêm các chi phí khác
        # worksheet.write('A20', 'Tổng tiền hàng + cước nội địa TQ', bold)
        # worksheet.write('B20', '61,933,261')
        #
        # # Thêm thông tin liên hệ
        # worksheet.write('A22', 'Chuyên viên: Nguyễn Phương')
        # worksheet.write('A23', 'Liên hệ: Ngọc Khánh')
        # worksheet.write('A24', 'SĐT: 0936 670 368')
        # worksheet.write('A25', 'Email: dpt.pl1207@gmail.com')
        # stream = stringIOModule.BytesIO()
        # workbook.save(stream)
        workbook.close()
        # xls = stream.getvalue()
        xls = output.getvalue()
        vals = {
            'name': 'Template_ngan_sach' + '.xls',
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

    def write(self, vals):
        res = super(SaleOrderField, self).write(vals)
        if 'value_char' in vals or 'value_integer' in vals or 'value_date' in vals:
            self.sale_id.action_calculation()
        return res

    @api.depends('fields_id', 'fields_id.type')
    def _compute_sequence(self):
        for r in self:
            if r.type == 'required':
                r.sequence = 1
            else:
                r.sequence = 0

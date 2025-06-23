# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from ast import literal_eval
from odoo import fields, models, _, api
import logging
from odoo.exceptions import AccessError, UserError, ValidationError

_logger = logging.getLogger(__name__)


# dunghq

class DptProductBrand(models.Model):
    _name = "dpt.product.brand"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Dpt Product Brand'

    name = fields.Char(string='Name')


class DptProductModel(models.Model):
    _name = "dpt.product.model"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Dpt Product Model'

    name = fields.Char(string='Name')
    brand_id = fields.Many2one('dpt.product.brand', string='Brand')


# dunghq


class DptExportImportGate(models.Model):
    _name = "dpt.export.import.gate"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Dpt Export Import Gate'

    name = fields.Char(string='Name')


class DptExportImport(models.Model):
    _name = "dpt.export.import"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Dpt Export Import'
    _order = 'create_date desc'

    name = fields.Char(string='Title', tracking=True)
    code = fields.Char(string='Code', tracking=True)
    invoice_code = fields.Char(string='Invoice Code', tracking=True)
    sale_id = fields.Many2one('sale.order', string='Sale Order')
    sale_ids = fields.Many2many('sale.order', string='Select Sale Order', tracking=True)
    partner_importer_id = fields.Many2one('res.partner', string='Partner Importer')
    partner_exporter_id = fields.Many2one('res.partner', string='Partner Exporter')
    gate_id = fields.Many2one('dpt.export.import.gate', string='Gate Importer')
    # dunghq
    brand_id = fields.Many2one('dpt.product.brand', string='Brand')
    model_id = fields.Many2one('dpt.product.model', string='Model')
    # dunghq
    user_id = fields.Many2one('res.users', string='User Export/Import', default=lambda self: self.env.user,
                              tracking=True)
    date = fields.Date(required=True, default=lambda self: fields.Date.context_today(self))
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    consultation_date = fields.Date(string='Consultation date')
    clearance_date = fields.Date(string='Ngày thông quan', tracking=True)
    line_ids = fields.One2many('dpt.export.import.line', 'export_import_id', string='Export/Import Line')
    select_line_ids = fields.Many2many('dpt.export.import.line', string='Export/Import Line',
                                       domain=[('export_import_id', '=', False), ('state', '!=', 'draft')])
    dpt_tax_ecus5 = fields.Char(string='VAT ECUS5', tracking=True)
    description = fields.Text(string='Description')
    state = fields.Selection([
        ('draft', 'Nháp nội bộ'),
        ('draft_declaration', 'Nháp hải quan'),
        ('wait_confirm', 'Chờ duyệt nội bộ'),
        ('confirm', 'Đồng ý duyệt nội bộ'),
        ('cancelled', 'Từ chối duyệt nội bộ'),
        ('declared', 'Chính Thức'),
        ('edit', 'Sửa'),
        ('released', 'Giải phóng hàng'),
        # ('consulted', 'Tham vấn'),
        ('back_for_stock', 'Mang hàng về bảo quản'),
        ('cleared', 'Thông Quan'),
        ('edit_ama', 'Sửa AMA'),
        # ('post_control', 'Kiểm tra sau thông quan'),
        # ('cancelled', 'Huỷ')
    ], string='State', default='draft', tracking=True)
    # ('draft', 'Nháp'),
    # ('draft_declaration', 'Nháp hải quan'),
    # ('confirm', 'Xác nhận tờ khai'),
    # ('declared', 'Tờ khai thông quan'),
    # ('released', 'Giải phóng'),
    # ('consulted', 'Tham vấn'),
    # ('post_control', 'Kiểm tra sau thông quan'),
    # ('cancelled', 'Huỷ')

    # - Nháp nội bộ *
    # - Nháp hải quan *
    # - Chờ duyệt nội bộ
    # - Đồng ý duyệt nội bộ *
    # - Từ chối duyệt nội bộ*
    # - Chính thức*
    # - Sửa*
    # - Giải phóng hàng*
    # - Mang hàng vè bảo quản*
    # - Thông quan
    # - Sửa AMA

    declaration_flow = fields.Selection([
        ('red', 'Red'),
        ('yellow', 'Yellow'),
        ('green', 'Green')
    ], string='Declaration Flow', default='red', tracking=True)
    dpt_n_w_kg = fields.Integer(string='Total N.W (KG)', compute="_compute_total_sum_line")
    dpt_g_w_kg = fields.Integer(string='Total G.W (KG)', compute="_compute_total_sum_line")
    total_cubic_meters = fields.Float(string='Total cubic meters', compute="_compute_total_cubic_meters")
    total_package = fields.Char(string='Total package', compute="_compute_total_package_line")
    dpt_amount_tax_import = fields.Monetary(string='Total Amount import', compute="_compute_total_sum_line",
                                            currency_field='currency_id')
    dpt_amount_tax = fields.Monetary(string='Total Amount VAT', compute="_compute_total_sum_line",
                                     currency_field='currency_id')
    dpt_amount_tax_other = fields.Monetary(string='Total Amount Tax Other', currency_field='currency_id',
                                           compute="_compute_total_sum_line")
    dpt_total_line = fields.Integer(string='Total line', compute="_compute_total_count_line")
    dpt_total_line_new = fields.Integer(string='Total line New', compute="_compute_total_count_line")
    estimated_total_amount = fields.Monetary(string='Estimated total amount', compute="_compute_estimated_total_amount",
                                             currency_field='currency_id')
    actual_total_amount = fields.Monetary(string='Actual total amount', currency_field='currency_id')
    payment_exchange_rate = fields.Float(string='Rate ECUSS', digits=(12, 4))
    shipping_slip = fields.Char(string='Shipping Slip', tracking=True)
    type_of_vehicle = fields.Char(string='Type of vehicle', tracking=True)
    driver_name = fields.Char(string='Driver Name', tracking=True)
    driver_phone_number = fields.Char(string='Driver Phone Number', tracking=True)
    vehicle_license_plate = fields.Char(string='Vehicle License Plate', tracking=True)
    declaration_type = fields.Selection([
        ('usd', 'USD'),
        ('cny', 'CNY')
    ], string='Declaration type', default='usd', tracking=True)
    active = fields.Boolean('Active', default=True)

    def action_draft_declaration(self):
        self.state = 'draft_declaration'
        # for line_id in self.line_ids:
        #     line_id.state = 'draft_declaration'

    # ('draft', 'Nháp'),
    # ('draft_declaration', 'Nháp hải quan'),
    # ('wait_confirm', 'Chờ duyệt nội bộ'),
    # ('confirm', 'Đồng ý duyệt nội bộ'),
    # ('cancelled', 'Từ chối duyệt nội bộ'),
    # ('declared', 'Chính Thức'),
    # ('edit', 'Sửa'),
    # ('released', 'Giải phóng hàng'),
    # ('back_for_stock', 'Mang hàng về bảo quản'),
    # ('cleared', 'Thông Quan'),
    # ('edit_ama', 'Sửa AMA'),

    def action_back_to_draft(self):
        self.state = 'draft'

    def action_sent_to_confirm(self):
        self.action_check_lot_name()
        self.state = 'wait_confirm'
        # for line_id in self.line_ids:
        #     line_id.state = 'draft_declaration'

    def action_confirm(self):
        self.action_check_lot_name()
        self.state = 'confirm'

    def action_declared(self):
        self.action_check_lot_name()
        self.state = 'declared'
        # for line_id in self.line_ids:
        #     line_id.state = 'declared'

    def action_edit(self):
        self.action_check_lot_name()
        self.state = 'edit'

    def action_released(self):
        self.action_check_lot_name()
        self.state = 'released'
        # for line_id in self.line_ids:
        #     line_id.state = 'released'

    def action_back_for_stock(self):
        self.action_check_lot_name()
        self.state = 'back_for_stock'

    def action_cleared(self):
        self.action_check_lot_name()
        self.state = 'cleared'
        # Tự động cập nhật ngày thông quan thành ngày hiện tại nếu chưa có
        if not self.clearance_date:
            self.clearance_date = fields.Date.context_today(self)
        # for line_id in self.line_ids:
        #     line_id.state = 'consulted'

    # def action_post_control(self):
    #     self.state = 'post_control'
    # for line_id in self.line_ids:
    #     line_id.state = 'post_control'

    def action_edit_ama(self):
        self.action_check_lot_name()
        self.state = 'edit_ama'

    def action_cancelled(self):
        self.state = 'cancelled'
        # for line_id in self.line_ids:
        #     line_id.state = 'cancelled'

    def action_check_lot_name(self):
        check = False
        for line_id in self.line_ids:
            if not line_id.stock_picking_ids:
                check = True
        if check:
            raise UserError(f"Chưa được cập nhật mã lô, vui lòng kiểm tra lại!!!")

        # picking_lot_name_ids = self.env['stock.picking'].search(
        #     ['|', ('sale_purchase_id', 'in', self.ids), ('sale_id', 'in', self.ids),
        #      ('state', '!=', 'cancel'), ('picking_lot_name', '=', False)])
        # if picking_lot_name_ids:
        #     picking_lot_name = ','.join(picking_lot_name_ids.mapped('name'))
        #     raise UserError(f"Vận chuyển : {picking_lot_name} chưa được cập nhật mã lô, vui lòng kiểm tra lại!!!")
        #
        # not_picking_lot_name_ids = self.env['stock.picking'].search(
        #     ['|', ('sale_purchase_id', 'in', self.ids), ('sale_id', 'in', self.ids)])
        # if not not_picking_lot_name_ids:
        #     raise UserError(f"Không có phiếu vận chuyển, vui lòng kiểm tra lại!!!")

    @api.depends('sale_ids', 'sale_ids.volume')
    def _compute_total_cubic_meters(self):
        for rec in self:
            total_cubic_meters = 0
            for sale_id in rec.sale_ids:
                total_cubic_meters += sale_id.volume
            rec.total_cubic_meters = total_cubic_meters

    @api.onchange('declaration_type')
    def onchange_update_value_declaration_type(self):
        if self.declaration_type == 'usd':
            exchange_rate = self.env['res.currency'].search([('name', '=', 'USD')])
            self.payment_exchange_rate = exchange_rate.rate
        if self.declaration_type == 'cny':
            exchange_rate = self.env['res.currency'].search([('name', '=', 'CNY')])
            self.payment_exchange_rate = exchange_rate.rate

    @api.onchange('payment_exchange_rate')
    def onchange_update_line_payment_exchange_rate(self):
        for line_id in self.line_ids:
            line_id.dpt_exchange_rate = self.payment_exchange_rate

    @api.onchange('dpt_tax_ecus5')
    def update_dpt_tax_ecus5(self):
        for line_id in self.line_ids:
            line_id.dpt_tax_ecus5 = self.dpt_tax_ecus5

    def write(self, vals):
        old_sale_ids = self.sale_ids
        res = super(DptExportImport, self).write(vals)
        new_sale_ids = self.sale_ids
        sale_ids = old_sale_ids - new_sale_ids
        _logger.info("Removed Sale IDs: %s", sale_ids)
        for sale_id in sale_ids:
            for dpt_export_import_line_id in sale_id.dpt_export_import_line_ids:
                dpt_export_import_line_id.export_import_id = None
        if 'payment_exchange_rate' in vals:
            for line_id in self.line_ids:
                line_id.dpt_exchange_rate = self.payment_exchange_rate
        return res

    @api.onchange('sale_ids')
    def onchange_add_declaration_line(self):
        for order_line_id in self.sale_ids:
            if order_line_id.dpt_export_import_line_ids:
                for dpt_export_import_line_id in order_line_id.dpt_export_import_line_ids:
                    if not dpt_export_import_line_id.export_import_id:
                        dpt_export_import_line_id.export_import_id = self.id

    def action_open_declaration_line(self):
        view_id = self.env.ref('dpt_export_import.view_dpt_export_import_line_tree').id
        view_form_id = self.env.ref('dpt_export_import.view_dpt_export_import_line_form').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.export.import.line',
            'name': _('Declaration Line'),
            'view_mode': 'tree,form',
            'domain': [('export_import_id', '=', self.id)],
            'views': [[view_id, 'tree'], [view_form_id, 'form']],
        }

    @api.depends('dpt_amount_tax_import', 'dpt_amount_tax', 'dpt_amount_tax_other')
    def _compute_estimated_total_amount(self):
        for rec in self:
            rec.estimated_total_amount = rec.dpt_amount_tax + rec.dpt_amount_tax_import + rec.dpt_amount_tax_other

    @api.depends('line_ids', 'line_ids.dpt_is_new')
    def _compute_total_count_line(self):
        for rec in self:
            rec.dpt_total_line = len(rec.line_ids)
            rec.dpt_total_line_new = len(rec.line_ids.filtered(lambda rec: rec.dpt_is_new == True))

    @api.depends('line_ids', 'line_ids.dpt_n_w_kg', 'line_ids.dpt_g_w_kg', 'line_ids.dpt_amount_tax_import',
                 'line_ids.dpt_amount_tax')
    def _compute_total_sum_line(self):
        for rec in self:
            rec.dpt_n_w_kg = sum(line.dpt_n_w_kg for line in rec.line_ids)
            rec.dpt_g_w_kg = sum(line.dpt_g_w_kg for line in rec.line_ids)
            rec.dpt_amount_tax_import = sum(line.dpt_amount_tax_import for line in rec.line_ids)
            rec.dpt_amount_tax_other = sum(line.dpt_amount_tax_other for line in rec.line_ids)
            rec.dpt_amount_tax = sum(line.dpt_amount_tax for line in rec.line_ids)

    def _compute_total_package_line(self):
        for rec in self:
            package_ids = []
            for line_id in rec.line_ids:
                for package_id in line_id.package_ids:
                    package_ids.append(package_id.id)
            if package_ids:
                query = """
                    SELECT string_agg(quantity || ' ' || name, ' + ') AS total_package 
                    FROM (
                        SELECT SUM(quantity) as  quantity, b.name ->>'en_US' as name
                        FROM purchase_order_line_package a 
                        JOIN uom_uom b on a.uom_id = b.id
                        WHERE a.id in %s 
                    GROUP BY b.name) as a
                """
                self.env.cr.execute(query, [tuple(package_ids)])
                result = self.env.cr.dictfetchone()
                rec.total_package = result.get('total_package') or ''
            else:
                rec.total_package = ''

    def action_select_import_line(self):
        view_form_id = self.env.ref('dpt_export_import.dpt_export_import_select_line_form').id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Select Line'),
            'view_mode': 'form',
            'res_model': 'dpt.export.import',
            'target': 'new',
            'res_id': self.id,
            'views': [[view_form_id, 'form']],
        }

    def action_update_import_line(self):
        if self.select_line_ids:
            for select_line_id in self.select_line_ids:
                select_line_id.export_import_id = self.id
                
    def update_tax_to_sale_order(self):
        self.ensure_one()
        
        # 1. Kiểm tra xem tờ khai có liên kết với đơn bán hàng nào không
        if not self.sale_ids:  # THAY ĐỔI: Kiểm tra sale_ids thay vì sale_id
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Cảnh báo'),
                    'message': _('Tờ khai này không liên kết với đơn bán hàng.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }
            
        # 1.1 Kiểm tra xem các đơn bán hàng trong tờ khai có gắn với phiếu hạch toán nào không
        sale_orders_with_invoices = self.sale_ids.filtered(lambda so: so.invoice_ids)
        if sale_orders_with_invoices:
            so_names = ', '.join(sale_orders_with_invoices.mapped('name'))
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Cảnh báo'),
                    'message': _('Không thể cập nhật thuế cho đơn hàng đã có phiếu hạch toán: %s') % so_names,
                    'type': 'warning',
                    'sticky': True,
                }
            }
        
        # 2. Kiểm tra các dòng tờ khai không ở trạng thái eligible hoặc không thuộc sale_ids
        valid_lines = self.line_ids.filtered(lambda l: l.state == 'eligible' and l.sale_id and l.sale_id in self.sale_ids)
        invalid_lines = self.line_ids.filtered(lambda l: l.sale_id in self.sale_ids) - valid_lines
        
        # 3. Hiển thị cảnh báo chi tiết nếu có dòng tờ khai không hợp lệ
        if invalid_lines:
            warning_messages = []
            for line in invalid_lines:
                sale_name = line.sale_id.name if line.sale_id else 'Không có đơn hàng'
                description = line.dpt_description or 'Không có mô tả'
                state_display = dict(line._fields['state'].selection).get(line.state, line.state)
                
                # Thông báo cụ thể hơn
                if line.state != 'eligible':
                    warning_messages.append(_(
                        "Dòng tờ khai '%s' thuộc đơn hàng '%s' đang ở trạng thái '%s', cần ở trạng thái 'Đủ điều kiện khai báo'"
                    ) % (description, sale_name, state_display))
                elif not line.sale_id:
                    warning_messages.append(_(
                        "Dòng tờ khai '%s' không được gán với bất kỳ đơn bán hàng nào"
                    ) % description)
                elif line.sale_id not in self.sale_ids:
                    warning_messages.append(_(
                        "Dòng tờ khai '%s' được gán với đơn hàng '%s' không thuộc danh sách đơn hàng của tờ khai này"
                    ) % (description, sale_name))
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Cảnh báo: Dòng tờ khai không hợp lệ'),
                    'message': '\n\n'.join(warning_messages),
                    'type': 'warning',
                    'sticky': True,
                }
            }
        
        # 4. Nếu không có dòng tờ khai nào thuộc các đơn hàng trong sale_ids
        if not valid_lines:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Cảnh báo'),
                    'message': _('Không có dòng tờ khai hợp lệ nào thuộc các đơn hàng được chọn.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }
        
        # 5. Lấy danh sách các đơn hàng có dòng tờ khai hợp lệ (đã được lọc đúng)
        sale_orders = valid_lines.mapped('sale_id')
        
        # Biến để theo dõi các dịch vụ đã cập nhật
        updated_services = []
        
        # Lưu trạng thái khóa ban đầu của đơn hàng
        locked_orders = {}
        
        # Xử lý cho từng đơn hàng
        for sale_order in sale_orders:
            # Kiểm tra xem đơn hàng có bị khóa không và mở khóa nếu cần
            if sale_order.locked:
                locked_orders[sale_order.id] = True
                sale_order.action_unlock()
            else:
                locked_orders[sale_order.id] = False
            # Tìm các dịch vụ thuế trong đơn hàng
            vat_services = sale_order.sale_service_ids.filtered(
                lambda s: s.service_id.is_vat_service)
            import_tax_services = sale_order.sale_service_ids.filtered(
                lambda s: s.service_id.is_import_tax_service)
            other_tax_services = sale_order.sale_service_ids.filtered(
                lambda s: s.service_id.is_other_tax_service)
            
            # Kiểm tra trường hợp nhiều dịch vụ thuế cùng loại
            warning_messages = []
            
            if len(vat_services) > 1:
                warning_messages.append(_("Đơn hàng %s có %s dịch vụ thuế VAT") % 
                                      (sale_order.name, len(vat_services)))
                                      
            if len(import_tax_services) > 1:
                warning_messages.append(_("Đơn hàng %s có %s dịch vụ thuế NK") % 
                                      (sale_order.name, len(import_tax_services)))
                                      
            if len(other_tax_services) > 1:
                warning_messages.append(_("Đơn hàng %s có %s dịch vụ thuế Khác") % 
                                      (sale_order.name, len(other_tax_services)))
            
            # Kiểm tra trường hợp không có dịch vụ thuế
            if not vat_services:
                warning_messages.append(_("Đơn hàng %s không có dịch vụ thuế VAT") % 
                                      sale_order.name)
                                      
            if not import_tax_services:
                warning_messages.append(_("Đơn hàng %s không có dịch vụ thuế NK") % 
                                      sale_order.name)
                                      
            if not other_tax_services:
                warning_messages.append(_("Đơn hàng %s không có dịch vụ thuế Khác") % 
                                      sale_order.name)
            
            # Hiển thị cảnh báo nếu có
            if warning_messages:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Cảnh báo'),
                        'message': '\n'.join(warning_messages),
                        'type': 'warning',
                        'sticky': True,
                    }
                }
            
            # Lấy các dòng tờ khai hợp lệ thuộc đơn hàng này
            eligible_lines = self.line_ids.filtered(lambda l: l.state == 'eligible' and l.sale_id.id == sale_order.id)
            
            # Tính tổng tiền thuế từ các dòng tờ khai thuộc đơn hàng này
            total_vat = sum(eligible_lines.mapped('dpt_amount_tax_vat_customer'))
            total_import_tax = sum(eligible_lines.mapped('dpt_amount_tax_import_basic'))
            total_other_tax = sum(eligible_lines.mapped('dpt_amount_tax_other_basic'))
            
            # Cập nhật dịch vụ thuế VAT
            if vat_services and total_vat > 0:
                vat_service = vat_services[0]
                old_price = vat_service.price
                vat_service.write({
                    'price': total_vat,
                    'compute_value': 1.0
                })
                updated_services.append({
                    'sale_order': sale_order.name,
                    'name': _('Thuế VAT'),
                    'old_price': old_price,
                    'new_price': total_vat
                })
            
            # Cập nhật dịch vụ thuế NK
            if import_tax_services and total_import_tax > 0:
                import_tax_service = import_tax_services[0]
                old_price = import_tax_service.price
                import_tax_service.write({
                    'price': total_import_tax,
                    'compute_value': 1.0
                })
                updated_services.append({
                    'sale_order': sale_order.name,
                    'name': _('Thuế NK'),
                    'old_price': old_price,
                    'new_price': total_import_tax
                })
            
            # Cập nhật dịch vụ thuế Khác
            if other_tax_services and total_other_tax > 0:
                other_tax_service = other_tax_services[0]
                old_price = other_tax_service.price
                other_tax_service.write({
                    'price': total_other_tax,
                    'compute_value': 1.0
                })
                updated_services.append({
                    'sale_order': sale_order.name,
                    'name': _('Thuế Khác'),
                    'old_price': old_price,
                    'new_price': total_other_tax
                })
        
        # Log thông báo chi tiết về cập nhật
        if updated_services:
            for sale_order in sale_orders:
                # Lọc các dịch vụ đã cập nhật cho đơn hàng này
                order_services = [s for s in updated_services if s['sale_order'] == sale_order.name]
                
                if order_services:
                    message_parts = [_("Đã cập nhật tiền thuế từ tờ khai %s:") % self.name]
                    for service in order_services:
                        message_parts.append(
                            _("- %s: %s → %s") % (
                                service['name'], 
                                format(service['old_price'], '.2f'),
                                format(service['new_price'], '.2f')
                            )
                        )
                    
                    message = "\n".join(message_parts)
                    sale_order.message_post(body=message)
                    
            
            # Khóa lại đơn hàng nếu trước đó đã bị khóa
            for sale_order in sale_orders:
                if locked_orders.get(sale_order.id):
                    sale_order.action_lock()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Thành công'),
                    'message': _('Đã cập nhật tiền thuế từ tờ khai vào các dịch vụ thuế trong đơn hàng.'),
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Thông báo'),
                    'message': _('Không có dịch vụ thuế nào được cập nhật.'),
                    'type': 'info',
                    'sticky': False,
                }
            }

    def action_update_exchange_rates(self):
        """
        Cập nhật tỉ giá tờ khai và tỉ giá ngân hàng (XHĐ) dựa trên ngày thông quan.
        - Tỉ giá tờ khai: Lấy từ nhóm tiền tệ import_export
        - Tỉ giá ngân hàng (XHĐ): Lấy từ nhóm tiền tệ basic
        """
        self.ensure_one()
        if not self.clearance_date:
            raise UserError(_("Vui lòng thiết lập ngày thông quan trước khi cập nhật tỷ giá."))
        
        # Khởi tạo biến để theo dõi số dòng được cập nhật
        updated_lines = 0
        
        # Xử lý từng dòng tờ khai
        for line in self.line_ids:
            declaration_type = line.declaration_type
            if not declaration_type:
                continue
                
            # Lấy tiền tệ tương ứng theo loại khai báo
            currency_code = {
                'usd': 'USD',
                'cny': 'CNY',
                'krw': 'KRW',
            }.get(declaration_type)
            
            if not currency_code:
                continue
                
            # Tìm tỉ giá nhóm import_export (hải quan) gần nhất trước ngày thông quan
            customs_currency = self.env['res.currency'].search([
                ('category', '=', 'import_export'), 
                ('category_code', '=', currency_code)
            ], limit=1)
            
            if customs_currency:
                customs_rate_record = self.env['res.currency.rate'].search([
                    ('currency_id', '=', customs_currency.id),
                    ('name', '<=', self.clearance_date)
                ], order='name desc', limit=1)
                
                if customs_rate_record:
                    line.dpt_exchange_rate = customs_rate_record.company_rate
            
            # Tìm tỉ giá nhóm basic (ngân hàng - XHĐ) gần nhất trước ngày thông quan
            basic_currency = self.env['res.currency'].search([
                ('category', '=', 'basic'), 
                ('category_code', '=', currency_code)
            ], limit=1)
            
            if basic_currency:
                basic_rate_record = self.env['res.currency.rate'].search([
                    ('currency_id', '=', basic_currency.id),
                    ('name', '<=', self.clearance_date)
                ], order='name desc', limit=1)
                
                if basic_rate_record:
                    line.dpt_exchange_rate_basic = basic_rate_record.company_rate
                    line.dpt_exchange_rate_basic_final = basic_rate_record.company_rate
            
            updated_lines += 1
        
        # Hiển thị thông báo xác nhận
        if updated_lines > 0:
            msg = _("Đã cập nhật tỷ giá cho %s dòng tờ khai theo ngày thông quan: %s") % (
                updated_lines, 
                fields.Date.to_string(self.clearance_date)
            )
            self.message_post(body=msg)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Thành công'),
                    'message': msg,
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Cảnh báo'),
                    'message': _('Không có dòng tờ khai nào được cập nhật.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }

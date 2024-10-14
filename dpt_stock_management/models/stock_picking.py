# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, fields, api, _
import xlrd, xlwt
import math
import base64
from odoo.exceptions import ValidationError, UserError
import io as stringIOModule


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    _rec_name = 'picking_lot_name'

    transfer_code = fields.Char('Transfer Code')
    transfer_code_chinese = fields.Char('Transfer Code in Chinese')
    package_ids = fields.One2many('purchase.order.line.package', 'picking_id', 'Packages')
    move_ids_product = fields.One2many('stock.move', 'picking_id', string="Stock move",
                                       domain=[('is_package', '=', False)], copy=False)
    picking_in_id = fields.Many2one('stock.picking', 'Picking In', copy=True)
    picking_out_ids = fields.One2many('stock.picking', 'picking_in_id', 'Picking Out')
    num_picking_out = fields.Integer('Num Picking Out', compute="_compute_num_picking_out")
    finish_create_picking = fields.Boolean('Finish Create Picking', compute="_compute_finish_create_picking")
    packing_lot_name = fields.Char('Packing Lot name', compute="compute_packing_lot_name", store=True)
    is_main_incoming = fields.Boolean('Is Main Incoming', compute="_compute_main_incoming",
                                      search="search_main_incoming")
    is_main_outgoing = fields.Boolean('Is Main Outgoing', compute="_compute_main_outgoing",
                                      search="search_main_outgoing")
    total_volume = fields.Float('Total Volume (m3)', digits=(12, 3), compute="_compute_total_volume_weight", store=True)
    total_weight = fields.Float('Total Weight (kg)', digits=(12, 2), compute="_compute_total_volume_weight", store=True)

    # re-define for translation
    name = fields.Char(
        'Picking Name', default='/',
        copy=False, index='trigram', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', compute='_compute_state',
        copy=False, index=True, readonly=True, store=True, tracking=True,
        help=" * Draft: The transfer is not confirmed yet. Reservation doesn't apply.\n"
             " * Waiting another operation: This transfer is waiting for another operation before being ready.\n"
             " * Waiting: The transfer is waiting for the availability of some products.\n(a) The shipping policy is \"As soon as possible\": no product could be reserved.\n(b) The shipping policy is \"When all products are ready\": not all the products could be reserved.\n"
             " * Ready: The transfer is ready to be processed.\n(a) The shipping policy is \"As soon as possible\": at least one product has been reserved.\n(b) The shipping policy is \"When all products are ready\": all product have been reserved.\n"
             " * Done: The transfer has been processed.\n"
             " * Cancelled: The transfer has been cancelled.")
    partner_id = fields.Many2one(
        'res.partner', 'Supplier',
        check_company=True, index='btree_not_null')
    scheduled_date = fields.Datetime(
        'Scheduled Date', compute='_compute_scheduled_date', inverse='_set_scheduled_date', store=True,
        index=True, default=fields.Datetime.now, tracking=True,
        help="Scheduled time for the first part of the shipment to be processed. Setting manually a value here would set it as expected date for all the stock moves.")

    sale_service_ids = fields.One2many('dpt.sale.service.management', 'picking_id', 'Sale Service')
    fields_ids = fields.One2many('dpt.sale.order.fields', 'picking_id', 'Fields')
    exported_label = fields.Boolean('Exported Label')
    picking_lot_name = fields.Char('Picking Lot Name')

    @api.model
    def action_update_old_package_information(self):
        for item in self:
            item.package_ids.onchange_volume()
            item.package_ids.onchange_weight()
            item.package_ids._onchange_total_fields()

    @api.depends('package_ids.total_volume', 'package_ids.total_weight')
    def _compute_total_volume_weight(self):
        for item in self:
            item.total_volume = math.ceil(round(sum(item.package_ids.mapped('total_volume')) * 100, 4)) / 100
            item.total_weight = math.ceil(round(sum(item.package_ids.mapped('total_weight')), 2))

    def _compute_main_incoming(self):
        for item in self:
            item.is_main_incoming = item.picking_type_code == 'incoming' and item.location_dest_id.warehouse_id.is_main_incoming_warehouse

    @api.onchange('picking_type_code', 'location_dest_id')
    def _onchange_main_incoming(self):
        for item in self:
            item.is_main_incoming = item.picking_type_code == 'incoming' and item.location_dest_id.warehouse_id.is_main_incoming_warehouse

    def search_main_incoming(self, operator, value):
        domain = []
        main_warehouse_ids = self.env['stock.warehouse'].sudo().search([('is_main_incoming_warehouse', '=', True)])
        if (operator == '=' and value) or (operator == '!=' and not value):
            domain = [('picking_type_code', '=', 'incoming'),
                      ('location_dest_id.warehouse_id', 'in', main_warehouse_ids.ids)]
        if (operator == '!=' and value) or (operator == '=' and not value):
            domain = ['|', ('picking_type_code', '!=', 'incoming'),
                      ('location_dest_id.warehouse_id', 'not in', main_warehouse_ids.ids)]
        return domain

    def _compute_main_outgoing(self):
        for item in self:
            item.is_main_outgoing = item.picking_type_code == 'outgoing' and item.location_id.warehouse_id.is_main_incoming_warehouse

    @api.onchange('picking_type_code', 'location_id')
    def _onchange_main_outgoing(self):
        for item in self:
            item.is_main_outgoing = item.picking_type_code == 'outgoing' and item.location_id.warehouse_id.is_main_incoming_warehouse

    def search_main_outgoing(self, operator, value):
        domain = []
        main_warehouse_ids = self.env['stock.warehouse'].sudo().search([('is_main_incoming_warehouse', '=', True)])
        if (operator == '=' and value) or (operator == '!=' and not value):
            domain = [('picking_type_code', '=', 'outgoing'),
                      ('location_id.warehouse_id', 'in', main_warehouse_ids.ids)]
        if (operator == '!=' and value) or (operator == '=' and not value):
            domain = ['|', ('picking_type_code', '!=', 'outgoing'),
                      ('location_id.warehouse_id', 'not in', main_warehouse_ids.ids)]
        return domain

    @api.depends('package_ids.quantity', 'package_ids.uom_id.packing_code')
    def compute_packing_lot_name(self):
        for item in self:
            item.packing_lot_name = '.'.join(
                [f"{package_id.quantity}{package_id.uom_id.packing_code}" for package_id in
                 item.package_ids if package_id.uom_id.packing_code])

    def _compute_num_picking_out(self):
        for item in self:
            item.num_picking_out = len(item.picking_out_ids)

    def _compute_finish_create_picking(self):
        for item in self:
            item.finish_create_picking = all(
                [package_id.quantity == package_id.created_picking_qty for package_id in item.package_ids])

    @api.model
    def create(self, vals):
        res = super(StockPicking, self).create(vals)
        res.check_required_fields()
        res.action_update_picking_name()
        res.constrains_package()
        # auto assign picking
        res.action_confirm()
        # for picking in res:
        #     if picking.x_transfer_type != 'outgoing_transfer':
        #         continue
        #     picking.create_in_transfer_picking()
        return res

    @api.constrains('package_ids')
    def constrains_package(self):
        if self.is_main_incoming:
            # remove package move
            package_move_ids = self.move_ids_without_package - self.move_ids_product
            package_move_ids.unlink()
            if self.purchase_id:
                self.package_ids.update({
                    'purchase_id': self.purchase_id.id
                })
            # create package move
            self.package_ids._create_stock_moves(self)

    def action_confirm(self):
        if self.is_main_incoming or (
                self.x_transfer_type == 'outgoing_transfer' and self.location_id.warehouse_id.is_main_incoming_warehouse):
            # auto create move line with lot name is picking name
            self.move_line_ids.unlink()
            move_line_vals = []
            for move_id in self.move_ids_without_package:
                if move_id.product_id.tracking != 'lot':
                    continue
                move_line_vals.append({
                    'move_id': move_id.id,
                    'picking_id': self.id,
                    'location_id': move_id.location_id.id,
                    'location_dest_id': move_id.location_dest_id.id,
                    'product_id': move_id.product_id.id,
                    'quantity': move_id.product_uom_qty,
                    'product_uom_id': move_id.product_uom.id,
                    'lot_name': self.picking_lot_name if self.is_main_incoming else None,
                    'lot_id': self.env['stock.lot'].search(
                        [('product_id', '=', move_id.product_id.id), ('name', '=', self.picking_lot_name)])[
                              :1].id if not self.is_main_incoming and self.picking_lot_name else None
                })
            if move_line_vals:
                self.env['stock.move.line'].create(move_line_vals)
        if self.picking_type_code == 'outgoing' and not self.location_id.warehouse_id.is_main_incoming_warehouse:
            # auto create move line with lot name is picking name
            self.move_line_ids.unlink()
            move_line_vals = []
            for move_id in self.move_ids_without_package:
                if move_id.product_id.tracking != 'lot':
                    continue
                move_line_vals.append({
                    'move_id': move_id.id,
                    'picking_id': self.id,
                    'location_id': move_id.location_id.id,
                    'location_dest_id': move_id.location_dest_id.id,
                    'product_id': move_id.product_id.id,
                    'quantity': move_id.product_uom_qty,
                    'product_uom_id': move_id.product_uom.id,
                    'lot_id': self.env['stock.lot'].search([('product_id', '=', move_id.product_id.id),
                                                            ('name', '=', move_id.from_picking_id.picking_lot_name)],
                                                           limit=1).id
                })
            if move_line_vals:
                self.env['stock.move.line'].create(move_line_vals)

        # update back to export import
        if self.x_transfer_type == 'outgoing_transfer' and self.location_id.warehouse_id.is_main_incoming_warehouse:
            for order_line in self.sale_purchase_id.order_line:
                order_line.dpt_export_import_line_ids.write({'lot_code': self.picking_lot_name})
                package_ids = self.package_ids.filtered(
                    lambda p: order_line.product_id.id in p.detail_ids.mapped('product_id').ids)
                if not package_ids:
                    continue
                order_line.dpt_export_import_line_ids.package_ids = order_line.dpt_export_import_line_ids.package_ids | package_ids
        return super().action_confirm()

    def action_update_picking_name(self):
        # getname if it is incoming picking in Chinese stock
        if self.is_main_incoming:
            prefix = f'KT{datetime.now().strftime("%y%m%d")}'
            nearest_picking_id = self.env['stock.picking'].sudo().search(
                [('picking_lot_name', 'ilike', prefix + "%"), ('id', '!=', self.id),
                 ('location_dest_id.warehouse_id', '=', self.location_dest_id.warehouse_id.id),
                 ('picking_type_id.code', '=', self.picking_type_code)], order='id desc').filtered(
                lambda sp: '.' not in sp.picking_lot_name)
            if nearest_picking_id:
                number = int(nearest_picking_id[:1].picking_lot_name[8:])
                self.picking_lot_name = prefix + str(number + 1).zfill(3)
            else:
                self.picking_lot_name = prefix + '001'
        if self.picking_type_code == 'outgoing' or self.x_transfer_type == 'outgoing_transfer':
            if not self.picking_in_id:
                return self
            if sum(self.picking_in_id.package_ids.mapped('quantity')) > sum(self.package_ids.mapped('quantity')):
                # get last picking out of this picking in
                last_picking_out_id = self.picking_in_id.picking_out_ids.filtered(lambda sp: sp.id != self.id).sorted(
                    key=lambda r: r.id)[:1]
                if last_picking_out_id and '.' in last_picking_out_id.picking_lot_name:
                    num = int(last_picking_out_id.picking_lot_name.split('.')[-1])
                    self.picking_lot_name = self.picking_in_id.picking_lot_name + f".{num + 1}"
                else:
                    self.picking_lot_name = self.picking_in_id.picking_lot_name + ".1"
            else:
                self.picking_lot_name = self.picking_in_id.picking_lot_name
        if self.x_transfer_type == 'incoming_transfer':
            transfer_picking_out_id = self.env['stock.picking'].sudo().search(
                [('x_in_transfer_picking_id', '=', self.id)], limit=1)
            if not transfer_picking_out_id:
                return self
            self.picking_lot_name = transfer_picking_out_id.picking_lot_name

    def action_create_transfer_picking(self):
        # condition cutlift
        other_warehouse_id = self.env['stock.warehouse'].sudo().search(
            [('id', '!=', self.location_dest_id.warehouse_id.id)], limit=1)
        if not other_warehouse_id:
            return
        picking_type_id = self.env['stock.picking.type'].sudo().search(
            [('warehouse_id', '=', other_warehouse_id.id), ('code', '=', 'internal')])
        if not picking_type_id:
            return
        transit_location_id = self.env['stock.location'].sudo().search(
            [('usage', '=', 'transit'), ('company_id', '=', self.env.company.id)], limit=1)
        return {
            'name': _('Create Transfer'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'target': 'new',
            'view_mode': 'form',
            'views': [(self.env.ref('stock.view_picking_form').sudo().id, "form")],
            'context': {
                'default_picking_in_id': self.id,
                # 'default_x_location_id': self.location_dest_id.id,
                # 'default_x_location_dest_id': other_warehouse_id.lot_stock_id.id,
                'default_location_id': self.location_dest_id.id,
                'default_location_dest_id': transit_location_id.id,
                'default_picking_type_id': picking_type_id.id,
                'default_x_transfer_type': 'outgoing_transfer',
                'default_partner_id': self.partner_id.id,
                'default_sale_purchase_id': self.sale_purchase_id.id,
                'default_move_ids_without_package': [(0, 0, {
                    'location_id': self.location_dest_id.id,
                    'location_dest_id': transit_location_id.id,
                    'name': (move_line_id.product_id.display_name or '')[:2000],
                    'product_id': move_line_id.product_id.id,
                    'product_uom_qty': move_line_id.product_uom_qty,
                    'product_uom': move_line_id.product_uom.id,
                }) for move_line_id in self.move_ids_without_package],
                'default_package_ids': [(0, 0, {
                    'quantity': package_id.quantity - package_id.created_picking_qty,
                    'length': package_id.length,
                    'width': package_id.width,
                    'height': package_id.height,
                    'size': package_id.size,
                    'weight': package_id.weight,
                    'total_weight': package_id.total_weight * (package_id.quantity - package_id.created_picking_qty) / package_id.quantity,
                    'volume': package_id.volume,
                    'total_volume': package_id.total_volume * (package_id.quantity - package_id.created_picking_qty) / package_id.quantity,
                    'uom_id': package_id.uom_id.id,
                    'detail_ids': [(0, 0, {
                        'product_id': detail_id.product_id.id,
                        'uom_id': detail_id.uom_id.id,
                        'quantity': detail_id.quantity,
                    }) for detail_id in package_id.detail_ids],
                }) for package_id in self.package_ids if package_id.quantity - package_id.created_picking_qty != 0]
            }
        }

    def action_view_picking_out(self):
        view_id = self.env.ref('stock.vpicktree').id
        view_form_id = self.env.ref('stock.view_picking_form').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'name': _('Deposit'),
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.picking_out_ids.ids)],
            'views': [[view_id, 'tree'], [view_form_id, 'form']],
        }

    def export_wrong_import_data(self):
        data = [1, 2, 3, 4, 5]
        workbook = xlwt.Workbook(encoding="UTF-8")
        worksheet = workbook.add_sheet("Ngân sách")
        xlwt.add_palette_colour('gray_lighter', 0x21)
        workbook.set_colour_RGB(0x21, 224, 224, 224)
        style_blue = xlwt.easyxf(
            'font: bold on, name Times New Roman, height 249; pattern: pattern solid, fore_colour pale_blue;'
            'borders: left thin, right thin, top thin, bottom thin;'
        )
        style_blue_3 = xlwt.easyxf(
            'font: bold on, name Times New Roman, height 249; pattern: pattern solid, fore_colour pale_blue;'
            'borders: left thin, right thin, top thin, bottom thin; align: horiz centre, vert centre'
        )
        style_blue_2 = xlwt.easyxf(
            'font: name Times New Roman, height 219; pattern: pattern solid, fore_colour white;'
            'align: wrap on, horiz left; borders: left thin, right thin, top thin, bottom thin;'
        )
        style_red = xlwt.easyxf(
            'font: bold on, name Times New Roman, height 269, colour_index red; align: horiz centre, vert centre;'
        )
        style_normal = xlwt.easyxf(
            'font: name Times New Roman, height 229;'
        )
        style_normal.num_format_str = '#,##0'
        style_total = xlwt.easyxf(
            'font: bold on, name Times New Roman, height 249'
        )
        style_total.num_format_str = '#,##0'
        row = 2
        for r in self.package_ids:
            val = \
                f"Tên hàng: {r.uom_id.name}\n" \
                f"Kiểu mẫu: {r.uom_id.name} - Nhãn hiệu: ... - Ký hiệu: ....\n" \
                f"Kích thước/Dung tích/Chất liệu: {r.size}/{r.volume}/" \
                f"Ngày/Tháng/năm sản xuất: \n" \
                f"Trọng lượng: {r.weight} \n" \
                f"Nhà sản xuất: {self.partner_id.name}\n" \
                f"Địa chỉ nhà sản xuất: {self.partner_id.street or ''}\n" \
                f"Nhà nhập khẩu: CÔNG TY TNHH DPT VINA HOLDINGS\n" \
                f"Địa chỉ nhà nhập khẩu: Liền kề NTT38, Số 82 Nguyễn Tuân, Phường Thanh Xuân Trung, Quận Thanh Xuân, Thành phố Hà Nội\n" \
                f"XUẤT XỨ: TRUNG QUỐC\n" \
                f"{self.packing_lot_name or ''}\n" \
                f"<Mã lô (QR)>"

            val2 = f"Description of goods: {r.uom_id.name}\n" \
                   f"Model: {r.uom_id.name} - Brand: ... - Symbol: .... \n" \
                   f"Dimensions/Capacity/Material: {r.size}/{r.volume}/ \n" \
                   f"Manufacturing date: \n" \
                   f"N.W/ G.W: {r.weight}\n" \
                   f"Manufacturer: {self.partner_id.name} \n" \
                   f"Address: {self.partner_id.street or ''} \n" \
                   f"Importer: DPT VINA HOLDINGS CO., LTD\n" \
                   f"Address: Apartment NTT38, No. 82, Nguyen Tuan Street, Thanh Xuan Trung Ward, Thanh Xuan District, Hanoi City, Vietnam\n" \
                   f"MADE IN CHINA\n" \
                   f"{self.packing_lot_name or ''}\n" \
                   f"<Mã lô (QR)>"

            worksheet.row(row).height = 256 * 2
            worksheet.col(0).width = 128 * 200
            worksheet.col(1).width = 128 * 200
            worksheet.write(row, 0, val, style_blue_2)
            worksheet.write(row, 1, val2, style_blue_2)
            row += 1
        stream = stringIOModule.BytesIO()
        workbook.save(stream)
        xls = stream.getvalue()
        vals = {
            'name': f'Tem_phu_{self.name}' + '.xls',
            'datas': base64.b64encode(xls),
            # 'datas_fname': 'Template_ngan_sach.xls',
            'type': 'binary',
            'res_model': self._name,
            'res_id': self.id,
        }
        file_xls = self.env['ir.attachment'].create(vals)
        # self.exported_label = True
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/' + str(file_xls.id) + '?download=true',
            'target': 'new',
        }

    @api.constrains('sale_purchase_id', 'sale_service_ids', 'fields_ids')
    def constrains_update_sale_service(self):
        for item in self:
            for sale_service_id in item.sale_service_ids:
                sale_service_id.write({
                    'sale_id': item.sale_purchase_id.id
                })
            for fields_id in item.fields_ids:
                fields_id.write({
                    'sale_id': item.sale_purchase_id.id
                })

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        picking = super(StockPicking, self).copy(default)
        picking.sale_service_ids = self.sale_service_ids
        picking.fields_ids = self.fields_ids
        return picking

    def write(self, vals):
        res = super(StockPicking, self).write(vals)
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
        list_exist = self.env['stock.picking'].browse(self.id.origin).fields_ids.fields_id.ids
        list_onchange = [item.fields_id.id for item in self.fields_ids]
        list_sale_service_id = []
        for sale_service_id in self.sale_service_ids:
            if sale_service_id.service_id.id in list_sale_service_id:
                continue
            for required_fields_id in sale_service_id.service_id.required_fields_ids:
                if required_fields_id.id in list_exist:
                    for field_data in self.env['stock.picking'].browse(self.id.origin).fields_ids:
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
                        default_value = required_fields_id.get_default_value(so=self.sale_purchase_id)
                        if default_value:
                            x.update(default_value)
                        val.append(x)
                else:
                    x = {
                        'sequence': 1 if required_fields_id.type == 'required' else 0,
                        'fields_id': required_fields_id.id,
                    }
                    default_value = required_fields_id.get_default_value(so=self.sale_purchase_id)
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

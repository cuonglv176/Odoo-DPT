from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ServiceCombo(models.Model):
    _name = 'dpt.sale.order.service.combo'
    _description = 'Combo dịch vụ'
    _rec_name = 'combo_id'

    combo_id = fields.Many2one('dpt.service.combo', string='Combo', 
                              domain="[('state', '=', 'active')]")
    code = fields.Char('Mã combo', related='combo_id.code')
    description = fields.Text('Mô tả')
    service_ids = fields.Many2many('dpt.service.management', string='Dịch vụ trong combo',
                                   related='combo_id.service_ids')
    sale_id = fields.Many2one('sale.order', string='Order')
    planned_sale_id = fields.Many2one('sale.order', string='Planned Order')
    qty = fields.Integer('Số lượng', default=1)
    price = fields.Float('Đơn giá', help='Để trống sẽ tính tổng từ các dịch vụ')
    amount_discount = fields.Float('Khuyến mãi', default=0.0)
    amount_total = fields.Float('Thành tiền', compute='_compute_total_price')
    sale_service_ids = fields.One2many('dpt.sale.service.management', 'combo_id', 'Chi tiết dịch vụ')

    # Thay đổi trường is_price_fixed thành trường độc lập (không phải related field)
    is_price_fixed = fields.Boolean(string='Đã chốt giá', copy=False, tracking=True,
                                    help='Đánh dấu combo dịch vụ đã được chốt giá với khách')
    locked_price = fields.Float('Giá đã khóa', copy=False)
    
    # Thêm trường cho phân bổ chi phí
    combo_compute_uom_id = fields.Many2one('uom.uom', string='Đơn vị',
                                          help='Đơn vị tính dùng để phân bổ chi phí')
    combo_compute_value = fields.Float(string='Số lượng', default=1.0,
                                      help='Giá trị dùng để phân bổ chi phí')

    # Para almacenar temporalmente los servicios durante la creación
    _services_to_create = {}

    @api.onchange('combo_id')
    def onchange_combo_id(self):
        if self.combo_id:
            self.price = self.combo_id.price
            # Crear los servicios automáticamente cuando se cambia el combo
            if self.combo_id.service_ids:
                new_services = []
                services = self.get_combo_services()

                # Xác định đơn đặt hàng liên quan (thực tế hoặc dự kiến)
                related_sale_id = self.sale_id.id if self.sale_id else False
                related_planned_sale_id = self.planned_sale_id.id if self.planned_sale_id else False

                for service_data in services:
                    service_vals = {
                        'service_id': service_data['service_id'],
                        'price': service_data['price'],
                        'uom_id': service_data['uom_id'],
                        'qty': service_data['qty'],
                        'compute_value': self.qty or 1,  # Sử dụng số lượng combo
                        'combo_id': self.id if not self._origin.id else self._origin.id,
                        'price_status': 'calculated',
                        'department_id': service_data['department_id'],
                        'is_price_fixed': self.is_price_fixed,  # Kế thừa trạng thái chốt giá từ combo
                    }

                    # Gán đúng trường đơn hàng (thực tế hoặc dự kiến)
                    if related_sale_id:
                        service_vals['sale_id'] = related_sale_id
                    if related_planned_sale_id:
                        service_vals['planned_sale_id'] = related_planned_sale_id

                        # Nếu đã chốt giá, lưu giá hiện tại vào trường locked_price
                        if self.is_price_fixed:
                            service_vals['locked_price'] = service_data['price']

                    new_services.append((0, 0, service_vals))

                if new_services:
                    # Guardar los servicios para crearlos después de guardar si es un nuevo registro
                    if not self._origin.id:
                        self._services_to_create[self.id] = new_services
                    self.sale_service_ids = [(5, 0, 0)] + new_services

    # Thêm onchange cho trường qty - cập nhật số lượng dịch vụ khi số lượng combo thay đổi
    @api.onchange('qty')
    def onchange_qty(self):
        """Cập nhật số lượng cho các dịch vụ khi thay đổi số lượng combo"""
        if self.qty and self.sale_service_ids:
            for service in self.sale_service_ids:
                service.compute_value = self.qty

    # Thêm onchange cho trường is_price_fixed
    @api.onchange('is_price_fixed')
    def _onchange_is_price_fixed(self):
        """Khi thay đổi trạng thái chốt giá của combo, cập nhật cho tất cả dịch vụ thuộc combo"""
        for combo in self:
            # Nếu combo đã chốt giá, khóa giá hiện tại
            if combo.is_price_fixed and not combo.locked_price and combo.price > 0:
                combo.locked_price = combo.price

            # Cập nhật trạng thái chốt giá cho tất cả dịch vụ thuộc combo
            for service in combo.sale_service_ids:
                service.is_price_fixed = combo.is_price_fixed
                # Nếu đã chốt giá, lưu giá hiện tại của dịch vụ
                if combo.is_price_fixed and not service.locked_price and service.price > 0:
                    service.locked_price = service.price

    @api.model_create_multi
    def create(self, vals_list):
        records = super(ServiceCombo, self).create(vals_list)
        # Crear servicios para cada nuevo registro
        for record in records:
            if record.combo_id and record.combo_id.service_ids:
                services = record.get_combo_services()
                new_services = []

                # Xác định đơn đặt hàng liên quan (thực tế hoặc dự kiến)
                related_sale_id = record.sale_id.id if record.sale_id else False
                related_planned_sale_id = record.planned_sale_id.id if record.planned_sale_id else False

                for service_data in services:
                    service_vals = {
                        'service_id': service_data['service_id'],
                        'price': service_data['price'],
                        'uom_id': service_data['uom_id'],
                        'qty': service_data['qty'],
                        'compute_value': record.qty or 1,  # Sử dụng số lượng combo
                        'combo_id': record.id,
                        'price_status': 'calculated',
                        'department_id': service_data['department_id'],
                        'is_price_fixed': record.is_price_fixed,  # Kế thừa trạng thái chốt giá từ combo
                    }

                    # Gán đúng trường đơn hàng (thực tế hoặc dự kiến)
                    if related_sale_id:
                        service_vals['sale_id'] = related_sale_id
                    if related_planned_sale_id:
                        service_vals['planned_sale_id'] = related_planned_sale_id

                        # Nếu đã chốt giá, lưu giá hiện tại vào trường locked_price
                        if record.is_price_fixed:
                            service_vals['locked_price'] = service_data['price']

                    new_services.append(service_vals)

                if new_services:
                    self.env['dpt.sale.service.management'].create(new_services)
        return records

    # Ghi đè phương thức write để cập nhật số lượng cho dịch vụ khi số lượng combo thay đổi
    def write(self, vals):
        res = super(ServiceCombo, self).write(vals)

        # Nếu có thay đổi số lượng, cập nhật số lượng cho các dịch vụ
        if 'qty' in vals:
            for combo in self:
                services = self.env['dpt.sale.service.management'].search([
                    ('combo_id', '=', combo.id)
                ])
                for service in services:
                    service.compute_value = vals['qty']

        # Nếu có thay đổi trạng thái chốt giá
        if 'is_price_fixed' in vals:
            for combo in self:
                # Khóa giá nếu đã chốt giá
                if vals['is_price_fixed'] and not combo.locked_price and combo.price > 0:
                    combo.locked_price = combo.price

                # Cập nhật trạng thái chốt giá cho tất cả dịch vụ thuộc combo
                services = self.env['dpt.sale.service.management'].search([
                    ('combo_id', '=', combo.id)
                ])
                for service in services:
                    service_vals = {'is_price_fixed': vals['is_price_fixed']}
                    # Nếu đã chốt giá, lưu giá hiện tại của dịch vụ
                    if vals['is_price_fixed'] and not service.locked_price and service.price > 0:
                        service_vals['locked_price'] = service.price
                    service.write(service_vals)

        return res

    @api.depends('price', 'qty', 'amount_discount', 'sale_service_ids', 'sale_service_ids.amount_total')
    def _compute_total_price(self):
        for record in self:
            if record.price:
                base_price = record.price * record.qty
            else:
                base_price = sum(service.amount_total for service in record.sale_service_ids)
            record.amount_total = base_price - record.amount_discount

    # Thêm ràng buộc khi thay đổi giá
    @api.onchange('price')
    def _onchange_price(self):
        for record in self:
            # Kiểm tra nếu combo này đã chốt giá
            if record.is_price_fixed:
                if record.locked_price > 0 and record.price != record.locked_price:
                    record.price = record.locked_price
                    return {
                        'warning': {
                            'title': _("Cảnh báo"),
                            'message': _("Không thể thay đổi giá khi đã chốt với khách hàng!")
                        }
                    }
                elif not record.locked_price:
                    record.locked_price = record.price

    def get_combo_services(self):
        """Trả về danh sách dịch vụ trong combo"""
        services = []
        for service in self.service_ids:
            services.append({
                'service_id': service.id,
                'price': service.price,
                'uom_id': service.uom_id.id,
                'qty': 1,
                'department_id': service.department_id.id if service.department_id else False,
            })
        return services
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ServiceCombo(models.Model):
    _name = 'dpt.sale.order.service.combo'
    _description = 'Combo dịch vụ'

    combo_id = fields.Many2one('dpt.service.combo', string='Combo')
    code = fields.Char('Mã combo', related='combo_id.code')
    description = fields.Text('Mô tả')
    service_ids = fields.Many2many('dpt.service.management', string='Dịch vụ trong combo',
                                   related='combo_id.service_ids')
    sale_id = fields.Many2one('sale.order', string='Order')
    price = fields.Float('Giá Combo', help='Để trống sẽ tính tổng từ các dịch vụ')
    amount_discount = fields.Float('Giảm giá', default=0.0)
    discount_percent = fields.Float('Phần trăm giảm giá', default=0.0)  # Thêm field thiếu
    amount_total = fields.Float('Tổng', compute='_compute_total_price')
    sale_service_ids = fields.One2many('dpt.sale.service.management', 'combo_id', 'Chi tiết dịch vụ')

    @api.onchange('combo_id')
    def onchange_combo_id(self):
        if self.combo_id:
            self.price = self.combo_id.price

    @api.depends('price', 'discount_percent', 'sale_service_ids', 'sale_service_ids.amount_total')
    def _compute_total_price(self):
        for record in self:
            if record.price:
                base_price = record.price
            else:
                base_price = sum(service.amount_total for service in record.sale_service_ids)
            if record.discount_percent:
                discount_amount = base_price * (record.discount_percent / 100.0)
                record.amount_total = base_price - discount_amount
            else:
                record.amount_total = base_price

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

    @api.onchange('combo_id')
    def onchange_combo_services(self):
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
                        'sale_id': self.sale_id.id,
                        'price_status': 'calculated',
                        'department_id': service_data['department_id'],
                    }))
            if new_services:
                self.sale_service_ids = [(4, service.id) for service in self.sale_service_ids] + new_services
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ServiceCombo(models.Model):
    _name = 'dpt.sale.order.service.combo'
    _description = 'Combo dịch vụ'
    _rec_name = 'combo_id'

    combo_id = fields.Many2one('dpt.service.combo', string='Combo')
    code = fields.Char('Mã combo', related='combo_id.code')
    description = fields.Text('Mô tả')
    service_ids = fields.Many2many('dpt.service.management', string='Dịch vụ trong combo',
                                   related='combo_id.service_ids')
    sale_id = fields.Many2one('sale.order', string='Order')
    price = fields.Float('Giá Combo', help='Để trống sẽ tính tổng từ các dịch vụ')
    amount_discount = fields.Float('Giảm giá', default=0.0)
    amount_total = fields.Float('Tổng', compute='_compute_total_price')
    sale_service_ids = fields.One2many('dpt.sale.service.management', 'combo_id', 'Chi tiết dịch vụ')

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
                for service_data in services:
                    new_services.append((0, 0, {
                        'service_id': service_data['service_id'],
                        'price': service_data['price'],
                        'uom_id': service_data['uom_id'],
                        'qty': service_data['qty'],
                        'combo_id': self.id if not self._origin.id else self._origin.id,
                        'sale_id': self.sale_id.id if self.sale_id else False,
                        'price_status': 'calculated',
                        'department_id': service_data['department_id'],
                    }))
                if new_services:
                    # Guardar los servicios para crearlos después de guardar si es un nuevo registro
                    if not self._origin.id:
                        self._services_to_create[self.id] = new_services
                    self.sale_service_ids = [(5, 0, 0)] + new_services

    @api.model_create_multi
    def create(self, vals_list):
        records = super(ServiceCombo, self).create(vals_list)
        # Crear servicios para cada nuevo registro
        for record in records:
            if record.combo_id and record.combo_id.service_ids:
                services = record.get_combo_services()
                new_services = []
                for service_data in services:
                    new_services.append({
                        'service_id': service_data['service_id'],
                        'price': service_data['price'],
                        'uom_id': service_data['uom_id'],
                        'qty': service_data['qty'],
                        'combo_id': record.id,
                        'sale_id': record.sale_id.id if record.sale_id else False,
                        'price_status': 'calculated',
                        'department_id': service_data['department_id'],
                    })
                if new_services:
                    self.env['dpt.sale.service.management'].create(new_services)
        return records

    @api.depends('price', 'amount_discount', 'sale_service_ids', 'sale_service_ids.amount_total')
    def _compute_total_price(self):
        for record in self:
            if record.price:
                base_price = record.price
            else:
                base_price = sum(service.amount_total for service in record.sale_service_ids)
            record.amount_total = base_price - record.amount_discount

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
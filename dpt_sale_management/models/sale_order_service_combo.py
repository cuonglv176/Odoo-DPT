from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ServiceCombo(models.Model):
    _name = 'dpt.sale.order.service.combo'
    _description = 'Combo dịch vụ'

    name = fields.Char('Tên combo', required=True)
    code = fields.Char('Mã combo', required=True)
    active = fields.Boolean('Hoạt động', default=True)
    description = fields.Text('Mô tả')
    partner_id = fields.Many2one('res.partner', string='Khách hàng',
                                 help='Nếu được chọn, combo này chỉ áp dụng cho khách hàng cụ thể')
    service_ids = fields.Many2many('dpt.service.management', string='Dịch vụ trong combo')
    # Thêm trường service_id để khắc phục lỗi
    service_id = fields.Many2one('dpt.service.management', string='Dịch vụ chính',
                                 help='Dịch vụ đại diện cho combo')
    sale_id = fields.Many2one('sale.order', string='Order')
    # Thông tin giá và tính toán
    price = fields.Float('Giá combo', help='Để trống sẽ tính tổng từ các dịch vụ')
    discount_percent = fields.Float('Giảm giá (%)', default=0.0)
    total_price = fields.Float('Tổng giá sau KM', compute='_compute_total_price')

    @api.constrains('code')
    def _check_code_unique(self):
        for record in self:
            if self.search_count([('code', '=', record.code), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_("Mã combo phải là duy nhất!"))

    @api.depends('price', 'discount_percent', 'service_ids')
    def _compute_total_price(self):
        for combo in self:
            if combo.price:
                combo.total_price = combo.price * (1 - combo.discount_percent / 100)
            else:
                services = combo.get_combo_services()
                total_price = sum(service['price'] for service in services)
                combo.total_price = total_price * (1 - combo.discount_percent / 100)

    def get_combo_services(self):
        """
        Trả về danh sách các dịch vụ trong combo với giá và thông tin
        """
        services = []
        for service in self.service_ids:
            # Lấy giá mặc định từ bảng giá của khách hàng hoặc bảng giá chung
            price = 0
            pricelist_item = self.env['product.pricelist.item'].search([
                ('service_id', '=', service.id),
                ('partner_id', '=', self.partner_id.id)
            ], limit=1) if self.partner_id else False

            if not pricelist_item:
                pricelist_item = self.env['product.pricelist.item'].search([
                    ('service_id', '=', service.id),
                    ('partner_id', '=', False)
                ], limit=1)

            if pricelist_item:
                price = pricelist_item.fixed_price

            services.append({
                'service_id': service.id,
                'price': price,
                'uom_id': service.uom_id.id,
                'qty': 1.0,
                'department_id': service.department_id.id,
            })

        return services

    @api.onchange('service_ids')
    def onchange_service_ids(self):
        """
        Khi thay đổi danh sách dịch vụ, tự động chọn dịch vụ đầu tiên làm dịch vụ chính
        """
        if self.service_ids and not self.service_id:
            self.service_id = self.service_ids[0]
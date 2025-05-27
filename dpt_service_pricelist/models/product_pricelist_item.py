from odoo import fields, models, api, _


class MailMessage(models.Model):
    _inherit = 'mail.message'

    @api.model
    def create(self, vals_list):
        res = super(MailMessage, self).create(vals_list)
        if res.model and res.model in ('product.pricelist.item', 'product.pricelist.item.detail'):
            obj_data = self.env[res.model].browse(res.res_id)
            res.res_id = obj_data.service_id.id
            res.model = 'dpt.service.management'
        return res


class ProductPricelistItem(models.Model):
    _name = 'product.pricelist.item'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin', 'product.pricelist.item']

    partner_id = fields.Many2one('res.partner', 'Customer', domain=[('customer_rank', '>', 0)], tracking=True)
    service_id = fields.Many2one('dpt.service.management', 'Service', tracking=True, copy=True)
    combo_id = fields.Many2one('dpt.service.combo', 'Combo', tracking=True, copy=True)
    service_uom_ids = fields.Many2many(related='service_id.uom_ids', tracking=True, copy=True)
    uom_id = fields.Many2one('uom.uom', string='Unit', tracking=True, copy=True)
    version = fields.Integer('Version', default=1, tracking=True, copy=True)
    percent_based_on = fields.Selection([
        ('product_total_amount', 'Product Total Amount'),
        ('declaration_total_amount', 'Declaration Total Amount'),
        ('purchase_total_amount', 'Purchase Total Amount'),
        ('invoice_total_amount', 'Tổng giá trị xuất hoá đơn'),
    ], 'Based On', tracking=True, copy=True)
    min_amount = fields.Float(string="Min Amount", digits='Product Price', tracking=True, copy=True)
    # re define
    compute_price = fields.Selection(
        selection=[
            ('fixed', "Fixed Price"),
            ('percentage', "Percentage"),
            ('table', "Table"),
        ],
        index=True, default='fixed', required=True, tracking=True, copy=True)
    pricelist_table_detail_ids = fields.One2many('product.pricelist.item.detail', 'item_id', string='Pricelist Table',
                                                 tracking=True)
    is_price = fields.Boolean('Is Price', tracking=True, copy=True)
    is_accumulated = fields.Boolean('Is Accumulated', tracking=True, copy=True)

    # re-define for tracking
    date_start = fields.Datetime(tracking=True)
    date_end = fields.Datetime(tracking=True)
    currency_id = fields.Many2one(tracking=True)

    # Bỏ yêu cầu product_tmpl_id
    product_tmpl_id = fields.Many2one(required=False)

    @api.onchange('service_id')
    def onchange_service(self):
        return {
            'domain': {'uom_id': [('id', 'in', self.service_id.uom_ids.ids)]}
        }

    @api.model
    def create(self, vals):
        if not vals.get('pricelist_id', False):
            partner_id = vals.get('partner_id', False)
            currency_id = vals.get('currency_id', False)
            if partner_id:
                pricelist_id = self.env['product.pricelist'].search(
                    [('partner_id', '=', partner_id), ('currency_id', '=', currency_id),
                     ('company_id', '=', self.env.company.id)], limit=1)
                if not pricelist_id:
                    partner_obj_id = self.env['res.partner'].sudo().browse(partner_id)
                    pricelist_id = self.env['product.pricelist'].create({
                        'name': 'Bảng giá khách hàng %s' % partner_obj_id.name,
                        'partner_id': partner_id,
                        'currency_id': currency_id,
                        'company_id': self.env.company.id
                    })
                    vals['pricelist_id'] = pricelist_id.id
            else:
                pricelist_id = self.env['product.pricelist'].search(
                    [('partner_id', '=', False), ('currency_id', '=', currency_id),
                     ('company_id', '=', self.env.company.id)], limit=1)
                if not pricelist_id:
                    pricelist_id = self.env['product.pricelist'].create({
                        'name': 'Bảng giá chung',
                        'currency_id': currency_id,
                        'company_id': self.env.company.id
                    })
                vals['pricelist_id'] = pricelist_id.id
        return super().create(vals)

    def unlink(self):
        # log to front end of deleted bookings
        mapping_delete = {}
        for item in self:
            if mapping_delete.get(item.service_id):
                mapping_delete[item.service_id] = mapping_delete[f'{item.service_id.id}'] | item
            else:
                mapping_delete[item.service_id] = item
        for service_id, pricelist_item_ids in mapping_delete.items():
            service_id.message_post(
                body=_("Delete Pricelist: %s") % ','.join(pricelist_item_ids.mapped('uom_id').mapped('name')))
        return super(ProductPricelistItem, self).unlink()

    # Thêm phương thức để tính giá dựa trên điều kiện đơn vị
    # Cập nhật phương thức compute_price_with_conditions
    def compute_price_with_conditions(self, value, selected_uoms):
        """Tính toán giá dựa trên giá trị và các đơn vị được chọn

        Args:
            value (float): Giá trị để tính toán (ví dụ: tổng tiền, số lượng...)
            selected_uoms (recordset): Danh sách các đơn vị được chọn

        Returns:
            float: Giá tính toán được hoặc None nếu không áp dụng được
        """
        self.ensure_one()

        if self.compute_price == 'fixed':
            # Với giá cố định, chỉ cần kiểm tra điều kiện đơn vị
            if self.is_applicable_for_uoms(selected_uoms):
                return self.fixed_price

        elif self.compute_price == 'percentage':
            # Với giá phần trăm
            if self.is_applicable_for_uoms(selected_uoms):
                return value * (self.percent_price / 100.0)

        elif self.compute_price == 'table':
            # Sắp xếp chi tiết bảng giá theo sequence và min_value
            details = self.pricelist_table_detail_ids.sorted(lambda d: (d.sequence, d.min_value))

            # Với giá bảng, tính tổng giá từ tất cả các mức áp dụng
            total_price = 0.0
            applied_details = []

            # Trường hợp giá tích lũy: tính tổng các mức giá áp dụng
            if self.is_accumulated:
                for detail in details:
                    if detail.is_applicable(value, selected_uoms):
                        if detail.price_type == 'fixed_range':
                            # Khoảng giá: chỉ tính mức giá nào có value nằm trong khoảng
                            if detail.min_value <= value <= (detail.max_value or float('inf')):
                                total_price += detail.amount
                                applied_details.append(detail)
                        elif detail.price_type == 'unit_price':
                            # Đơn giá: tính cho phần giá trị vượt quá min_value
                            # nhưng không vượt quá max_value
                            excess_value = min(value, detail.max_value or float('inf')) - detail.min_value
                            if excess_value > 0:
                                total_price += excess_value * detail.amount
                                applied_details.append(detail)

                return total_price if applied_details else None

            # Trường hợp không tích lũy: tìm mức giá đầu tiên phù hợp
            else:
                # Nếu là giá theo khoảng, tìm khoảng chứa value
                for detail in details:
                    if detail.is_applicable(value, selected_uoms):
                        if detail.price_type == 'fixed_range':
                            # Với khoảng giá, trả về giá cố định
                            return detail.amount
                        elif detail.price_type == 'unit_price':
                            # Với đơn giá, tính theo công thức: (value - min_value) * amount
                            excess_value = value - detail.min_value
                            if excess_value > 0:
                                return excess_value * detail.amount

                # Không tìm thấy mức giá phù hợp
                return None

        return None

    # Thêm vào class ProductPricelistItem

    def is_applicable_for_uoms(self, selected_uoms, use_for_pricing=False):
        """Kiểm tra xem bảng giá có áp dụng được cho các đơn vị đã chọn không

        Args:
            selected_uoms: recordset các đơn vị đã chọn
            use_for_pricing: Nếu True, ưu tiên sử dụng pricing_uom_ids

        Returns:
            bool: True nếu áp dụng được, False nếu không
        """
        self.ensure_one()

        # Nếu sử dụng cho tính giá, kiểm tra pricing_uom_ids
        if use_for_pricing and self.service_id:
            applicable_uoms = []
            for field in self.service_id.required_fields_ids:
                if field.pricing_uom_ids:
                    applicable_uoms.extend(field.pricing_uom_ids.ids)
                # Tương thích ngược
                elif field.uom_ids and field.using_calculation_price:
                    applicable_uoms.extend(field.uom_ids.ids)
                elif field.uom_id and field.using_calculation_price:
                    applicable_uoms.append(field.uom_id.id)

            return bool(set(selected_uoms.ids).intersection(set(applicable_uoms)))

        # Logic hiện tại
        # ...
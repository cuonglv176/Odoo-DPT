
from odoo import fields, models, api, _

class ProductPricelistItemDetail(models.Model):
    _name = 'product.pricelist.item.detail'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _order = 'sequence, min_value'  # Sắp xếp theo sequence và min_value

    sequence = fields.Integer(string='Thứ tự', default=10,
                              help='Xác định thứ tự áp dụng của các điều kiện giá')
    item_id = fields.Many2one('product.pricelist.item', 'Pricelist Item', tracking=True)
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist', tracking=True)
    amount = fields.Monetary(currency_field='currency_id', string="Amount", digits='Product Price', tracking=True)
    uom_id = fields.Many2one('uom.uom', 'Product Units', tracking=True)
    description = fields.Char('Description', tracking=True)
    min_value = fields.Float('Min Value', tracking=True)
    max_value = fields.Float('Max Value', tracking=True)
    currency_id = fields.Many2one(related='item_id.currency_id')
    service_id = fields.Many2one(related='item_id.service_id')
    combo_id = fields.Many2one(related='item_id.combo_id')

    # Thêm các trường mới
    price_type = fields.Selection([
        ('fixed_range', 'Khoảng giá (cố định cho cả khoảng)'),
        ('unit_price', 'Đơn giá (giá nhân với số lượng)')
    ], string='Kiểu giá', default='fixed_range', required=True, tracking=True,
        help="Khoảng giá: áp dụng giá cố định cho toàn bộ khoảng\n"
             "Đơn giá: nhân giá với số lượng vượt quá mức Min Value")

    compute_uom_id = fields.Many2one('uom.uom', string='Đơn vị tính',
                                     help="Đơn vị tính dùng để tính giá (km, kg, m3...)", tracking=True)

    # Thêm các trường mới để xử lý điều kiện đơn vị
    condition_type = fields.Selection([
        ('simple', 'Đơn vị đơn'),
        ('or', 'Thỏa mãn bất kỳ đơn vị nào (OR)'),
        ('and', 'Thỏa mãn tất cả đơn vị (AND)')
    ], string='Loại điều kiện', default='simple', tracking=True)

    uom_condition_ids = fields.Many2many('uom.uom', 'pricelist_item_detail_uom_rel',
                                         'detail_id', 'uom_id', string='Điều kiện đơn vị', tracking=True)

    @api.onchange('condition_type')
    def _onchange_condition_type(self):
        if self.condition_type == 'simple' and self.uom_id:
            self.uom_condition_ids = [(6, 0, [self.uom_id.id])]
        elif self.condition_type != 'simple' and self.uom_id and not self.uom_condition_ids:
            self.uom_condition_ids = [(6, 0, [self.uom_id.id])]

    @api.onchange('uom_id')
    def _onchange_uom_id(self):
        if self.condition_type == 'simple' and self.uom_id:
            self.uom_condition_ids = [(6, 0, [self.uom_id.id])]

    def is_applicable(self, value, selected_uoms):
        """Kiểm tra xem mục bảng giá này có được áp dụng không

        Args:
            value (float): Giá trị để kiểm tra trong khoảng min_value-max_value
            selected_uoms (recordset): Danh sách các đơn vị được chọn

        Returns:
            bool: True nếu thỏa mãn điều kiện, False nếu không
        """
        self.ensure_one()

        # Kiểm tra điều kiện khoảng giá trị
        if self.min_value and value < self.min_value:
            return False
        if self.max_value and value > self.max_value:
            return False

        # Kiểm tra điều kiện đơn vị
        if not self.uom_condition_ids:
            return False

        selected_uom_ids = selected_uoms.ids

        if self.condition_type == 'simple':
            # Với kiểu đơn, phải khớp chính xác 1 đơn vị
            condition_uom_id = self.uom_id.id
            return condition_uom_id in selected_uom_ids

        elif self.condition_type == 'or':
            # Với kiểu OR, chỉ cần 1 đơn vị khớp
            condition_uom_ids = self.uom_condition_ids.ids
            return any(uom_id in selected_uom_ids for uom_id in condition_uom_ids)

        elif self.condition_type == 'and':
            # Với kiểu AND, tất cả đơn vị trong điều kiện phải được chọn
            condition_uom_ids = self.uom_condition_ids.ids
            return all(uom_id in selected_uom_ids for uom_id in condition_uom_ids)

        return False

    def compute_price(self, value):
        """Tính giá dựa trên giá trị và kiểu giá (khoảng giá hoặc đơn giá)

        Args:
            value (float): Giá trị để tính toán (ví dụ: số km, số kg...)

        Returns:
            float: Giá tính được dựa trên kiểu giá
        """
        self.ensure_one()

        if self.price_type == 'fixed_range':
            # Khoảng giá: trả về giá cố định cho cả khoảng
            return self.amount
        elif self.price_type == 'unit_price':
            # Đơn giá: nhân với số lượng vượt quá min_value
            excess_value = value - self.min_value
            if excess_value <= 0:
                return 0
            return excess_value * self.amount

        return self.amount

    def unlink(self):
        # log to front end of deleted bookings
        mapping_delete = {}
        for item in self:
            if mapping_delete.get(item.item_id.service_id):
                mapping_delete[item.item_id.service_id] = mapping_delete.get(item.item_id.service_id) | item
            else:
                mapping_delete[item.item_id.service_id] = item
        for service_id, pricelist_item_detail_ids in mapping_delete.items():
            service_id.message_post(
                body=_("Delete Pricelist Table: %s") % ','.join(
                    pricelist_item_detail_ids.mapped('uom_id').mapped('name')))
        return super(ProductPricelistItemDetail, self).unlink()
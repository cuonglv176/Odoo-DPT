from odoo import fields, models, api


class DPTServiceManagement(models.Model):
    _inherit = 'dpt.service.management'

    pricelist_item_ids = fields.One2many('product.pricelist.item', 'service_id', string='Pricelist')

    def get_active_pricelist(self, partner_id):
        self = self.sudo()
        valid_pricelist_ids = self.pricelist_item_ids.filtered(lambda p: not p.date_end or (
                p.date_start and p.date_end and p.date_start <= fields.Datetime.now() and p.date_end >= fields.Datetime.now()))
        valid_partner_pricelist_ids = valid_pricelist_ids.filtered(lambda p: p.partner_id == partner_id)
        valid_pricelist_ids -= valid_pricelist_ids.filtered(
            lambda p: not p.partner_id and p.uom_id.id in valid_partner_pricelist_ids.mapped('uom_id').ids)
        return valid_pricelist_ids

    def get_active_pricelist(self, partner_id, selected_uoms=None):
        """Lấy bảng giá đang hoạt động phù hợp với khách hàng và đơn vị đã chọn

        Args:
            partner_id (res.partner): Khách hàng
            selected_uoms (recordset): Danh sách các đơn vị đã chọn (tuỳ chọn)

        Returns:
            recordset: Các bảng giá phù hợp
        """
        self = self.sudo()
        # Lọc các bảng giá còn hiệu lực
        valid_pricelist_ids = self.pricelist_item_ids.filtered(lambda p: not p.date_end or (
                p.date_start and p.date_end and p.date_start <= fields.Datetime.now() and p.date_end >= fields.Datetime.now()))
        # Lọc theo khách hàng
        valid_partner_pricelist_ids = valid_pricelist_ids.filtered(lambda p: p.partner_id == partner_id)

        # Loại bỏ bảng giá chung nếu đã có bảng giá riêng cho khách hàng cùng đơn vị
        valid_pricelist_ids -= valid_pricelist_ids.filtered(
            lambda p: not p.partner_id and p.uom_id.id in valid_partner_pricelist_ids.mapped('uom_id').ids)

        # Nếu có đơn vị được chọn, lọc thêm theo điều kiện đơn vị
        if selected_uoms:
            # Với bảng giá cố định hoặc phần trăm, kiểm tra điều kiện đơn vị
            non_table_pricelists = valid_pricelist_ids.filtered(lambda p: p.compute_price != 'table')
            applicable_non_table = non_table_pricelists.filtered(lambda p: p.is_applicable_for_uoms(selected_uoms))

            # Giữ lại tất cả bảng giá theo bảng (sẽ kiểm tra chi tiết khi tính giá)
            table_pricelists = valid_pricelist_ids.filtered(lambda p: p.compute_price == 'table')

            return applicable_non_table + table_pricelists

        return valid_pricelist_ids


class DPTServiceCombo(models.Model):
    _inherit = 'dpt.service.combo'

    pricelist_item_ids = fields.One2many('product.pricelist.item', 'combo_id', string='Pricelist')

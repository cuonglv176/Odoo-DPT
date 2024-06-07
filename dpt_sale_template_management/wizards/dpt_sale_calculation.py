from odoo import models, fields, api, _


class DPTSaleCalculation(models.Model):
    _name = 'dpt.sale.calculation'

    def _default_service_id(self):
        return self.env.context.get('active_id') or self.env.context.get('default_service_id')

    service_id = fields.Many2one('dpt.service.management', default=_default_service_id)
    sale_service_id = fields.Many2one('dpt.sale.service.management')
    calculation_line_ids = fields.One2many('dpt.sale.calculation.line', 'parent_id')
    min_amount_total = fields.Monetary(string="Min Amount", currency_field="currency_id",
                                       compute="_compute_min_amount_total")
    currency_id = fields.Many2one(related="service_id.currency_id")

    address = fields.Char('Address')
    weight = fields.Char('Weight')
    volume = fields.Char('Volume')
    distance = fields.Char('Distance')

    # compute show input field
    is_show_address = fields.Boolean('Is show address', compute="compute_show_field")
    is_show_weight = fields.Boolean('Is show weight', compute="compute_show_field")
    is_show_volume = fields.Boolean('Is show volume', compute="compute_show_field")
    is_show_distance = fields.Boolean('Is show distance', compute="compute_show_field")

    is_required_address = fields.Boolean('Is required address', compute="compute_show_field")
    is_required_weight = fields.Boolean('Is required weight', compute="compute_show_field")
    is_required_volume = fields.Boolean('Is required volume', compute="compute_show_field")
    is_required_distance = fields.Boolean('Is required distance', compute="compute_show_field")

    weight_uom_id = fields.Many2one('uom.uom', 'Weight Unit')
    volume_uom_id = fields.Many2one('uom.uom', 'Volume Unit')
    distance_uom_id = fields.Many2one('uom.uom', 'Distance Unit')

    @api.depends('service_id')
    def compute_show_field(self):
        for item in self:
            item.is_show_address = False
            item.is_show_weight = False
            item.is_show_volume = False
            item.is_show_distance = False
            item.is_required_address = False
            item.is_required_weight = False
            item.is_required_volume = False
            item.is_required_distance = False
            for field in item.service_id.required_fields_ids:
                if field.field == 'address':
                    item.is_show_address = True
                    item.is_required_address = field.type == 'required'
                if field.field == 'weight':
                    item.is_show_weight = True
                    item.is_required_weight = field.type == 'required'
                if field.field == 'volume':
                    item.is_show_volume = True
                    item.is_required_volume = field.type == 'required'
                if field.field == 'distance':
                    item.is_show_distance = True
                    item.is_required_distance = field.type == 'required'

    @api.onchange('weight', 'volume', 'distance', 'weight_uom_id', 'volume_uom_id', 'distance_uom_id')
    def onchange_compute_price(self):
        return

    def _compute_min_amount_total(self):
        for item in self:
            item.min_amount_total = max(item.calculation_line_ids.mapped('min_amount_total'))

    def action_save(self):
        max_amount = self.calculation_line_ids.sorted(key=lambda t: t.amount_total, reverse=True)[:1]
        self.sale_service_id.write({
            'uom_id': max_amount.uom_id.id,
            'qty': max_amount.qty,
            'price': max_amount.price,
            'price_status': 'approved',
            'pricelist_item_id': max_amount.pricelist_item_id.id if max_amount.pricelist_item_id else None,
        })

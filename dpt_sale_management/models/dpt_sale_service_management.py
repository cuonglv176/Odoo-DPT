from odoo import models, fields, api, _


class DPTSaleServiceManagement(models.Model):
    _name = 'dpt.sale.service.management'
    _description = 'DPT Sale Service Management'

    sale_id = fields.Many2one('sale.order', ondelete='cascade')
    service_id = fields.Many2one('dpt.service.management', string='Service')
    description = fields.Html(string='Description')
    qty = fields.Float(string='QTY')
    uom_ids = fields.Many2many(related='service_id.uom_ids')
    uom_id = fields.Many2one('uom.uom', string='Unit', domain="[('id', 'in', uom_ids)]")
    price = fields.Monetary(currency_field='currency_id', string='Price')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    department_id = fields.Many2one(related='service_id.department_id')
    amount_total = fields.Monetary(currency_field='currency_id', string="Amount Total", compute="_compute_amount_total")
    price_status = fields.Selection([
        ('no_price', 'No Price'),
        ('wait_approve', 'Wait Approve'),
        ('approved', 'Approved'),
    ], string='Status', default='no_price')
    sequence = fields.Integer()
    show_action_calculation = fields.Boolean('Show Action Calculation', compute='compute_show_action_calculation')
    pricelist_item_id = fields.Many2one('product.pricelist.item', 'Pricelist Item')

    # compute show input field
    is_show_address = fields.Boolean('Is show address', compute="compute_show_field")
    is_show_weight = fields.Boolean('Is show weight', compute="compute_show_field")
    is_show_volume = fields.Boolean('Is show volume', compute="compute_show_field")
    is_show_distance = fields.Boolean('Is show distance', compute="compute_show_field")

    is_required_address = fields.Boolean('Is required address', compute="compute_show_field")
    is_required_weight = fields.Boolean('Is required weight', compute="compute_show_field")
    is_required_volume = fields.Boolean('Is required volume', compute="compute_show_field")
    is_required_distance = fields.Boolean('Is required distance', compute="compute_show_field")

    @api.depends('service_id')
    def compute_show_field(self):
        for item in self:
            for field in item.service_id.required_fields_ids:
                item.is_show_address = field.field == 'address'
                item.is_required_address = field.field == 'address' and field.type == 'required'

                item.is_show_weight = field.field == 'weight'
                item.is_required_weight = field.field == 'weight' and field.type == 'required'

                item.is_show_volume = field.field == 'volume'
                item.is_required_volume = field.field == 'volume' and field.type == 'required'

                item.is_show_distance = field.field == 'distance'
                item.is_required_distance = field.field == 'distance' and field.type == 'required'

    def _compute_amount_total(self):
        for item in self:
            item.amount_total = item.qty * item.price

    def compute_show_action_calculation(self):
        # only show action calculation when current user is in the same department
        for item in self:
            item.show_action_calculation = (self.env.user.employee_ids and item.department_id and
                                            self.env.user.employee_ids[:1].department_id.id == item.department_id.id)

    def action_calculation(self):
        # get default based on pricelist
        calculation_line = []
        for pricelist_item_id in self.service_id.get_active_pricelist().filtered(
                lambda p: not p.partner_id or (p.partner_id and p.partner_id.id == self.sale_id.partner_id.id)):
            if pricelist_item_id.compute_price == 'fixed':
                calculation_line.append((0, 0, {
                    'uom_id': pricelist_item_id.uom_id.id,
                    'price': pricelist_item_id.currency_id._convert(
                        from_amount=pricelist_item_id.fixed_price,
                        to_currency=self.env.company.currency_id,
                        company=self.env.company,
                        date=fields.Date.today(),
                    ),
                    'min_price': pricelist_item_id.min_amount,
                    'pricelist_item_id': pricelist_item_id.id,
                }))
            elif pricelist_item_id.compute_price == 'percentage':
                price_base = 0
                if pricelist_item_id.percent_based_on == 'product_total_amount':
                    price_base = sum(self.sale_id.order_line.mapped('price_total'))
                elif pricelist_item_id.percent_based_on == 'declaration_total_amount':
                    price_base = sum(self.sale_id.order_line.mapped('price_declaration'))
                if price_base:
                    calculation_line.append((0, 0, {
                        'uom_id': pricelist_item_id.uom_id.id,
                        'price': pricelist_item_id.currency_id._convert(
                            from_amount=price_base * pricelist_item_id.percent_price / 100,
                            to_currency=self.env.company.currency_id,
                            company=self.env.company,
                            date=fields.Date.today(),
                        ),
                        'min_price': pricelist_item_id.min_amount,
                        'pricelist_item_id': pricelist_item_id.id,
                    }))
            elif pricelist_item_id.compute_price == 'table':
                for detail_id in pricelist_item_id.pricelist_table_detail_ids:
                    if detail_id.compute_price == 'fixed':
                        calculation_line.append((0, 0, {
                            'uom_id': pricelist_item_id.uom_id.id,
                            'price': pricelist_item_id.currency_id._convert(
                                from_amount=detail_id.amount,
                                to_currency=self.env.company.currency_id,
                                company=self.env.company,
                                date=fields.Date.today(),
                            ),
                            'min_price': pricelist_item_id.min_amount,
                            'pricelist_item_id': pricelist_item_id.id,
                        }))
        return {
            'name': "Calculation Service",
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.sale.calculation',
            'target': 'new',
            'views': [[False, 'form']],
            'context': {
                'default_service_id': self.service_id.id,
                'default_sale_service_id': self.id,
                'default_calculation_line_ids': calculation_line,
            },
        }

    @api.onchange('price', 'qty')
    def onchange_amount_total(self):
        if self.price and self.qty:
            self.amount_total = self.price * self.qty

    @api.onchange('service_id')
    def onchange_service(self):
        if self.service_id:
            self.uom_id = self.service_id.uom_id

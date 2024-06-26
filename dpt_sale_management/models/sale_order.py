from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError

SALE_ORDER_STATE = [
    ('draft', "Quotation"),
    ('wait_price', "Wait Price"),
    ('sent', "Quotation Sent"),
    ('sale', "Sales Order"),
    ('cancel', "Cancelled"),
]


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # re-define
    state = fields.Selection(
        selection=SALE_ORDER_STATE,
        string="Status",
        readonly=True, copy=False, index=True,
        tracking=3,
        default='draft')
    sale_service_ids = fields.One2many('dpt.sale.service.management', 'sale_id', string='Service')
    fields_ids = fields.One2many('dpt.sale.order.fields', 'sale_id', string='Fields')
    service_total_untax_amount = fields.Float(compute='_compute_service_amount')
    service_tax_amount = fields.Float(compute='_compute_service_amount')
    service_total_amount = fields.Float(compute='_compute_service_amount')
    update_pricelist = fields.Boolean('Update Pricelist')
    show_action_calculation = fields.Boolean('Show Action Calculation', compute='compute_show_action_calculation')
    weight = fields.Float('Weight')
    volume = fields.Float('Volume')

    @api.onchange('weight', 'volume', 'order_line')
    def onchange_weight_volume(self):
        for fields_id in self.fields_ids:
            if fields_id.fields_id.default_compute_from == 'weight_in_so' and fields_id.fields_id.fields_type == 'integer':
                fields_id.value_integer = self.weight
            if fields_id.fields_id.default_compute_from == 'volume_in_so' and fields_id.fields_id.fields_type == 'integer':
                fields_id.value_integer = self.volume
            if fields_id.fields_id.default_compute_from == 'declared_price_in_so' and fields_id.fields_id.fields_type == 'integer':
                fields_id.value_integer = sum(self.order_line.mapped('price_declaration'))

    @api.model
    def create(self, vals_list):
        res = super(SaleOrder, self).create(vals_list)
        self.check_required_fields()
        return res

    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
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
        sequence = 0
        list_exist = self.env['sale.order'].browse(self.id.origin).fields_ids.fields_id.ids
        list_onchange = [item.fields_id.id for item in self.fields_ids]
        list_sale_service_id = []
        for sale_service_id in self.sale_service_ids:
            if sale_service_id.service_id.id in list_sale_service_id:
                continue
            for required_fields_id in sale_service_id.service_id.required_fields_ids:
                if required_fields_id.id in list_exist:
                    for field_data in self.env['sale.order'].browse(self.id.origin).fields_ids:
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
                        default_value = required_fields_id.get_default_value(self)
                        if default_value:
                            x.update(default_value)
                        val.append(x)
                else:
                    x = {
                        'sequence': 1 if required_fields_id.type == 'required' else 0,
                        'fields_id': required_fields_id.id,
                    }
                    default_value = required_fields_id.get_default_value(self)
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

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order_id in self:
            if order_id.sale_service_ids.filtered(lambda ss: ss.price_in_pricelist != ss.price):
                raise ValidationError(_('Please approve new price!'))
            if not order_id.update_pricelist:
                continue
            for sale_service_id in order_id.sale_service_ids.filtered(lambda ss: ss.price_in_pricelist != ss.price):
                if not sale_service_id.uom_id:
                    raise ValidationError(_("Please insert Units"))
                pricelist_id = self.env['product.pricelist'].sudo().search([('partner_id', '=', self.partner_id.id)])
                if not pricelist_id:
                    pricelist_id = self.env['product.pricelist'].sudo().create({
                        'name': 'Bảng giá của khách hàng %s' % self.partner_id.name,
                        'partner_id': self.partner_id.id,
                        'currency_id': sale_service_id.currency_id.id,
                    })
                price_list_item_id = self.env['product.pricelist.item'].sudo().search(
                    [('pricelist_id', '=', pricelist_id.id), ('service_id', '=', sale_service_id.service_id.id),
                     ('uom_id', '=', sale_service_id.uom_id.id), ('partner_id', '=', self.partner_id.id)])
                if not price_list_item_id:
                    self.env['product.pricelist.item'].sudo().create({
                        'partner_id': self.partner_id.id,
                        'pricelist_id': pricelist_id.id,
                        'service_id': sale_service_id.service_id.id,
                        'uom_id': sale_service_id.uom_id.id,
                        'compute_price': 'fixed',
                        'fixed_price': sale_service_id.price,
                        'is_price': False,
                    })
                else:
                    price_list_item_id.write({
                        'compute_price': 'fixed',
                        'fixed_price': sale_service_id.price,
                        'is_price': False,
                    })
        return res

    def send_quotation_department(self):
        self.state = 'wait_price'

    @api.depends('sale_service_ids.amount_total')
    def _compute_service_amount(self):
        untax_amount = 0
        tax_amount = 0
        for r in self.sale_service_ids:
            untax_amount += r.amount_total
            tax_amount += r.amount_total * 8 / 100
        self.service_total_untax_amount = untax_amount
        self.service_tax_amount = tax_amount
        self.service_total_amount = untax_amount

    def compute_show_action_calculation(self):
        # only show action calculation when current user is in the same department
        for item in self:
            not_compute_price_service_ids = True or item.sale_service_ids.filtered(
                lambda ss: ss.department_id.id in self.env.user.employee_ids.mapped('department_id').ids)
            item.show_action_calculation = True if not_compute_price_service_ids else False

    def action_calculation(self):
        # get default based on pricelist
        # for sale_service_id in self.sale_service_ids.filtered(
        #         lambda ss: ss.department_id.id == self.env.user.employee_ids[:1].department_id.id):

        for sale_service_id in self.sale_service_ids:
            if not sale_service_id.uom_id:
                continue
            current_uom_id = sale_service_id.uom_id
            service_price_ids = sale_service_id.service_id.get_active_pricelist(partner_id=self.partner_id)
            if current_uom_id:
                service_price_ids = service_price_ids.filtered(lambda sp: sp.uom_id.id == current_uom_id.id)
            if not service_price_ids:
                continue
            max_price = 0
            price_list_item_id = None
            compute_value = 0
            compute_uom_id = None
            for service_price_id in service_price_ids:
                if service_price_id.compute_price == 'fixed_price':
                    price = max(service_price_id.currency_id._convert(service_price_id.fixed_price,
                                                                      to_currency=self.env.company.currency_id,
                                                                      company=self.env.company,
                                                                      date=fields.Date.today()),
                                service_price_id.min_amount)
                    if price > max_price:
                        max_price = price
                        price_list_item_id = service_price_id
                elif service_price_id.compute_price == 'percentage':
                    price_base = 0
                    price = 0
                    if service_price_id.percent_based_on == 'product_total_amount':
                        price_base = sum(self.order_line.mapped('price_total'))
                    elif service_price_id.percent_based_on == 'declaration_total_amount':
                        price_base = sum(self.order_line.mapped('price_declaration'))
                    if price_base:
                        price = max(service_price_id.currency_id._convert(
                            from_amount=price_base * service_price_id.percent_price / 100,
                            to_currency=self.env.company.currency_id,
                            company=self.env.company,
                            date=fields.Date.today(),
                        ), service_price_id.min_amount)
                    if price and price > max_price:
                        max_price = price
                        price_list_item_id = service_price_id
                elif service_price_id.compute_price == 'table':
                    compute_field_ids = self.fields_ids.filtered(lambda f: f.using_calculation_price)
                    for compute_field_id in compute_field_ids:
                        if not service_price_id.is_accumulated:
                            detail_price_ids = service_price_id.pricelist_table_detail_ids.filtered(lambda
                                                                                                        ptd: ptd.uom_id.id == compute_field_id.uom_id.id and compute_field_id.value_integer >= ptd.min_value and compute_field_id.value_integer <= ptd.max_value)
                            for detail_price_id in detail_price_ids:
                                price = compute_field_id.value_integer * detail_price_id.amount if service_price_id.is_price else detail_price_id.amount
                                price = max(service_price_id.currency_id._convert(
                                    from_amount=price,
                                    to_currency=self.env.company.currency_id,
                                    company=self.env.company,
                                    date=fields.Date.today(),
                                ), service_price_id.min_amount)
                                if (not service_price_id.is_price and price > max_price) or (
                                        service_price_id.is_price and (price / compute_field_id.value_integer if compute_field_id.value_integer != 0 else price) > max_price):
                                    max_price = service_price_id.currency_id._convert(
                                        from_amount=detail_price_id.amount,
                                        to_currency=self.env.company.currency_id,
                                        company=self.env.company,
                                        date=fields.Date.today(),
                                    )
                                    price_list_item_id = service_price_id
                                    compute_value = compute_field_id.value_integer
                                    compute_uom_id = compute_field_id.uom_id.id
                        else:
                            detail_price_ids = service_price_id.pricelist_table_detail_ids.filtered(
                                lambda ptd: ptd.uom_id.id == compute_field_id.uom_id.id)
                            total_price = 0
                            for detail_price_id in detail_price_ids.sorted(key=lambda r: r.min_value):
                                if detail_price_id.min_value > compute_field_id.value_integer:
                                    continue
                                if detail_price_id.max_value:
                                    price = (min(compute_field_id.value_integer,
                                                 detail_price_id.max_value) - detail_price_id.min_value + 1) * detail_price_id.amount if service_price_id.is_price else detail_price_id.amount
                                else:
                                    price = (
                                                    compute_field_id.value_integer - detail_price_id.min_value + 1) * detail_price_id.amount if service_price_id.is_price else detail_price_id.amount
                                total_price += service_price_id.currency_id._convert(
                                    from_amount=price,
                                    to_currency=self.env.company.currency_id,
                                    company=self.env.company,
                                    date=fields.Date.today(),
                                )
                            if max(total_price, service_price_id.min_amount) > max_price:
                                max_price = max(total_price, service_price_id.min_amount)
                                price_list_item_id = service_price_id
                                compute_value = compute_field_id.value_integer
                                compute_uom_id = compute_field_id.uom_id.id

            sale_service_id.with_context(from_pricelist=True).write({
                'uom_id': price_list_item_id.uom_id.id if price_list_item_id else (
                    service_price_ids[:1].uom_id.id if service_price_ids and service_price_ids[:1].uom_id else None),
                'price': max_price,
                'qty': 1,
                'pricelist_item_id': price_list_item_id.id if price_list_item_id else (
                    service_price_ids[:1].id if service_price_ids else None),
                'price_in_pricelist': max_price,
                'compute_value': compute_value,
                'compute_uom_id': compute_uom_id,
            })

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        sale = super(SaleOrder, self).copy(default)
        sale.sale_service_ids = self.sale_service_ids
        sale.fields_ids = self.fields_ids
        return sale


class SaleOrderField(models.Model):
    _name = 'dpt.sale.order.fields'

    def _default_sequence(self):
        if self.type == 'required':
            return 1
        return 0

    sequence = fields.Integer(default=_default_sequence, compute='_compute_sequence', store=True)
    sale_id = fields.Many2one('sale.order', string='Sale Order')
    service_id = fields.Many2one(related='fields_id.service_id')
    fields_id = fields.Many2one('dpt.service.management.required.fields', string='Fields')
    value_char = fields.Char(string='Value Char')
    value_integer = fields.Float(string='Value Integer')
    value_date = fields.Date(string='Value Date')
    selection_value_id = fields.Many2one('dpt.sale.order.fields.selection', string='Selection Value')
    type = fields.Selection(selection=[
        ("required", "Required"),
        ("options", "Options")
    ], string='Type Fields', default='options', related='fields_id.type')
    fields_type = fields.Selection([
        ('char', 'Char'),
        ('integer', 'Integer'),
        ('date', 'Date'),
        ('selection', 'Selection'),
    ], string='Fields type', default='char', related='fields_id.fields_type')
    using_calculation_price = fields.Boolean(related='fields_id.using_calculation_price')
    uom_id = fields.Many2one(related="fields_id.uom_id")

    @api.depends('fields_id', 'fields_id.type')
    def _compute_sequence(self):
        for r in self:
            if r.type == 'required':
                r.sequence = 1
            else:
                r.sequence = 0

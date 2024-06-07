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
            if r.fields_id.type == 'options' or (r.fields_id.type == 'required' and (r.value_char or r.value_integer or r.value_date)):
                continue
            else:
                raise ValidationError(_("Please fill required fields!!!"))


    @api.onchange('sale_service_ids')
    def onchange_sale_service_ids(self):
        val = []
        sequence = 0
        for sale_service_id in self.sale_service_ids:
            for required_fields_id in sale_service_id.service_id.required_fields_ids:
                if val:
                    result = [item for item in val if item['fields_id'] == required_fields_id.id]
                    if not result:
                        val.append({
                            'sequence': sequence,
                            'fields_id': required_fields_id.id,
                        })
                else:
                    val.append({
                        'sequence': sequence,
                        'fields_id': required_fields_id.id,
                    })
        if val:
            self.fields_ids = None
            self.fields_ids = [(0, 0, item) for item in val]

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        # for order_id in self:
        #     if not order_id.update_pricelist:
        #         continue

        return res

    def send_quotation_department(self):
        self.state = 'wait_price'

    def action_change_price(self):
        return {
            'name': "Change Price",
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.sale.change.price',
            'target': 'new',
            'views': [[False, 'form']],
            'context': {
                'default_order_id': self.id,
            },
        }

    @api.depends('sale_service_ids.amount_total')
    def _compute_service_amount(self):
        untax_amount = 0
        tax_amount = 0
        for r in self.sale_service_ids:
            untax_amount += r.amount_total
            tax_amount += r.amount_total * 8 / 100
        self.service_total_untax_amount = untax_amount
        self.service_tax_amount = tax_amount
        self.service_total_amount = untax_amount + tax_amount

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
            # compute_price_field_ids = self.fields_ids.filtered(lambda f: f.fields_id.using_calculation_price and f.fields_id.service_id.id == service_id.id)
            # for compute_price_field_id in compute_price_field_ids:
            #     if not compute_price_field_id.uom_id:
            #         raise ValidationError(_('Please adding Units for field: %s') % compute_price_field_id.field_id.name)
            service_price_ids = sale_service_id.service_id.get_active_pricelist()
            max_price = 0
            price_list_item_id = None
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
                        price_base = sum(self.sale_id.order_line.mapped('price_total'))
                    elif service_price_id.percent_based_on == 'declaration_total_amount':
                        price_base = sum(self.sale_id.order_line.mapped('price_declaration'))
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
                            if price > max_price:
                                max_price = price
                                price_list_item_id = service_price_id
                sale_service_id.write({
                    'uom_id': price_list_item_id.uom_id.id if price_list_item_id else None,
                    'price': max_price,
                    'qty': 1,
                    'price_status': 'approved',
                })


class SaleOrderField(models.Model):
    _name = 'dpt.sale.order.fields'

    sequence = fields.Integer()
    sale_id = fields.Many2one('sale.order', string='Sale Order')
    fields_id = fields.Many2one('dpt.service.management.required.fields', string='Fields')
    value_char = fields.Char(string='Value Char')
    value_integer = fields.Integer(string='Value Integer')
    value_date = fields.Integer(string='Value Date')
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


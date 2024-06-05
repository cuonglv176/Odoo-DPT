from odoo import models, fields, api, _
from datetime import datetime

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

    @api.onchange('sale_service_ids')
    def onchange_sale_service_ids(self):
        val = []
        sequence = 0
        for sale_service_id in self.sale_service_ids:
            for required_fields_id in sale_service_id.service_id.required_fields_ids:
                if val:
                    result = [item for item in val if item['fields_id'] == required_fields_id.fields_id.id]
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


class SaleOrderField(models.Model):
    _name = 'dpt.sale.order.fields'

    sequence = fields.Integer()
    sale_id = fields.Many2one('sale.order', string='Sale Order')
    fields_id = fields.Many2one('dpt.service.management.required.fields', string='Fields')
    value_char = fields.Char(string='Value Char')
    value_integer = fields.Integer(string='Value Integer')
    value_date = fields.Integer(string='Value Date')
    type = fields.Selection(selection=[
        ("required", "Required"),
        ("options", "Options")
    ], string='Type Fields', default='options', related='fields_id.type')
    fields_type = fields.Selection([
        ('char', 'Char'),
        ('integer', 'Integer'),
        ('date', 'Date'),
    ], string='Fields type', default='char', related='fields_id.fields_type')

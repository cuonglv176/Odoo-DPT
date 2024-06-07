from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


class DPTSaleTemplateService(models.Model):
    _name = 'dpt.sale.template.service'
    _description = 'DPT Sale Template Service'

    sale_id = fields.Many2one('sale.order.template', ondelete='cascade')
    service_id = fields.Many2one('dpt.service.management', string='Service')
    description = fields.Html(string='Description')
    qty = fields.Float(string='QTY')
    uom_ids = fields.Many2many(related='service_id.uom_ids')
    uom_id = fields.Many2one('uom.uom', string='Unit', domain="[('id', 'in', uom_ids)]")
    price = fields.Monetary(currency_field='currency_id', string='Price')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    department_id = fields.Many2one(related='service_id.department_id')
    amount_total = fields.Monetary(currency_field='currency_id', string="Amount Total", compute="_compute_amount_total")
    sequence = fields.Integer()
    pricelist_item_id = fields.Many2one('product.pricelist.item', 'Pricelist Item')


    def _prepare_order_service_values(self):
        """ Give the values to create the corresponding order line.

        :return: `sale.order.line` create values
        :rtype: dict
        """
        self.ensure_one()
        return {
            'service_id': self.service_id.id,
            'description': self.description,
            'qty': self.qty,
            'uom_id': self.uom_id.id,
            'sequence': self.sequence,
            'price': self.price,
            'currency_id': self.currency_id.id,
        }

    def _compute_amount_total(self):
        for item in self:
            item.amount_total = item.qty * item.price

    @api.onchange('price', 'qty')
    def onchange_amount_total(self):
        if self.price and self.qty:
            self.amount_total = self.price * self.qty

    @api.onchange('service_id')
    def onchange_service(self):
        if self.service_id:
            self.uom_id = self.service_id.uom_id




class SaleOrderTemplate(models.Model):
    _inherit = 'sale.order.template'

    sale_service_ids = fields.One2many('dpt.sale.template.service', 'sale_id', string='Service')


class SaleOrder(models.Model):
    _inherit = 'sale.order'


    @api.onchange('sale_order_template_id')
    def _onchange_sale_order_service_template_id(self):
        if not self.sale_order_template_id:
            return

        sale_order_template = self.sale_order_template_id.with_context(lang=self.partner_id.lang)

        sale_service_ids_data = [fields.Command.clear()]
        sale_service_ids_data += [
            fields.Command.create(line._prepare_order_service_values())
            for line in sale_order_template.sale_service_ids
        ]

        # set first line to sequence -99, so a resequence on first page doesn't cause following page
        # lines (that all have sequence 10 by default) to get mixed in the first page
        if len(sale_service_ids_data) >= 2:
            sale_service_ids_data[1][2]['sequence'] = -99

        self.sale_service_ids = sale_service_ids_data

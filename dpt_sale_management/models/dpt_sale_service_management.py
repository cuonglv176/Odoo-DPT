from odoo import models, fields, api, _


class DPTSaleServiceManagement(models.Model):
    _name = 'dpt.sale.service.management'
    _description = 'DPT Sale Service Management'

    sale_id = fields.Many2one('sale.order', ondelete='cascade')
    service_id = fields.Many2one('dpt.service.management', string='Service')
    description = fields.Html(string='Description')
    qty = fields.Float(string='QTY')
    uom_id = fields.Many2one(related='service_id.uom_id')
    price = fields.Monetary(currency_field='currency_id', string='Price')
    currency_id = fields.Many2one('res.currency', string='Currency')
    department_id = fields.Many2one(related='service_id.department_id')
    amount_total = fields.Float(string="Amount Total")
    price_status = fields.Selection([
        ('wait_approve', 'Wait Approve'),
        ('approved', 'Approved'),
    ], string='Status', default='wait_approve')
    sequence = fields.Integer()

    def action_calculation(self):
        return {
            'name': "Calculation Service",
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.sale.calculation',
            'target': 'new',
            'views': [[False, 'form']],
            'context': {
                'default_service_id': self.service_id.id,
            },
        }

    @api.onchange('price', 'qty')
    def onchange_amount_total(self):
        if self.price and self.qty:
            self.amount_total = self.price * self.qty
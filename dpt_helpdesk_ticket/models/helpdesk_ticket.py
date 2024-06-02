from odoo import models, fields, api, _


class HelpdeskTicket(models.Model):

    _inherit = 'helpdesk.ticket'

    name = fields.Char(default='PDV')
    sale_id = fields.Many2one('sale.order')
    type_service = fields.Selection([('sale_order', 'Sale Order'),
                                     ('stock', 'Stock'),
                                     ('import_export', 'Import Export')])
    service_lines_ids = fields.One2many('dpt.helpdesk.servie.line', 'parent_id', string='Service')
    purchase_id = fields.Many2one('purchase.order', string='Purchase Order')
    purchase_status = fields.Selection(related='purchase_id.state', string='Purchase Status')
    department_id = fields.Many2one('hr.department', string='Department')

    @api.model
    def create(self, vals):
        res = super(HelpdeskTicket, self).create(vals)
        res.name = self._generate_service_code()
        return res

    def _generate_service_code(self):
        sequence = self.env['ir.sequence'].next_by_code('helpdesk.ticket') or '00'
        return f'{sequence}'

    def action_create_po(self):
        pass


class DPTSaleChangePriceServiceLine(models.Model):
    _name = 'dpt.helpdesk.servie.line'

    sequence = fields.Integer()
    parent_id = fields.Many2one('helpdesk.ticket')
    service_id = fields.Many2one('dpt.service.management', string='Service')
    description = fields.Char(string='Description')
    qty = fields.Float(string='QTY')
    uom_id = fields.Many2one('uom.uom')
    price = fields.Monetary(currency_field='currency_id', string='Price')
    currency_id = fields.Many2one('res.currency', string='Currency')
    amount_total = fields.Float(string="Amount Total")
    status = fields.Char(string='Status')




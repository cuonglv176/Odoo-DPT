from odoo import models, fields, api, _
from odoo.osv.expression import AND, OR


class DPTSaleOrderFields(models.Model):
    _inherit = 'dpt.sale.order.fields'

    ticket_id = fields.Many2one('helpdesk.ticket')

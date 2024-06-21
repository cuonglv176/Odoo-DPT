from odoo import models, fields, api, _


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    department_id = fields.Many2one('hr.department', string="Department")
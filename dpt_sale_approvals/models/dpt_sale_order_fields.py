from odoo import models, fields, api, _
from odoo.osv.expression import AND, OR


class DPTSaleOrderFields(models.Model):
    _inherit = 'dpt.sale.order.fields'

    approval_id = fields.Many2one('approval.request', string='Approval Change Price', compute="compute_get_approval_id")

    @api.depends('service_id', 'sale_id')
    def compute_get_approval_id(self):
        for rec in self:
            sale_service_id = self.env['dpt.sale.service.management'].sudo().search(
                [('service_id', '=', rec.service_id.id), ('sale_id', '=', rec.sale_id.id)])
            if sale_service_id and sale_service_id.approval_id:
                rec.approval_id = sale_service_id.approval_id
            else:
                rec.approval_id = None

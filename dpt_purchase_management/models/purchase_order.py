from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    sale_id = fields.Many2one('sale.order', 'Sale')
    package_line_ids = fields.One2many('purchase.order.line.package', 'purchase_id', 'Package Line')
    import_package_stock = fields.Boolean('Import Package to Stock')
    purchase_type = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External')
    ], string='Purchase type', default='external', tracking=True)

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if not self.env.context.get('create_from_so', False):
            return res
        # create ticket and auto mark done ticket
        res.create_helpdesk_ticket()
        return res

    def create_helpdesk_ticket(self):
        helpdesk_vals = self.get_helpdesk_vals()
        if helpdesk_vals:
            self.env['helpdesk.ticket'].sudo().create(helpdesk_vals)

    def get_helpdesk_vals(self):
        sale_service_ids = self.sale_id.sale_service_ids.filtered(lambda s: s.service_id.is_purchase_service)
        if not sale_service_ids:
            return {}
        department_id = sale_service_ids.filtered(
            lambda s: s.department_id).department_id.id if sale_service_ids.filtered(
            lambda s: s.department_id) else None
        service_lines_ids = []
        for sale_service_id in sale_service_ids:
            service_lines_ids.append((0, 0, {
                'service_id': sale_service_id.service_id.id,
                'qty': sale_service_id.qty,
                'uom_id': sale_service_id.uom_id.id if sale_service_id.uom_id else None,
                'price': sale_service_id.price
            }))
        helpdesk_stage_id = self.env['helpdesk.stage'].search([('is_done_stage', '=', True)], limit=1)
        if not helpdesk_stage_id:
            raise ValidationError(_('Please config 1 helpdesk stage is finish stage!!'))
        return {
            'sale_id': self.sale_id.id if self.sale_id else None,
            'purchase_id': self.id,
            'partner_id': self.sale_id.partner_id.id if self.sale_id else None,
            'department_id': department_id,
            'service_lines_ids': service_lines_ids,
            'stage_id': helpdesk_stage_id.id,
        }

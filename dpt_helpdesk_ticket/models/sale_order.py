from odoo import models, fields, api, _


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    count_ticket = fields.Integer(compute='_compute_count_ticket')

    def get_tickets(self):
        return {
            'name': "Service Ticket",
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'target': 'self',
            'views': [[False, 'tree']],
            'domain': [('sale_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def _compute_count_ticket(self):
        for record in self:
            record.count_ticket = self.env['helpdesk.ticket'].search_count([('sale_id', '=', record.id)])

    def action_create_ticket(self):
        if self.sale_service_ids:
            department = self.sale_service_ids[0].department_id.id
        else:
            department = False
        service_ids = []
        for r in self.sale_service_ids:
            service_ids.append((0, 0, {
                'service_id': r.service_id.id,
                'description': r.description,
                'qty': r.qty,
                'uom_id': r.uom_id.id,
                'price': r.price,
                'currency_id': r.currency_id,
                'amount_total': r.amount_total,
                'status': r.price_status,
            }))
        return {
            'name': "Service Ticket",
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'target': 'self',
            'views': [[False, 'form']],
            'context': {
                'default_sale_id': self.id,
                'default_partner_id': self.partner_id.id,
                'default_service_lines_ids': service_ids,
                'default_department_id': department,
            },
        }
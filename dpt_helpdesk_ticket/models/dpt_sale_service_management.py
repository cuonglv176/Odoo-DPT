from odoo import models, fields, api, _


class DPTSaleServiceManagement(models.Model):
    _inherit = 'dpt.sale.service.management'

    def write(self, vals):
        if 'service_id' in vals:
            return super().write(vals)
        for item in self:
            ticket_line_ids = item.sale_id.ticket_ids.mapped('service_lines_ids').filtered(
                lambda sl: sl.service_id.id == item.service_id.id and sl.uom_id.id == item.uom_id.id)
            if not ticket_line_ids:
                continue
            service_line_ticket_vals = {}
            if 'uom_id' in vals:
                service_line_ticket_vals.update({
                    'uom_id': vals.get('uom_id')
                })

            if 'price' in vals:
                service_line_ticket_vals.update({
                    'price': vals.get('price')
                })
            ticket_line_ids.write(service_line_ticket_vals)
        return super().write(vals)

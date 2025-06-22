from odoo import models, fields, api, _


class DPTSaleServiceManagement(models.Model):
    _inherit = 'dpt.sale.service.management'

    ticket_id = fields.Many2one('helpdesk.ticket')

    def write(self, vals):
        if 'service_id' in vals:
            return super().write(vals)
        rec = super().write(vals)
        for item in self:
            ticket_line_ids = item.sale_id.ticket_ids.mapped('service_lines_ids').filtered(
                lambda sl: sl.service_id.id == item.service_id.id and sl.uom_id.id == item.uom_id.id)
            if not ticket_line_ids:
                continue
            updates = []
            params = []
            if 'uom_id' in vals:
                updates.append("uom_id = %s")
                uom_value = vals.get('uom_id')
                if uom_value is False:
                    params.append(None)
                else:
                    params.append(uom_value)
            if 'price' in vals:
                updates.append("price = %s")
                params.append(vals.get('price'))
            if 'compute_value' in vals:
                updates.append("qty = %s")
                params.append(vals.get('compute_value'))
            updates.append("amount_total = %s")
            params.append(self.amount_total)
            if updates:
                update_query = f"""
                    UPDATE dpt_helpdesk_servie_line
                    SET {", ".join(updates)}
                    WHERE id IN %s
                """
                params.append(tuple(ticket_line_ids.ids))
                self.env.cr.execute(update_query, params)
        return rec

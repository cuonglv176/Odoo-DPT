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
            if 'compute_value' in vals:
                service_line_ticket_vals.update({
                    'qty': vals.get('compute_value')
                })
            if 'amount_total' in vals:
                service_line_ticket_vals.update({
                    'amount_total': vals.get('amount_total')
                })
            ticket_line_ids.write(service_line_ticket_vals)
        return super().write(vals)

    def write(self, vals):
        if 'service_id' in vals:
            return super().write(vals)

        for item in self:
            ticket_line_ids = item.sale_id.ticket_ids.mapped('service_lines_ids').filtered(
                lambda sl: sl.service_id.id == item.service_id.id and sl.uom_id.id == item.uom_id.id)
            if not ticket_line_ids:
                continue
            updates = []
            params = []
            if 'uom_id' in vals:
                updates.append("uom_id = %s")
                params.append(vals.get('uom_id'))
            if 'price' in vals:
                updates.append("price = %s")
                params.append(vals.get('price'))
            if 'compute_value' in vals:
                updates.append("qty = %s")
                params.append(vals.get('compute_value'))
            if 'amount_total' in vals:
                updates.append("amount_total = %s")
                params.append(vals.get('amount_total'))
            if updates:
                update_query = f"""
                    UPDATE dpt_helpdesk_servie_line
                    SET {", ".join(updates)}
                    WHERE id IN %s
                """
                params.append(tuple(ticket_line_ids.ids))
                self.env.cr.execute(update_query, params)
        return super().write(vals)

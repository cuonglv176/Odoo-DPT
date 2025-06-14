from odoo import fields, models, api, _


class DPTSaleServiceManagement(models.Model):
    _inherit = 'dpt.sale.service.management'

    picking_id = fields.Many2one('stock.picking', 'Picking')

    def write(self, vals):
        old_values = {rec.id: rec.read(vals.keys())[0] for rec in self}
        res = super(DPTSaleServiceManagement, self).write(vals)
        for rec in self:
            if rec.picking_id and rec.picking_id.exists():
                changes = []
                for field, new_value in vals.items():
                    old_value = old_values[rec.id].get(field)
                    if old_value != new_value:
                        changes.append(f"{field}: {old_value} -> {new_value}")
                if changes:
                    message = f"Thông tin dịch vụ thay đổi: {rec.service_id.name}: " + ", ".join(changes)
                    try:
                        rec.picking_id.message_post(body=message, message_type='comment')
                    except:
                        continue
        return res

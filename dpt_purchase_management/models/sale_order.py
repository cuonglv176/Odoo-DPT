from odoo import fields, models, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    product_order_count = fields.Boolean('Product Order Count', compute="_compute_product_order_count")

    def _compute_product_order_count(self):
        for item in self:
            item.product_order_count = len(item.order_line)

    def action_create_purchase_order(self):
        default_order_line = []
        for order_line in self.order_line:
            default_order_line.append((0, 0, {
                'product_id': order_line.product_tmpl_id.product_id.id,
                'name': order_line.name,
                'product_qty': order_line.product_uom_qty,
                'product_uom': order_line.product_uom.id,
                'price_unit': order_line.price_unit,
            }))
        return {
            'name': _('Create your first Appointment'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'target': 'new',
            'view_mode': 'form',
            'views': [(self.env.ref('purchase.purchase_order_form').sudo().id, "form")],
            'context': {
                'default_order_line': default_order_line,
            }
        }

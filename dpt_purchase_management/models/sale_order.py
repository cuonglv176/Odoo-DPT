from odoo import fields, models, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    product_order_count = fields.Integer('Product Order Count', compute="_compute_product_order_count")
    show_create_po = fields.Boolean('Show create PO', compute="_compute_show_create_po")
    purchase_ids = fields.One2many('purchase.order', 'sale_id', 'Purchase')

    def _compute_show_create_po(self):
        for item in self:
            item.show_create_po = (any(item.sale_service_ids.mapped('service_id').mapped(
                'is_purchase_service')) if item.sale_service_ids else False) and len(item.order_line) != 0

    def _compute_product_order_count(self):
        for item in self:
            item.product_order_count = len(item.purchase_ids)

    def action_create_purchase_order(self):
        default_order_line = []
        for order_line in self.order_line:
            product_id = self.env['product.product'].search(
                [('product_tmpl_id', '=', order_line.product_template_id.id)], limit=1)
            default_order_line.append((0, 0, {
                'product_id': product_id.id if product_id else None,
                'name': order_line.name,
                'product_qty': order_line.product_uom_qty,
                'product_uom': order_line.product_uom.id,
                'price_unit': order_line.price_unit,
            }))
        return {
            'name': _('Create PO'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'target': 'new',
            'view_mode': 'form',
            'views': [(self.env.ref('purchase.purchase_order_form').sudo().id, "form")],
            'context': {
                'default_sale_id': self.id,
                'default_order_line': default_order_line,
                'default_date_planned': fields.Datetime.now(),
                'no_compute_price': True,
                'create_from_so': True
            }
        }

    def action_open_po(self):
        purchase_action = self.env.ref('purchase.purchase_rfq').sudo().read()[0]
        purchase_action['domain'] = [('id', 'in', self.purchase_ids.ids)]
        return purchase_action

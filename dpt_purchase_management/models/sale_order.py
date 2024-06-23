from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


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
            item.product_order_count = len(item.sudo().purchase_ids)

    def action_confirm(self):
        res = super().action_confirm()
        for order in self:
            # order.validate_create_po()
            # order.action_create_purchase_order()
            # delete stock_picking of SO:
            order.sudo().picking_ids.unlink()
        return res

    def validate_create_po(self):
        have_purchase_service = (any(self.sale_service_ids.mapped('service_id').mapped(
            'is_purchase_service')) if self.sale_service_ids else False)
        if not have_purchase_service:
            return
        if have_purchase_service and not self.order_line:
            raise ValidationError(_("Please add some Order line for creating PO!"))

    def action_create_purchase_order(self):
        self.validate_create_po()
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
                'date_planned': fields.Datetime.now(),
            }))
        # po_id = self.env['purchase.order'].create({
        #     'sale_id': self.id,
        #     'order_line': default_order_line,
        #     'date_planned': fields.Datetime.now(),
        #     'import_package_stock': True,
        #     'partner_id': self.env.ref('dpt_purchase_management.partner_default_supplier').id,
        # })
        default_package_unit_id = self.env['uom.uom'].sudo().search([('is_default_package_unit', '=', True)], limit=1)
        default_package_line_ids = [(0, 0, {
            'uom_id': default_package_unit_id.id if default_package_unit_id else None,
            'quantity': 1,
        })]
        return {
            'name': _('Create PO'),
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'target': 'new',
            'view_mode': 'form',
            'views': [(self.env.ref('purchase.purchase_order_form').sudo().id, "form")],
            'context': {
                'default_sale_id': self.id,
                'default_partner_id':  self.env.ref('dpt_purchase_management.partner_default_supplier').id,
                'default_order_line': default_order_line,
                'default_package_line_ids': default_package_line_ids,
                'default_date_planned': fields.Datetime.now(),
                'default_import_package_stock': True,
                'no_compute_price': True,
                'create_from_so': True
            }
        }

    def action_open_po(self):
        purchase_action = self.env.ref('purchase.purchase_rfq').sudo().read()[0]
        purchase_action['domain'] = [('id', 'in', self.purchase_ids.ids)]
        return purchase_action

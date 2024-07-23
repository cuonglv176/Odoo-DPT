# -*- coding: utf-8 -*-

from odoo import models, fields, api, _, SUPERUSER_ID
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.depends('order_line.move_ids.picking_id', 'package_line_ids.move_ids.picking_id')
    def _compute_picking_ids(self):
        for order in self:
            order.picking_ids = order.order_line.move_ids.picking_id | order.package_line_ids.move_ids.picking_id

    def button_confirm_with_package(self):
        for order in self:
            order.validate_order()
            # create stock_move
            order.sudo().action_create_stock()
            # update state
            order.action_mark_done_po()

    def validate_order(self):
        if not self.package_line_ids:
            raise ValidationError(_("Please add some Package line!"))
        not_uom_package_line_ids = self.package_line_ids.filtered(lambda pl: not pl.uom_id)
        if not_uom_package_line_ids:
            raise ValidationError(
                _("Please add Units to Package line with lot name: %s !") % ', '.join(
                    not_uom_package_line_ids.mapped('name')))
        not_product_package_line_ids = self.package_line_ids.filtered(lambda pl: pl.uom_id and not pl.uom_id.product_id)
        if not_product_package_line_ids:
            raise ValidationError(
                _("Please configurate Product to Units of Package line with lot name: %s !") % ', '.join(
                    not_product_package_line_ids.mapped('name')))

    def action_mark_done_po(self):
        self.write({'state': 'purchase', 'date_approve': fields.Datetime.now()})
        self.filtered(lambda p: p.company_id.po_lock == 'lock').write({'state': 'done'})

    def action_create_stock(self):
        pickings = self.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
        if not pickings:
            res = self._prepare_picking()
            picking = self.env['stock.picking'].with_user(SUPERUSER_ID).create(res)
            picking = picking
        else:
            picking = pickings[0]
        self.package_line_ids.write({
            'picking_id': picking.id
        })
        moves = self.package_line_ids._create_stock_moves(picking)

    def get_picking(self):
        pickings = self.picking_ids.filtered(lambda x: x.state not in ('done', 'cancel'))
        if not pickings:
            res = self._prepare_picking()
            picking = self.env['stock.picking'].with_user(SUPERUSER_ID).create(res)
            picking = picking
        else:
            picking = pickings[0]
        self.package_line_ids.write({
            'picking_id': picking.id
        })
        return picking

    def button_confirm(self):
        res = super().button_confirm()
        for order in self:
            order.validate_order()
            picking = order.get_picking()
            order.package_line_ids._create_stock_moves(picking)
        return res

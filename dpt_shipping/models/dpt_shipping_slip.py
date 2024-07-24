# -*- coding: utf-8 -*-

from odoo import models, fields, api


class DPTShippingSlip(models.Model):
    _name = 'dpt.shipping.slip'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name')
    transfer_code = fields.Char('Transfer Code')
    transfer_code_chinese = fields.Char('Transfer Code in Chinese')
    out_picking_ids = fields.Many2many('stock.picking', 'stock_picking_out_shipping_rel', 'shipping_slip_id',
                                       'picking_id', string='Out Picking')
    export_import_ids = fields.Many2many('dpt.export.import', string='Export Import', compute="_compute_information")
    in_picking_ids = fields.Many2many('stock.picking', 'stock_picking_in_shipping_rel', 'shipping_slip_id',
                                      'picking_id', string='In Picking')
    sale_ids = fields.Many2many('sale.order', string='Sale Order', compute="_compute_information")
    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle')
    vehicle_country = fields.Selection(related='vehicle_id.country')
    vn_vehicle_stage_id = fields.Many2one('dpt.vehicle.stage', 'Vehicle Stage', domain=[('country', '=', 'vietnamese')])
    cn_vehicle_stage_id = fields.Many2one('dpt.vehicle.stage', 'Vehicle Stage', domain=[('country', '=', 'chinese')])
    vehicle_stage_log_ids = fields.One2many('dpt.vehicle.stage.log', 'shipping_slip_id', 'Vehicle Stage Log')
    send_shipping_id = fields.Many2one('dpt.shipping.slip', 'Shipping Sent')
    vehicle_driver_id = fields.Many2one(related="vehicle_id.driver_id")
    vehicle_license_plate = fields.Char(related="vehicle_id.license_plate")
    vehicle_driver_phone = fields.Char(compute="_compute_vehicle_driver_phone")
    note = fields.Text('Note')

    total_volume = fields.Float('Total Volume (m3)', compute="_compute_information")
    total_weight = fields.Float('Total Weight (kg)', compute="_compute_information")
    total_num_packing = fields.Float('Total Num Packing', compute="_compute_information")

    def _compute_information(self):
        for item in self:
            item.sale_ids = (item.in_picking_ids | item.out_picking_ids).mapped('sale_purchase_id')
            item.export_import_ids = (item.in_picking_ids | item.out_picking_ids).mapped('sale_purchase_id').mapped(
                'dpt_export_import_ids')
            if item.vehicle_country == 'chinese':
                item.total_volume = sum(item.out_picking_ids.mapped('total_volume'))
                item.total_weight = sum(item.out_picking_ids.mapped('total_weight'))
                item.total_num_packing = sum(item.out_picking_ids.mapped('package_ids').mapped('quantity'))
            elif item.vehicle_country == 'vietnamese':
                item.total_volume = sum(item.in_picking_ids.mapped('total_volume'))
                item.total_weight = sum(item.in_picking_ids.mapped('total_weight'))
                item.total_num_packing = sum(item.in_picking_ids.mapped('package_ids').mapped('quantity'))
            else:
                item.total_volume = 0
                item.total_weight = 0
                item.total_num_packing = 0

    def _compute_vehicle_driver_phone(self):
        for item in self:
            item.vehicle_driver_phone = item.vehicle_driver_id.phone or item.vehicle_driver_id.mobile if item.vehicle_driver_id else None

    @api.model
    def create(self, vals):
        if 'name' not in vals:
            vals['name'] = self._generate_service_code()
        return super(DPTShippingSlip, self).create(vals)

    def _generate_service_code(self):
        sequence = self.env['ir.sequence'].next_by_code('shipping.slip.seq') or '00'
        return f'{sequence}'

    def write(self, vals):
        if 'vn_vehicle_stage_id' not in vals and 'cn_vehicle_stage_id' not in vals:
            return super().write(vals)
        last_time_record_id = self.vehicle_stage_log_ids.sorted(key=lambda x: x['log_datetime'], reverse=True)[:1]
        last_time = last_time_record_id.log_datetime if last_time_record_id else self.create_date
        log_time = fields.Datetime.now() - last_time
        if self.vehicle_country == 'vietnamese':
            current_stage_id = self.vn_vehicle_stage_id
            res = super().write(vals)
            next_stage_id = self.vn_vehicle_stage_id
            if current_stage_id == next_stage_id:
                return res
            self.env['dpt.vehicle.stage.log'].create({
                'vehicle_id': self.vehicle_id.id,
                'shipping_slip_id': self.id,
                'current_stage_id': current_stage_id.id,
                'next_stage_id': next_stage_id.id,
                'log_time': log_time.total_seconds() / 3600,
            })
        elif self.vehicle_country == 'chinese':
            current_stage_id = self.cn_vehicle_stage_id
            res = super().write(vals)
            next_stage_id = self.cn_vehicle_stage_id
            if current_stage_id == next_stage_id:
                return res
            self.env['dpt.vehicle.stage.log'].create({
                'vehicle_id': self.vehicle_id.id,
                'shipping_slip_id': self.id,
                'current_stage_id': current_stage_id.id,
                'next_stage_id': next_stage_id.id,
                'log_time': log_time.total_seconds() / 3600,
            })
        else:
            return super().write(vals)
        return res

    @api.constrains('picking_ids', 'transfer_code', 'transfer_code_chinese')
    def constrains_transfer_code(self):
        for item in self:
            item.in_picking_ids.write({
                'transfer_code': item.transfer_code,
                'transfer_code_chinese': item.transfer_code_chinese,
            })

    def action_create_shipping_slip_receive(self):
        action = self.env.ref('dpt_shipping.dpt_shipping_split_wizard_action').sudo().read()[0]
        action['context'] = {
            'default_shipping_id': self.id,
            'default_picking_ids': self.out_picking_ids.mapped('x_in_transfer_picking_id').ids,
            'default_sale_ids': self.sale_ids.ids,
            'default_available_sale_ids': self.sale_ids.ids,
            'default_available_picking_ids': self.out_picking_ids.mapped('x_in_transfer_picking_id').ids,
        }
        return action


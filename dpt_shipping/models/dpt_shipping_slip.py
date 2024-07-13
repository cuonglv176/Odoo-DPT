# -*- coding: utf-8 -*-

from odoo import models, fields, api


class DPTShippingSlip(models.Model):
    _name = 'dpt.shipping.slip'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name')
    transfer_code = fields.Char('Transfer Code')
    transfer_code_chinese = fields.Char('Transfer Code in Chinese')
    out_picking_ids = fields.Many2many('stock.picking', 'stock_picking_out_shipping_rel', 'shipping_slip_id',
                                       'picking_id', string='Out Picking', domain="[('valid_cutlist','=', True)]")
    export_import_ids = fields.Many2many('dpt.export.import', string='Export Import', compute="_compute_information")
    in_picking_ids = fields.Many2many('stock.picking', 'stock_picking_in_shipping_rel', 'shipping_slip_id',
                                      'picking_id', string='In Picking', domain="[('valid_cutlist','=', True)]")
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
    state = fields.Selection([
        ('draft', 'Draft'),
        ('ready_get_car', 'Ready Get Car'),
        ('start_get_car', 'Start Get Car'),
        ('finish_get_car', 'Finish Get Car'),
        ('start_drop_good', 'Start Drop Good'),
        ('finish_drop_good', 'Finish Drop Good'),
        ('declared', 'Declared'),
        ('move_other_car', 'Move Other Car'),
        ('finish', 'Finish'),
    ], default='draft', string='State')

    def _compute_information(self):
        for item in self:
            item.sale_ids = (item.in_picking_ids | item.out_picking_ids).mapped('sale_purchase_id')
            item.export_import_ids = (item.in_picking_ids | item.out_picking_ids).mapped('sale_purchase_id').mapped(
                'dpt_export_import_ids')

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
            item.picking_ids.write({
                'transfer_code': item.transfer_code,
                'transfer_code_chinese': item.transfer_code_chinese,
            })

    def action_create_shipping_slip_receive(self):
        action = self.env.ref('dpt_shipping.dpt_shipping_split_wizard_action').sudo().read()[0]
        action['context'] = {
            'default_shipping_id': self.id,
            'default_sale_ids': self.sale_ids.ids,
            'default_available_sale_ids': self.sale_ids.ids,
        }
        return action

    def action_ready_get_car(self):
        self.state = 'ready_get_car'

    def action_start_get_car(self):
        self.state = 'start_get_car'

    def action_finish_get_car(self):
        self.state = 'finish_get_car'

    def action_start_drop_good(self):
        self.state = 'start_drop_good'

    def action_finish_drop_good(self):
        self.state = 'finish_drop_good'

    def action_declared(self):
        self.state = 'declared'

    def action_move_other_car(self):
        self.state = 'move_other_car'

    def action_finish(self):
        self.state = 'finish'

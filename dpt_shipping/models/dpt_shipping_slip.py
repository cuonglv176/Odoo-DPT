# -*- coding: utf-8 -*-

from odoo import models, fields, api


class DPTShippingSlip(models.Model):
    _name = 'dpt.shipping.slip'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name')
    transfer_code = fields.Char('Transfer Code')
    transfer_code_chinese = fields.Char('Transfer Code in Chinese')
    picking_ids = fields.Many2many('stock.picking', string='Picking')
    sale_ids = fields.Many2many('sale.order', string='Sale Order')
    vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle')
    vehicle_country = fields.Selection(related='vehicle_id.country')
    vn_vehicle_stage_id = fields.Many2one('dpt.vehicle.stage', 'Vehicle Stage', domain=[('country', '=', 'vietnamese')])
    cn_vehicle_stage_id = fields.Many2one('dpt.vehicle.stage', 'Vehicle Stage', domain=[('country', '=', 'chinese')])
    vehicle_stage_log_ids = fields.One2many('dpt.vehicle.stage.log', 'shipping_slip_id', 'Vehicle Stage Log')

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
            })
        return res

    @api.constrains('picking_ids', 'transfer_code', 'transfer_code_chinese')
    def constrains_transfer_code(self):
        for item in self:
            item.picking_ids.write({
                'transfer_code': item.transfer_code,
                'transfer_code_chinese': item.transfer_code_chinese,
            })

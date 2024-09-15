from odoo import _, api, fields, models
import requests
import logging
import hashlib
import base64
import os
import json

from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class ServerActions(models.Model):
    _name = 'ir.actions.server'
    _description = 'Server Action'
    _inherit = ['ir.actions.server']

    state = fields.Selection(selection_add=[
        ('zalo_zns', 'Send Zalo ZNS'),
    ], ondelete={'zalo_zns': 'cascade'})
    zalo_template_id = fields.Many2one('dpt.zalo.template', string='Template Zalo')
    recipient_id = fields.Many2one('ir.model.fields', string='Gửi Cho',
                                   domain="[('model_id','=',model_id),('ttype','=','many2one'),('relation','=','res.partner')]")
    param_ids = fields.One2many('zalo.actions.server.params', 'actions_server_id', string='Params')

    @api.onchange('zalo_template_id')
    def onchange_update_params_zalo_zns(self):
        if self.zalo_template_id:
            self.param_ids = [(5, 0, 0)]
            new_lines = []
            zalo_list_params = json.loads(self.zalo_template_id.zalo_list_params)
            for param in zalo_list_params:
                new_lines.append(
                    (0, 0, {
                        'name': param.get('name')
                    }
                     )
                )

            self.param_ids = new_lines
        else:
            self.param_ids = [(5, 0, 0)]

    @api.onchange('zalo_template_id', 'param_ids')
    def _update_action_code_zalo(self):
        if self.param_ids:
            template_id = self.zalo_template_id.zalo_app_id
            recipient = f'record.{self.recipient_id.name}.phone'
            params = []
            for param_id in self.param_ids:
                params.append({
                    param_id.name: f'record.{param_id.fields_id.name}'
                })
            self.code = f"""
                template_id = env['dpt.zalo.template'].browse({self.zalo_template_id.id})
                template_id._action_send_zalo_notification(record,'{template_id}',{recipient},'{params}')
            """

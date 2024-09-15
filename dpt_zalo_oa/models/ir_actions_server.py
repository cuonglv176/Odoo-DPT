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
    param_ids = fields.One2many('zalo.actions.server.params', 'actions_server_id', string='Params')

    @api.onchange('zalo_template_id')
    def onchange_update_params_zalo_zns(self):
        if self.zalo_template_id:
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

    def _run_action_zalo_zns_multi(self):
        _logger.info(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
        _logger.info(self.zalo_template_id)
        _logger.info(self.param_ids)

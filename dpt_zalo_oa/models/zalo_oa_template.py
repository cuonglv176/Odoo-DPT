import requests
from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class DptZaloTemplate(models.Model):
    _name = 'dpt.zalo.template'
    _description = 'Zalo Template for ZNS'

    name = fields.Char(string="Template Name")
    zalo_app_id = fields.Char(string="Zalo App ID", readonly=True)
    zalo_template_id = fields.Char(string="Zalo Template ID", readonly=True)
    zalo_template_content = fields.Text(string="Template Content", readonly=True)
    zalo_list_params = fields.Json(string='List Params')

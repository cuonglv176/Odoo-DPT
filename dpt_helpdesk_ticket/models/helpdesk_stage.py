from odoo import models, fields, api, _


class HelpdeskStage(models.Model):
    _inherit = 'helpdesk.stage'

    is_done_stage = fields.Boolean('Is Done Stage')

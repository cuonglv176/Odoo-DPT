from odoo import models, fields, api, _


class KpSendMail(models.Model):
    _name = 'ks_dashboard_ninja.kpi_mail'
    _description = 'Dashboard Ninja Kpi mail'


    name = fields.Char(string="Email To:")

from odoo import models, fields, api, _


class KsDashboardNinjaBoardItemAction(models.Model):
    _name = 'ks_dashboard_ninja.child_board'
    _description = 'Dashboard Ninja Child Board'

    name = fields.Char()
    ks_dashboard_ninja_id = fields.Many2one("ks_dashboard_ninja.board", string="Select Dashboard")
    ks_gridstack_config = fields.Char('Item Configurations')
    # ks_board_active_user_ids = fields.Many2many('res.users')
    ks_active = fields.Boolean("Is Selected")
    ks_dashboard_menu_name = fields.Char(string="Menu Name", related='ks_dashboard_ninja_id.ks_dashboard_menu_name', store=True)
    board_type = fields.Selection([('default', 'Default'), ('child', 'Child')])
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)


    def write(self,vals):
        return super(KsDashboardNinjaBoardItemAction, self).write(vals)

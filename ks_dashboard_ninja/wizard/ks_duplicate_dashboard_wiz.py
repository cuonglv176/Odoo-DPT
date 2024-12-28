# -*- coding: utf-8 -*-

from odoo import api, fields, models


class KSduplicateDashboardWizard(models.TransientModel):
    _name = 'ks.dashboard.duplicate.wizard'
    _description = 'Dashboard Duplicate Wizard'

    ks_top_menu_id = fields.Many2one('ir.ui.menu', string="Show Under Menu", required=True, domain="[('parent_id','=',False)]",
                                     default=lambda self: self.env['ir.ui.menu'].search(
                                         [('name', '=', 'My Dashboard')]))

    def DuplicateDashBoard(self):
        '''this function returns acion id of ks.dashboard.duplicate.wizard'''
        action = self.env['ir.actions.act_window']._for_xml_id(
            'ks_dashboard_ninja.ks_duplicate_dashboard_wizard')
        action['context'] = {'dashboard_id': self.id}
        return action

    def ks_duplicate_record(self):
        '''this function creats record of ks_dashboard_ninja.board and return dashboard action_id'''
        dashboard_id = self._context.get('dashboard_id')
        dup_dash = self.env['ks_dashboard_ninja.board'].browse(dashboard_id).copy({'ks_dashboard_top_menu_id': self.ks_top_menu_id.id})
        context = {'ks_reload_menu': True, 'ks_menu_id': dup_dash.ks_dashboard_menu_id.id}
        dash_id = self.env['ks_dashboard_ninja.board'].browse(dashboard_id)
        if not dup_dash.ks_dashboard_items_ids:
            for item in dash_id.ks_dashboard_items_ids:
                item.sudo().copy({'ks_dashboard_ninja_board_id': dup_dash.id})
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }


class KSDeleteDashboardWizard(models.TransientModel):
    _name = 'ks.dashboard.delete.wizard'
    _description = 'Dashboard Delete Wizard'


    def ks_delete_record(self, **kwargs):
        '''this function creats record of ks_dashboard_ninja.board and return dashboard action_id'''
        dashboard_id = kwargs.get('dashboard_id')
        self.env['ks_dashboard_ninja.board'].browse(dashboard_id).unlink()
        action = self.env['ir.actions.client']._for_xml_id(
            'ks_dashboard_ninja.board_dashboard_action_window')
        return action

# -*- coding: utf-8 -*-
from . import models
from . import controllers

from odoo.api import Environment, SUPERUSER_ID


def uninstall_hook(cr, registry):
    env = Environment(cr, SUPERUSER_ID, {})
    for rec in env['ks_custom_report.ks_report'].search([]):
        rec.ks_tree_view_id.unlink()
        rec.ks_search_view_id.unlink()
        rec.ks_pivot_view_id.unlink()

        rec.ks_cr_action_id.unlink()
        rec.ks_cr_menu_id.unlink()

        if rec.ks_cr_model_id:
            rec.ks_cr_model_id.unlink()

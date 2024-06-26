# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    dpt_export_import_ids = fields.One2many('dpt.export.import', 'sale_id', string='Declaration')
    dpt_export_import_line_ids = fields.One2many('dpt.export.import.line', 'sale_id', string='Declaration line')
    declaration_count = fields.Integer(string='Declaration count', compute="_compute_declaration_count")
    declaration_line_count = fields.Integer(string='Declaration count line', compute="_compute_declaration_count")

    def _compute_declaration_count(self):
        for rec in self:
            rec.declaration_count = len(rec.dpt_export_import_ids)
            rec.declaration_line_count = len(rec.dpt_export_import_line_ids)

    def action_open_declaration(self):
        view_id = self.env.ref('dpt_export_import.view_dpt_export_import_tree').id
        view_form_id = self.env.ref('dpt_export_import.view_dpt_export_import_form').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.export.import',
            'name': _('Declaration'),
            'view_mode': 'tree,form',
            'domain': [('sale_id', '=', self.id)],
            'views': [[view_id, 'tree'], [view_form_id, 'form']],
            'context': {
                'default_sale_id': self.id,
            },
        }

    def action_open_declaration_line(self):
        view_id = self.env.ref('dpt_export_import.view_dpt_export_import_line_tree').id
        view_form_id = self.env.ref('dpt_export_import.view_dpt_export_import_line_form').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.export.import.line',
            'name': _('Declaration Line'),
            'view_mode': 'tree,form',
            'domain': [('sale_id', '=', self.id)],
            'views': [[view_id, 'tree'], [view_form_id, 'form']],
        }


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    dpt_export_import_line_ids = fields.One2many('dpt.export.import.line', 'sale_line_id', string='Declaration line')

    def action_open_dpt_export_import_line(self):
        view_id = self.env.ref('dpt_export_import.view_dpt_export_import_line_form').id
        if not self.dpt_export_import_line_ids:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Update Declaration Line'),
                'view_mode': 'form',
                'res_model': 'dpt.export.import.line',
                'target': 'new',
                'views': [[view_id, 'form']],
                'context': {
                    'default_sale_line_id': self.id,
                    'default_sale_id': self.order_id.id,
                    'default_product_id': self.product_id.id,
                    'default_dpt_english_name': self.product_id.dpt_english_name,
                    'default_dpt_description': self.product_id.dpt_description,
                    'default_dpt_n_w_kg': self.product_id.dpt_n_w_kg,
                    'default_dpt_g_w_kg': self.product_id.dpt_g_w_kg,
                    'default_dpt_uom_id': self.product_id.dpt_uom_id,
                    'default_dpt_uom2_ecus_id': self.product_id.dpt_uom2_ecus_id,
                    'default_dpt_uom2_id': self.product_id.dpt_uom2_id,
                    'default_dpt_price_kd': self.product_id.dpt_price_kd,
                    'default_dpt_tax_import': self.product_id.dpt_tax_import,
                    'default_dpt_tax_ecus5': self.product_id.dpt_tax_ecus5,
                    'default_dpt_tax': self.product_id.dpt_tax,
                    'default_dpt_exchange_rate': self.product_id.dpt_exchange_rate,
                    'default_dpt_code_hs': self.product_id.dpt_code_hs,
                    'default_dpt_uom1_id': self.product_id.dpt_uom1_id,
                    'default_dpt_sl1': self.product_id.dpt_sl1,
                    'default_dpt_sl2': self.product_id.dpt_sl2,
                },
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Update Declaration Line'),
                'view_mode': 'form',
                'res_model': 'dpt.export.import.line',
                'target': 'new',
                'res_id': self.dpt_export_import_line_ids[0].id,
                'views': [[view_id, 'form']],
            }

from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    contract_id = fields.Many2one('dpt.contract.management', string='Contract')

    def create_new_contract(self):
        return {
            'name': "Contract",
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.creat.new.contract',
            'target': 'new',
            'view_mode': 'form',
            'view_id': self.env.ref('dpt_contract_management.view_dpt_creat_new_contract_form').id,
            # 'domain': [('sale_id', '=', self.id)],
            'context': dict(self._context, **{
                'default_partner_id': self.partner_id.id,
                'default_res_model': self._name,
                'default_res_id': self.id,
            })
        }
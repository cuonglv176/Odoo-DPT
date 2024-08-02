from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    contract_id = fields.Many2one('dpt.contract.management', string='Last Contract Update')
    count_contract = fields.Integer(compute='_compute_count_contract')

    def _compute_count_contract(self):
        for record in self:
            record.count_contract = self.env['dpt.contract.management'].search_count([('partner_id', '=', self.id)])

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        current_user = self.env.user
        if not self.env.user.has_group("sales_team.group_sale_salesman_all_leads"):
            if self.env.user.has_group('sales_team.group_sale_salesman'):
                args += [('user_id', '=', current_user.id)]
        partner = self.sudo().search(args, limit=limit)
        return partner.name_get()

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
                'default_partner_id': self.id,
                'default_res_model': self._name,
                'default_res_id': self.id,
            })
        }
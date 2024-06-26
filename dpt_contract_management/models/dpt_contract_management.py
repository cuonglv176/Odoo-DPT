from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    contract_id = fields.Many2one('dpt.contract.management', string='Contract')

    def create_new_contract(self):
        return {
            'name': "Contract",
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.contract.management',
            'target': 'new',
            'views': [[False, 'form']],
            # 'domain': [('sale_id', '=', self.id)],
            # 'context': "{'create': False}"
        }

    def get_exist_contract(self):
        pass

    def action_update_to_contract(self):
        pass


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    contract_id = fields.Many2one('dpt.contract.management', string='Contract')

    def create_new_contract(self):
        pass

    def get_exist_contract(self):
        pass


class DPTContractManagement(models.Model):
    _name = 'dpt.contract.management'

    name = fields.Char(string='Name')
    code = fields.Char(string='Code')
    user_id = fields.Many2one('res.users', string='User')
    type = fields.Selection()
    partner_id = fields.Many2one('res.partner', string='Partner')
    currency_id = fields.Many2one('res.currency', string='Currency')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
    state = fields.Selection([('draft', 'Draft'),
                              ('processing', 'Processing'),
                              ('done', 'Done'),
                              ('cancel', 'Cancelled')], string='State')
    count_so = fields.Integer(compute='_compute_count_so')
    count_po = fields.Integer(compute='_compute_count_po')

    def get_count_so(self):
        return {
            'name': "Sale Order",
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'target': 'self',
            'views': [['tree', 'form']],
            'domain': [('contract_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def _compute_count_so(self):
        for record in self:
            record.count_ticket = self.env['sale.order'].search_count([('contract_id', '=', record.id)])

    def get_count_po(self):
        return {
            'name': "Purchase Order",
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'target': 'self',
            'views': [['tree', 'form']],
            'domain': [('contract_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def _compute_count_po(self):
        for record in self:
            record.count_ticket = self.env['purchase.order'].search_count([('contract_id', '=', record.id)])


class DPTContractManagementLine(models.Model):
    _name = 'dpt.contract.management.line'

    contract_id = fields.Many2one('dpt.contract.management', string='Contract')
    description = fields.Text(string='Description')
    type_file = fields.Text(string='Type')
    attachment_id = fields.Many2one('res.attachment', string='Attachment')

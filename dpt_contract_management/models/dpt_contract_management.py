from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    contract_id = fields.Many2one('dpt.contract.management', string='Contract')

    def create_new_contract(self):
        return {
            'name': "Contract",
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.creat.new.contract',
            'target': 'new',
            'views': [[False, 'form']],
            # 'domain': [('sale_id', '=', self.id)],
            # 'context': "{'create': False}"
        }


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    contract_id = fields.Many2one('dpt.contract.management', string='Contract')

    def create_new_contract(self):
        return {
            'name': "Contract",
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.creat.new.contract',
            'target': 'new',
            'views': [[False, 'form']],
            # 'domain': [('sale_id', '=', self.id)],
            # 'context': "{'create': False}"
        }


class DPTContractManagement(models.Model):
    _name = 'dpt.contract.management'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']

    name = fields.Char(string='Name', tracking=True, required=True)
    code = fields.Char(string='Code', tracking=True, default='NEW', copy=False, index=True  )
    user_id = fields.Many2one('res.users', required=True, string='User', tracking=True)
    type = fields.Selection([('short_term', 'Short Term'),
                             ('long_term', 'Long Term')], tracking=True, required=True)
    partner_id = fields.Many2one('res.partner', required=True, string='Partner', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency', tracking=True)
    start_date = fields.Date(string='Start Date', tracking=True)
    end_date = fields.Date(string='End Date', tracking=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('processing', 'Processing'),
                              ('done', 'Done'),
                              ('close', 'Close'),
                              ('cancel', 'Cancelled')], string='State', tracking=True)
    line_ids = fields.One2many('dpt.contract.management.line', 'contract_id', string='Detail')
    description = fields.Text(string='Description', tracking=True)
    count_so = fields.Integer(compute='_compute_count_so')
    count_po = fields.Integer(compute='_compute_count_po')

    @api.model
    def create(self, vals):
        res = super(DPTContractManagement, self).create(vals)
        if vals.get('code', 'NEW') == 'NEW':
            res.code = res._generate_service_code()
        return res

    def _generate_service_code(self):
        sequence = self.env['ir.sequence'].next_by_code('dpt.contract.management') or '00'
        return f'{sequence}'

    def get_so(self):
        return {
            'name': "Sale Order",
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'target': 'self',
            'views': [(False, 'list'), (False, 'form')],
            'domain': [('contract_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def _compute_count_so(self):
        for record in self:
            record.count_so = self.env['sale.order'].search_count([('contract_id', '=', record.id)])

    def get_po(self):
        return {
            'name': "Purchase Order",
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'target': 'self',
            'views': [(False, 'list'), (False, 'form')],
            'domain': [('contract_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def _compute_count_po(self):
        for record in self:
            record.count_po = self.env['purchase.order'].search_count([('contract_id', '=', record.id)])

    def action_confirm(self):
        self.state = 'processing'

    def action_close(self):
        self.state = 'close'

    def action_cancel(self):
        self.state = 'cancel'


class DPTContractManagementLine(models.Model):
    _name = 'dpt.contract.management.line'

    contract_id = fields.Many2one('dpt.contract.management', string='Contract')
    description = fields.Text(string='Description')
    type_file = fields.Text(string='Type')
    attachment_id = fields.Many2one('res.attachment', string='Attachment')


class DPTCreatNewContract(models.TransientModel):
    _name = 'dpt.creat.new.contract'

    def get_exist_contract(self):
        pass

    def action_update_to_contract(self):
        pass

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



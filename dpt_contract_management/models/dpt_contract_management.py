from odoo import api, fields, models, _


class DPTContractManagement(models.Model):
    _name = 'dpt.contract.management'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'utm.mixin']

    name = fields.Char(string='Name', tracking=True, required=True)
    code = fields.Char(string='Code', tracking=True, default='NEW', copy=False, index=True)
    user_id = fields.Many2one('res.users', required=True, string='User', tracking=True)
    type = fields.Selection([('short_term', 'Short Term'),
                             ('long_term', 'Long Term')], tracking=True, required=True, default='short_term')
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
        if self.env.context.get('dpt_res_model'):
            self.env['log.error.contract'].update_res_record(self.env.context.get('dpt_res_model'), self.env.context.get('dpt_res_id'), res)
        return res

    def write(self, vals):
        res = super(DPTContractManagement, self).write(vals)
        if self.env.context.get('dpt_res_model'):
            self.env['log.error.contract'].update_res_record(self.env.context.get('dpt_res_model'), self.env.context.get('dpt_res_id'), self)
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

    def _compute_count_so(self):
        for record in self:
            record.count_so = self.env['sale.order'].search_count([('contract_id', '=', record.id)])

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

    is_update_exist_contract = fields.Boolean(string='Update Exist Contract')
    contract_id = fields.Many2one('dpt.contract.management', string='Contract')
    partner_id = fields.Many2one('res.partner', string='Partner')
    res_model = fields.Char(string='Model')
    res_id = fields.Integer(string='Id')

    # @api.onchange('is_update_exist_contract')
    # def _onchange_contract(self):
    #     if self.is_update_exist_contract:
    #         return {
    #             'contract_id': {
    #                 'domain': [('partner_id', '=', self.partner_id.id)],
    #             }
    #         }

    def action_update_to_contract(self):
        self.env['log.error.contract'].update_res_record(self.res_model, self.res_id, self.contract_id)
        return {
            'name': "Contract",
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.contract.management',
            'res_id': self.contract_id.id,
            'target': 'self',
            'view_mode': 'form',
            'view_id': self.env.ref('dpt_contract_management.view_service_form').id,
            # 'domain': [('id', '=', self.contract_id.id)],
            'context': {
                'dpt_res_model': self.res_model,
                'dpt_res_id': self.res_id,
            }
        }

    def create_new_contract(self):
        return {
            'name': "Contract",
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.contract.management',
            'target': 'self',
            'views': [[False, 'form']],
            # 'domain': [('sale_id', '=', self.id)],
            'context': {
                'dpt_res_model': self.res_model,
                'dpt_res_id': self.res_id,
                'default_partner_id': self.partner_id.id,
                'default_user_id': self.env.user.id,
            }
        }


class LogErrorContract(models.Model):
    _name = 'log.error.contract'

    description = fields.Text(string='Description')
    res_id = fields.Integer(string='Id')
    res_model = fields.Char(string='Model')
    contract_id = fields.Many2one('dpt.contract', string='Contract')

    def update_res_record(self, res_model, res_id, contract_id):
        res_record = self.env[res_model].browse(res_id)
        if res_record:
            res_record.contract_id = contract_id
        else:
            self.env['log.error.contract'].create({
                'res_model': res_model,
                'res_id': res_id,
                'contract_id': contract_id,
                'description': f"Error when processing {res_model}-{res_id} link with Contract-{contract_id.id}",
            })

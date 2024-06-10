from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo.osv import expression

class ResPartner(models.Model):
    _inherit = 'res.partner'

    dpt_user_name = fields.Char('User Name')
    dpt_ul = fields.Char('UL')
    dpt_shipping_type = fields.Selection(selection=[
        ("official_rank", "Official Rank"),
        ("petty_rank", "Petty Rank")
    ], string='Shipping Type', default='official_rank')
    dpt_gender = fields.Selection(selection=[
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    ], string='Gender', default='male')
    dpt_get_invoice = fields.Boolean(string='Get an invoice?')
    dpt_quote = fields.Char('Quote')
    dpt_declare = fields.Char('Declare')
    dpt_invoice_info = fields.Char('Invoice Info')
    dpt_price_list = fields.Char('Price list/policies are applicable')
    dpt_classification = fields.Char('Customer classification')
    dpt_output_status = fields.Char('Output Status')
    dpt_order_status = fields.Char('Order status')
    dpt_date_of_delivery = fields.Char('Date of delivery')
    company_type = fields.Selection(selection_add=[('household_business', 'Household Business')])

    @api.model
    def _name_search(self, name='', args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if operator == 'ilike' and not (name or '').strip():
            domain = []
        else:
            domain = ['|', ('name', operator, name), ('dpt_user_name', operator, name)]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)

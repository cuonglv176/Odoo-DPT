from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo.osv import expression
import re


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

    @api.depends('complete_name', 'email', 'vat', 'state_id', 'country_id', 'commercial_company_name', 'dpt_user_name')
    @api.depends_context('show_address', 'partner_show_db_id', 'address_inline', 'show_email', 'show_vat', 'lang')
    def _compute_display_name(self):
        for partner in self:
            if partner.dpt_user_name:
                name = f'{partner.dpt_user_name} - {partner.name}'
            else:
                name = f'{partner.name}'
            partner.display_name = name


    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=None, order=None):
        domain = domain or []
        if name:
            name_domain = ['|', ('name', operator, name), ('dpt_user_name', operator, name)]

            domain = expression.AND([name_domain, domain])
        return self._search(domain, limit=limit, order=order)

    @api.onchange('email')
    def validate_email(self):
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if self.email and not re.fullmatch(regex, self.email):
            raise ValidationError(_('Email address is invalid.'))

    @api.onchange('phone', 'mobile')
    def validate_phone(self):
        regex = r'^(?:\+84|0)(?:3[2-9]|5[2689]|7[06-9]|8[1-689]|9[0-46-9])[0-9]{7}$'
        msg = ''
        if self.phone and not re.fullmatch(regex, self.phone):
            msg += f'{_("Phone1 is invalid.")}\n'

        if self.mobile and not re.fullmatch(regex, self.mobile):
            msg += f'{_("Phone2 is invalid.")}\n'
        if msg:
            raise ValidationError(msg)


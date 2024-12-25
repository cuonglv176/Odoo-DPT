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
    company_type = fields.Selection(selection_add=[('household_business', 'Household Business')], store=True)
    cs_user_id = fields.Many2one('res.users', string='Nhân viên CS')
    is_user = fields.Boolean(string='Là nhân viên', default=False, compute="_compute_check_employee", store=True)
    dpt_type_of_partner = fields.Selection([('employee', 'Employee'),
                                            ('customer', 'Customer'),
                                            ('vendor', 'Vendor'),
                                            ('shipping_address', 'Shipping Address'),
                                            ('payment_address', 'Payment Address'),
                                            ('other', 'Other')], string='Type Partner')

    @api.depends('is_company')
    def _compute_company_type(self):
        for partner in self:
            partner.company_type = 'company' if partner.is_company else 'person'

    def _compute_check_employee(self):
        for rec in self:
            rec.is_user = False
            user_id = self.env['res.users'].search([('partner_id', '=', rec.id)])
            if user_id:
                rec.is_user = True

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

    @api.model
    def create(self, vals):
        if vals.get('dpt_user_name'):
            existing_partner = self.search(
                [('dpt_user_name', '=', vals['dpt_user_name']), ('dpt_user_name', '!=', False)], limit=1)
            if existing_partner:
                raise ValidationError(
                    f"Tài khoản {vals['dpt_user_name']} đã tồn tại trong hệ thống cho đối tác {existing_partner.name}.")

        return super(ResPartner, self).create(vals)

    def write(self, vals):
        if vals.get('dpt_user_name'):
            for partner in self:
                existing_partner = self.search(
                    [('dpt_user_name', '=', vals['dpt_user_name']), ('id', '!=', partner.id),
                     ('dpt_user_name', '!=', False)], limit=1)
                if existing_partner:
                    raise ValidationError(
                        f"Tài khoản {vals['dpt_user_name']} đã tồn tại trong hệ thống cho đối tác {existing_partner.name}.")

        return super(ResPartner, self).write(vals)

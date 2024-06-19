# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests
import json
from odoo.osv import expression
from odoo.exceptions import RedirectWarning, UserError, ValidationError
import urllib3
import certifi

# import phonenumbers
from datetime import date, datetime, timedelta

_logger = logging.getLogger(__name__)


# def validate_phone(phone):
#     try:
#         phone = phonenumbers.parse(phone, 'None')
#     except:
#         phone = phonenumbers.parse(phone, 'VN')
#     if phonenumbers.is_valid_number(phone):
#         return True
#     return False


class CRMLEAD(models.Model):
    _inherit = 'crm.lead'


    phone = fields.Char(
        'Phone', tracking=50,
        compute='_compute_phone', inverse='_inverse_phone', readonly=False, store=True, required=True)
    is_exist = fields.Boolean(string='Lead exist', default=False, compute="_compute_is_exist")
    lead_exist_ids = fields.One2many('crm.lead.exist', 'lead_id', string='Lead exist')
    lead_log_note_ids = fields.One2many('crm.lead.log.note', 'lead_id', string='Lead Note')
    status_date_open = fields.Selection(
        [('within_term', 'Within 2 hours'), ('overdue', 'Overdue 2 hours'), ('warning', 'Warning')], string="Status 2h",
        default='within_term', compute="_compute_status_date_open")
    state_id = fields.Many2one(
        "res.country.state", string='State',
        compute='_compute_partner_address_values', readonly=False, store=True,
        domain="[('country_id', '=', 241)]")
    type_customer = fields.Selection(
        selection=[('new', 'New Customer'),
                   ('old', 'Old Customer')
                   ],
        string='Customer type', default='new', compute="auto_update_type_customer")
    date_buy = fields.Datetime(string='Last date buy', compute="_get_date_order")

    @api.depends('partner_id')
    def _compute_name(self):
        for lead in self:
            if not lead.name and lead.partner_id and lead.partner_id.name:
                lead.name = _("%s") % lead.partner_id.name

    @api.depends('order_ids')
    def _get_date_order(self):
        for s in self:
            if s.order_ids:
                order_id = self.env['sale.order'].sudo().search([('opportunity_id','=',s.id),('state','in',('sale','done'))],limit=1, order='date_order desc')
                if order_id:
                    s.date_buy = order_id.date_order
                else:
                    s.date_buy = None
            else:
                s.date_buy = None

    @api.depends('phone')
    def auto_update_type_customer(self):
        for s in self:
            if s.phone:
                partner_ids = self.env['res.partner'].sudo().search(
                    [('phone', '=', s.phone)])
                if partner_ids:
                    type_customer = 'new'
                    for partner_id in partner_ids:
                        order_ids = self.env['sale.order'].sudo().search(
                            [('partner_id', '=', partner_id.id),
                             ('date_order', '<', s.create_date),
                             ('state', 'in', ('sale', 'done'))])
                        a = 0
                        for order_id in order_ids:
                            for line in order_id.order_line:
                                if line.product_id.categ_id.id == 1:
                                    a = 1
                        if a == 1:
                            type_customer = 'old'
                        else:
                            type_customer = 'new'
                    s.type_customer = type_customer
                else:
                    s.type_customer = 'new'
            else:
                s.type_customer = 'new'

    @api.depends('date_open')
    def _compute_status_date_open(self):
        for s in self:
            if s.date_open:
                date_2h = s.date_open + timedelta(hours=2)
                date_15ph = s.date_open + timedelta(hours=2) - timedelta(minutes=15)
                if s.stage_id.id == 1:
                    if date_15ph >= datetime.now():
                        s.status_date_open = 'within_term'
                    elif date_15ph < datetime.now() and datetime.now() < date_2h:
                        s.status_date_open = 'warning'
                    elif date_2h < datetime.now():
                        s.status_date_open = 'overdue'
            else:
                s.status_date_open = False

    def _compute_is_exist(self):
        for s in self:
            if s.phone:
                lead_exist_ids = self.env['crm.lead'].sudo().search(
                    [('active', '=', True), ('phone', '=', s.phone), ('id', '!=', s.id)])
                if lead_exist_ids:
                    s.is_exist = True
                else:
                    s.is_exist = False
            else:
                s.is_exist = False


    @api.onchange('phone')
    def onchange_check_exist(self):
        if self.phone:
            lead_exist_ids = self.env['crm.lead'].sudo().search(
                [('phone', '=', self.phone), ('id', '!=', self.env.context.get('active_ids'))])
            if lead_exist_ids:
                for lead_exist_id in lead_exist_ids:
                    if lead_exist_id.id != self.env.context.get('active_ids'):
                        self.lead_exist_ids.create({
                            'lead_id': self.id,
                            'lead_exist_id': lead_exist_id.id,
                        })
            else:
                self.lead_exist_ids.unlink()
            partner_ids = self.env['res.partner'].sudo().search(
                [('phone', '=', self.phone)], limit=1)
            if partner_ids:
                for partner_id in partner_ids:
                    self.partner_id = partner_id

    def dpt_crm_lead_log_note_action_new(self):
        view_id = self.env.ref('dpt_custom_lead.dpt_crm_lead_log_note_form_view').id
        ctx = dict(
            default_lead_id=self.id,
            default_stage_id=self.stage_id.id,
        )
        return {
            'name': _('Ghi chú'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'crm.lead.log.note',
            'view_id': view_id,
            'target': 'new',
            'context': ctx,
            'flags': {'form': {'action_buttons': True, 'options': {'mode': 'edit'}}}
        }


    def write(self, vals):
        for lead_id in self:
            stage_id_old = lead_id.stage_id.id
            user_old_id = lead_id.user_id
            stage_old = lead_id.stage_id
            res = super(CRMLEAD, self).write(vals)
            stage_id_new = lead_id.stage_id.id
            stage_new = lead_id.stage_id
            user_new_id = lead_id.user_id
            if stage_id_old != stage_id_new and stage_old.sequence < stage_new.sequence:
                note = lead_id.check_lead_log_note_action(lead_id, stage_old)
                if not note:
                    raise UserError("Bạn vui lòng cập nhật ghi chú trước khi chuyển trạng thái")
            if user_old_id != user_new_id:
                lead_id.partner_id.user_id = user_new_id
            return res

    def check_lead_log_note_action(self, lead_id, stage_id):
        note = self.env['crm.lead.log.note'].search([('lead_id', '=', lead_id.id), ('stage_id', '=', stage_id.id)])
        return note

class CRMLEADexist(models.Model):
    _name = 'crm.lead.exist'

    lead_id = fields.Many2one('crm.lead', string='Lead')
    lead_exist_id = fields.Many2one('crm.lead', string='Lead exist')
    stage_id = fields.Many2one('crm.stage', string='Stage', related="lead_exist_id.stage_id")
    user_id = fields.Many2one('res.users', string='User', related="lead_exist_id.user_id")
    team_id = fields.Many2one('crm.team', string='Team', related="lead_exist_id.team_id")

class RESPARTNER(models.Model):
    _inherit = 'res.partner'

    def name_get(self):
        res = []
        for partner in self:
            phone = partner.phone and partner.phone or ''
            name = partner.name and partner.name or ''
            res.append((partner.id, f"{phone}-{name}"))
        return res

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=10):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('phone', operator, name), ('name', operator, name)]
        partner = self.search(domain + args, limit=limit)
        return partner.name_get()


class CRMLEADLOGNOTE(models.Model):
    _name = 'crm.lead.log.note'

    lead_id = fields.Many2one('crm.lead', string='Lead')
    stage_id = fields.Many2one('crm.stage', string="State")
    note = fields.Char('Ghi chú')
    content = fields.Selection([('pre_sale', 'Pre Sale'), ('after_sale', 'After Sale')],
                               string="Content",
                               default='pre_sale')
    contact_form = fields.Selection(
        [('video', 'Video Call'),
         ('tele_sale', 'Tele sale'),
         ('chat', 'Chat'),
         ('meeting', 'Meeting'),
         ('survey', 'Survey'),
         ('other', 'Other')],
        string="Contact form",
        default='tele_sale')
    result = fields.Selection(
        [('interacted', 'Interacted'),
         ('no_answer', 'No answer'),
         ('call_back', 'Call back'),
         ('cancel_meeting', 'Cancel meeting'),
         ('send_survey', 'Send survey'),
         ('answer_survey', 'Answer survey'),
         ('other', 'Other')],
        string="Result",
        default='interacted')

    @api.model
    def create(self, vals):
        note = super(CRMLEADLOGNOTE, self).create(vals)
        content = ''
        if note.content == 'pre_sale':
            content = 'Tư vấn trước bán'
        elif note.content == 'after_sale':
            content = 'Chăm sóc sau bán'

        contact_form = ''
        if note.contact_form == 'video':
            contact_form = 'Video Call'
        elif note.contact_form == 'tele_sale':
            contact_form = 'Tele sale'
        elif note.contact_form == 'chat':
            contact_form = 'Chat'
        elif note.contact_form == 'meeting':
            contact_form = 'Gặp mặt'
        elif note.contact_form == 'other':
            contact_form = 'Khác'

        result = ''
        if note.result == 'interacted':
            result = 'Đã tương tác'
        elif note.result == 'no_answer':
            result = 'Không trả lời'
        elif note.result == 'call_back':
            result = 'Gọi lại sau'
        elif note.result == 'cancel_meeting':
            result = 'Hủy gặp'
        elif note.result == 'other':
            result = 'Khác'

        chatter_message = _('''<b> Nội dung liên hệ: </b> %s <br/>
                               <b> Hình thức liên hệ: </b> %s <br/>
                               <b> Kết quả: </b> %s <br/>
                               <b> Ghi chú: </b> %s <br/>
                               <b> Trạng thái Note: </b> %s <br/>
                                       
                                     ''') % (
            content,
            contact_form,
            result,
            note.note,
            note.stage_id.name,
        )

        note.lead_id.message_post(body=chatter_message)

        return note

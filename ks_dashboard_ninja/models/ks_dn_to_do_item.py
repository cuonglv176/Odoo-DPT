import json
from odoo import models, fields, api, _
import copy
import re
from odoo.exceptions import ValidationError, UserError

class KsDashboardNinjaItems(models.Model):
    _inherit = 'ks_dashboard_ninja.item'

    ks_to_do_preview = fields.Char("To Do Preview", default="To Do Preview")
    ks_dn_header_lines = fields.One2many('ks_to.do.headers', 'ks_dn_item_id')
    ks_to_do_data = fields.Char(string="To Do Data in JSon", compute='ks_get_to_do_view_data', compute_sudo=False)
    ks_header_bg_color = fields.Char(string="Header Background Color", default="#8e24aa,0.99",
                                     help=' Select the background color with transparency. ')

    @api.depends('ks_dn_header_lines', 'ks_dashboard_item_type')
    def ks_get_to_do_view_data(self):
        for rec in self:
            ks_to_do_data = rec._ksGetToDOData()
            rec.ks_to_do_data = ks_to_do_data

    def _ksGetToDOData(self):
        ks_to_do_data = {
            'label': [],
            'ks_link': [],
            'ks_href_id': [],
            'ks_section_id': [],
            'ks_content': {},
            'ks_content_record_id': {},
            'ks_content_active': {}
        }

        if self.ks_dn_header_lines:
            for ks_dn_header_line in self.ks_dn_header_lines:
                ks_to_do_header_label = ks_dn_header_line.ks_to_do_header[:]
                ks_to_do_data['label'].append(ks_to_do_header_label)
                ks_dn_header_line_id = str(ks_dn_header_line.id)
                if type(ks_dn_header_line.id).__name__ != 'int' and ks_dn_header_line.id.ref != None:
                    ks_dn_header_line_id = ks_dn_header_line.id.ref
                if ' ' in  ks_dn_header_line.ks_to_do_header:
                    ks_temp = ks_dn_header_line.ks_to_do_header.replace(" ", "")
                    ks_to_do_data['ks_link'].append('#' + ks_temp + ks_dn_header_line_id)
                    ks_to_do_data['ks_href_id'].append(ks_temp + str(ks_dn_header_line.id))

                elif ks_dn_header_line.ks_to_do_header[0].isdigit():
                    ks_temp = ks_dn_header_line.ks_to_do_header.replace(
                        ks_dn_header_line.ks_to_do_header[0], 'z')
                    ks_to_do_data['ks_link'].append('#' + ks_temp + ks_dn_header_line_id)
                    ks_to_do_data['ks_href_id'].append(ks_temp + str(ks_dn_header_line.id))
                else:
                    ks_to_do_data['ks_link'].append('#' + ks_dn_header_line.ks_to_do_header + ks_dn_header_line_id)
                    ks_to_do_data['ks_href_id'].append(ks_dn_header_line.ks_to_do_header + str(ks_dn_header_line.id))
                ks_to_do_data['ks_section_id'].append(str(ks_dn_header_line.id))
                if len(ks_dn_header_line.ks_to_do_description_lines):
                    for ks_to_do_description_line in ks_dn_header_line.ks_to_do_description_lines:
                        if ' ' in ks_dn_header_line.ks_to_do_header or ks_dn_header_line.ks_to_do_header[0].isdigit():
                            if ks_to_do_data['ks_content'].get(ks_temp +
                                                               str(ks_dn_header_line.id), False):

                                ks_to_do_data['ks_content'][ks_temp +
                                                            str(ks_dn_header_line.id)].append(
                                    ks_to_do_description_line.ks_description)
                                ks_to_do_data['ks_content_record_id'][ks_temp +
                                                                      str(ks_dn_header_line.id)].append(
                                    str(ks_to_do_description_line.id))
                                ks_to_do_data['ks_content_active'][ks_temp +
                                                                   str(ks_dn_header_line.id)].append(
                                    str(ks_to_do_description_line.ks_active))
                            else:
                                ks_to_do_data['ks_content'][ks_temp +
                                                            str(ks_dn_header_line.id)] = [
                                    ks_to_do_description_line.ks_description]
                                ks_to_do_data['ks_content_record_id'][ks_temp +
                                                                      str(ks_dn_header_line.id)] = [
                                    str(ks_to_do_description_line.id)]
                                ks_to_do_data['ks_content_active'][ks_temp +
                                                                   str(ks_dn_header_line.id)] = [
                                    str(ks_to_do_description_line.ks_active)]
                        else:
                            if ks_to_do_data['ks_content'].get(ks_dn_header_line.ks_to_do_header +
                                                               str(ks_dn_header_line.id), False):

                                ks_to_do_data['ks_content'][ks_dn_header_line.ks_to_do_header +
                                                            str(ks_dn_header_line.id)].append(
                                    ks_to_do_description_line.ks_description)
                                ks_to_do_data['ks_content_record_id'][ks_dn_header_line.ks_to_do_header +
                                                                      str(ks_dn_header_line.id)].append(
                                    str(ks_to_do_description_line.id))
                                ks_to_do_data['ks_content_active'][ks_dn_header_line.ks_to_do_header +
                                                                   str(ks_dn_header_line.id)].append(
                                    str(ks_to_do_description_line.ks_active))
                            else:
                                ks_to_do_data['ks_content'][ks_dn_header_line.ks_to_do_header +
                                                            str(ks_dn_header_line.id)] = [
                                    ks_to_do_description_line.ks_description]
                                ks_to_do_data['ks_content_record_id'][ks_dn_header_line.ks_to_do_header +
                                                                      str(ks_dn_header_line.id)] = [
                                    str(ks_to_do_description_line.id)]
                                ks_to_do_data['ks_content_active'][ks_dn_header_line.ks_to_do_header +
                                                                   str(ks_dn_header_line.id)] = [
                                    str(ks_to_do_description_line.ks_active)]

            ks_to_do_data = json.dumps(ks_to_do_data)
        else:
            ks_to_do_data = False
        return ks_to_do_data




class KsToDoheaders(models.Model):
    _name = 'ks_to.do.headers'
    _description = "to do headers"

    ks_dn_item_id = fields.Many2one('ks_dashboard_ninja.item')
    ks_to_do_header = fields.Char('Header')
    ks_to_do_description_lines = fields.One2many('ks_to.do.description', 'ks_to_do_header_id')

    @api.constrains('ks_to_do_header')
    def ks_to_do_header_check(self):
        for rec in self:
            if rec.ks_to_do_header:
                ks_check = bool(re.match('^[A-Z, a-z,0-9,_]+$', rec.ks_to_do_header))
                if not ks_check:
                    raise ValidationError(_("Special characters are not allowed only string and digits allow for section header"))

    @api.onchange('ks_to_do_header')
    def ks_to_do_header_onchange(self):
        for rec in self:
            if rec.ks_to_do_header:
                ks_check = bool(re.match('^[A-Z, a-z,0-9,_]+$', rec.ks_to_do_header))
                if not ks_check:
                    raise ValidationError(_("Special characters are not allowed only string and digits allow for section header"))

class KsToDODescription(models.Model):
    _name = 'ks_to.do.description'
    _description = 'to do description'

    ks_to_do_header_id = fields.Many2one('ks_to.do.headers')
    ks_description = fields.Text('Description')
    ks_active = fields.Boolean('Active Description', default=True)

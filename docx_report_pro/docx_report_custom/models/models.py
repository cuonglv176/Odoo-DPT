# -*- coding: utf-8 -*-
# Copyright 2019-2021 Artem Shurshilov
# Odoo Proprietary License v1.0

# This software and associated files (the "Software") may only be used (executed,
# modified, executed after modifications) if you have purchased a valid license
# from the authors, typically via Odoo Apps, or if you have received a written
# agreement from the authors of the Software (see the COPYRIGHT file).

# You may develop Odoo modules that use the Software as a library (typically
# by depending on it, importing it and using its resources), but without copying
# any source code or material from the Software. You may distribute those
# modules under the license of your choice, provided that this license is
# compatible with the terms of the Odoo Proprietary License (For example:
# LGPL, MIT, or proprietary licenses similar to this one).

# It is forbidden to publish, distribute, sublicense, or sell copies of the Software
# or modified copies of the Software.

# The above copyright notice and this permission notice must be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

from odoo import models, fields, api, exceptions, _
from odoo.exceptions import AccessError, UserError, AccessDenied
import html2text


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def report_prepare(self):
        h = html2text.HTML2Text()
        record_fields = {
            'customer_name': self.partner_id.name,
            'customer_street': self.partner_id.street,
            'customer_country': self.partner_id.country_id.name,
            'customer_zip': self.partner_id.zip,
            'customer_city': self.partner_id.city,
            'sh_html_notes': h.handle(self.sh_html_notes),
            'date_order': self.date_order.strftime('%d/%m/%Y') if self.date_order else '',
            'validity_date': self.validity_date.strftime('%d/%m/%Y') if self.validity_date else '',
            'order_lines': self.order_line.read(),
        }
        return record_fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    def report_prepare(self):
        timesheet_total = 0
        for i in self.sudo().timesheet_ids:
            timesheet_total+= i.unit_amount
        record_fields = {
            'customer_name': self.partner_id.name,
            'customer_street': self.partner_id.street,
            'customer_country': self.partner_id.country_id.name,
            'customer_zip': self.partner_id.zip,
            'customer_city': self.partner_id.city,
            'vat': self.partner_id.vat,
            'invoice_date': self.invoice_date.strftime('%d/%m/%Y') if self.invoice_date else '',
            # sequence, date desc, move_name desc, id
            'order_lines': self.sudo().invoice_line_ids.sorted(lambda m: (m.sequence,m.date,m.move_name,m.id)).read(),
            'timesheet_ids': self.sudo().timesheet_ids.read(),
            'timesheet_total': timesheet_total
        }
        return record_fields

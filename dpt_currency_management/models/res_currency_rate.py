# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _, exceptions
import pytz
from datetime import datetime


class ResCurrencyRate(models.Model):
    _name = 'res.currency.rate'
    _inherit = ['res.currency.rate', 'mail.thread', 'mail.activity.mixin']
    _description = 'Currency Rate'

    name = fields.Date(tracking=True) 
    rate = fields.Float(tracking=True)
    company_id = fields.Many2one(tracking=True)
    currency_id = fields.Many2one(tracking=True)
    write_date = fields.Datetime(tracking=True) 
    
    def write(self, vals):
        """Override write method to allow updates only for records with name=today in UTC+7"""
        for record in self:
            # Get today's date in UTC+7 timezone
            vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')  # UTC+7 timezone
            today_utc7 = datetime.now(vietnam_tz).date()
            
            # Check if the record's date is today
            if record.name != today_utc7:
                raise exceptions.UserError(_("You can only update currency rates for today's date (UTC+7)."))
                
        return super(ResCurrencyRate, self).write(vals) 
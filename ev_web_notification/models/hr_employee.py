# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import re

from binascii import Error as binascii_error
from collections import defaultdict
from operator import itemgetter
from odoo.http import request
from datetime import datetime

from odoo import _, api, fields, models, modules, tools
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools import groupby

_logger = logging.getLogger(__name__)
_image_dataurl = re.compile(r'(data:image/[a-z]+?);base64,([a-z0-9+/\n]{3,}=*)\n*([\'"])(?: data-filename="([^"]*)")?',
                            re.I)


class Employee(models.Model):
    _inherit = 'hr.employee'

    def write(self, values):
        res = super(Employee, self).write(values)
        res_id = self.env['mail.message']._push_system_notification(self.env.user.partner_id.id,
                                                                    [3], self.name,
                                                                    'hr.employee', self.id)
        print(res_id)
        return res

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from datetime import datetime


def year_to_alphabet(year):
    # Define the base year
    base_year = 2024
    # Calculate the offset from the base year
    offset = year - base_year
    # Calculate the corresponding alphabet character
    alphabet = chr(ord('A') + offset)
    return alphabet


def next_alphabet(letter):
    # Convert to uppercase to handle both cases uniformly
    letter = letter.upper()
    return chr(ord(letter) + 1)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    sale_id = fields.Many2one('sale.order', 'Sale')
    package_line_ids = fields.One2many('purchase.order.line.package', 'purchase_id', 'Package Line')
    import_package_stock = fields.Boolean('Import Package to Stock')
    purchase_type = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External'),
        ('buy_cny', 'Mua tệ'),
    ], string='Purchase type', default='external', tracking=True)
    packing_lot_name = fields.Char('Packing Lot name', compute="compute_packing_lot_name", store=True)
    department_id = fields.Many2one('hr.department', string='Phòng ban')
    origin_po = fields.Many2one('sale.order')
    count_buy_cny_po = fields.Integer(compute='_compute_count_buy_cny_po')
    last_rate_currency = fields.Float('Rate Currency')
    purchase_service_ids = fields.One2many('dpt.purchase.service.management', 'purchase_id', 'Service Line')

    @api.onchange('department_id')
    def onchange_department_id(self):
        if not self.department_id:
            self.department_id = self.user.employee_id.department_id

    def _compute_count_buy_cny_po(self):
        for r in self:
            r.count_buy_cny_po = self.search_count([('purchase_type', '=', 'buy_cny'), ('origin_po', '=', r.id)])

    def get_origin_po(self):
        return {
            'name': "Purchase Order",
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'target': 'self',
            'views': [(False, 'list'), (False, 'form')],
            'domain': [('origin_po', '=', self.id)],
            'context': "{'create': False}"
        }

    @api.depends('package_line_ids.quantity', 'package_line_ids.uom_id.packing_code')
    def compute_packing_lot_name(self):
        for item in self:
            item.packing_lot_name = '.'.join(
                [f"{package_line_id.quantity}{package_line_id.uom_id.packing_code}" for package_line_id in
                 item.package_line_ids if package_line_id.uom_id.packing_code])

    @api.model
    def create(self, vals):
        res = super().create(vals)
        res.create_buy_cny_purchase_order()
        if not self.env.context.get('create_from_so', False):
            return res
        # create ticket and auto mark done ticket
        res.create_helpdesk_ticket()
        return res

    def create_buy_cny_purchase_order(self):
        self.ensure_one()
        if self.purchase_type == 'buy_cny':
            return True
        vals = {
            'purchase_type': 'buy_cny',
            'department_id': self.department_id.id,
            'partner_id': self.partner_id.id,
            'origin_po': self.id,
        }
        res = self.create(vals)
        return res

    def create_helpdesk_ticket(self):
        helpdesk_vals = self.get_helpdesk_vals()
        if helpdesk_vals:
            self.env['helpdesk.ticket'].sudo().create(helpdesk_vals)

    def get_helpdesk_vals(self):
        sale_service_ids = self.sale_id.sale_service_ids.filtered(lambda s: s.service_id.is_purchase_service)
        if not sale_service_ids:
            return {}
        department_id = sale_service_ids.filtered(
            lambda s: s.department_id).department_id.id if sale_service_ids.filtered(
            lambda s: s.department_id) else None
        service_lines_ids = []
        for sale_service_id in sale_service_ids:
            service_lines_ids.append((0, 0, {
                'service_id': sale_service_id.service_id.id,
                'qty': sale_service_id.qty,
                'uom_id': sale_service_id.uom_id.id if sale_service_id.uom_id else None,
                'price': sale_service_id.price
            }))
        helpdesk_stage_id = self.env['helpdesk.stage'].search([('is_done_stage', '=', True)], limit=1)
        if not helpdesk_stage_id:
            raise ValidationError(_('Please config 1 helpdesk stage is finish stage!!'))
        return {
            'sale_id': self.sale_id.id if self.sale_id else None,
            'purchase_id': self.id,
            'partner_id': self.sale_id.partner_id.id if self.sale_id else None,
            'department_id': department_id,
            'service_lines_ids': service_lines_ids,
            'stage_id': helpdesk_stage_id.id,
        }

    @api.constrains('package_line_ids')
    def _constrains_package_line(self):
        for item in self:
            if not item.sale_id:
                continue
            purchase_ids = item.sale_id.purchase_ids
            packing_num = sum(purchase_ids.package_line_ids.mapped('quantity'))
            all_num_packing_field_ids = item.sale_id.fields_ids.filtered(
                lambda f: f.fields_id.default_compute_from == 'packing_num_in_po')
            all_num_packing_field_ids.write({
                'value_integer': packing_num
            })

    def write(self, vals):
        res = super(PurchaseOrder, self).write(vals)
        if vals.get('state'):
            self.update_last_rate_currency()

    def update_last_rate_currency(self):
        self.ensure_one()
        if self.state == 'purchase' and self.currency_id:
            self.last_rate_currency = self.currency_id.rate

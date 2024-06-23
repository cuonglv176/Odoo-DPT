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
        ('external', 'External')
    ], string='Purchase type', default='external', tracking=True)
    packing_lot_name = fields.Char('Packing Lot name', compute="compute_packing_lot_name", store=True)
    last_packing_lot_alphabet = fields.Char('Last Packing Lot alphabet', compute="compute_packing_lot_name", store=True)

    @api.depends('package_line_ids.quantity', 'package_line_ids.uom_id.packing_code')
    def compute_packing_lot_name(self):
        for item in self:
            now = datetime.now()
            prefix = f'D{year_to_alphabet(now.year)}{now.strftime("%m%d")}'
            main_name = '+'.join(
                [f'{line.quantity}{line.uom_id.packing_code if line.uom_id.packing_code else ""}' for line in
                 item.package_line_ids])
            if main_name:
                full_name = f'{prefix}-{main_name}'
                # other purchase have same full name
                domain = [('packing_lot_name', 'ilike', full_name),
                          ('id', '!=', item._origin.id)] if item._origin.id else [
                    ('packing_lot_name', 'ilike', full_name)]
                exist_po_id = self.env['purchase.order'].search(domain, order="id desc", limit=1)
                if not exist_po_id:
                    item.packing_lot_name = full_name
                    item.last_packing_lot_alphabet = ''
                else:
                    if not exist_po_id.last_packing_lot_alphabet:
                        exist_po_id.last_packing_lot_alphabet = 'A'
                        exist_po_id.packing_lot_name = exist_po_id.packing_lot_name + '-A'
                    item.packing_lot_name = f'{full_name}-{next_alphabet(exist_po_id.last_packing_lot_alphabet)}'
                    item.last_packing_lot_alphabet = next_alphabet(exist_po_id.last_packing_lot_alphabet)
            else:
                item.packing_lot_name = None
                item.last_packing_lot_alphabet = ''

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if not self.env.context.get('create_from_so', False):
            return res
        # create ticket and auto mark done ticket
        res.create_helpdesk_ticket()
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

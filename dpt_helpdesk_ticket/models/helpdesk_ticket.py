from odoo import models, fields, api, _


class HelpdeskTicket(models.Model):

    _inherit = 'helpdesk.ticket'

    name = fields.Char(default='PDV')
    type_service = fields.Selection([('sale_order', 'Sale Order'),
                                     ('stock', 'Stock'),
                                     ('import_export', 'Import Export')], string='Loại ticket')
    service_lines_ids = fields.One2many('dpt.helpdesk.servie.line', 'parent_id', string='Service')
    purchase_id = fields.Many2one('purchase.order', string='Purchase Order')
    purchase_status = fields.Selection(related='purchase_id.state', string='Purchase Status')
    department_id = fields.Many2one('hr.department', string='Department')
    lot_name = fields.Char(string='Mã Lô', readonly=True)
    service_ids = fields.Many2many('dpt.service.management', compute='_compute_service_ids', store=True)
    pack_name = fields.Char(string='Mã pack', compute='_compute_pack_name', store=True)
    sale_id = fields.Many2one('sale.order', string='Đơn bán hàng')
    user_sale_id = fields.Many2one('res.users', string='Nhân viên kinh doanh', related='sale_id.user_id', store=True)

    def action_view_sale_order(self):
        if not self.sale_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Cảnh báo',
                    'type': 'warning',
                    'message': 'Không tìm thấy đơn hàng',
                    'sticky': True,
                }
            }
        sale_id = self.sale_id
        view_id = self.env.ref('sale.view_order_form').id
        action = self.env['ir.actions.actions']._for_xml_id('sale.action_orders')
        action.update({
            'view_mode': 'form',
            'views': [[view_id, 'form']],
            'target': 'main',
            'res_id': sale_id.id,
        })
        return action

    def action_view_purchase_order(self):
        if not self.purchase_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Cảnh báo',
                    'type': 'warning',
                    'message': 'Không tìm thấy đơn mua hàng',
                    'sticky': True,
                }
            }
        purchase_id = self.purchase_id
        result = self.env['ir.actions.act_window']._for_xml_id('purchase.purchase_form_action')
        view_id = self.env.ref('purchase.purchase_order_form').id
        result.update({
            'view_mode': 'form',
            'views': [[view_id, 'form']],
            'target': 'main',
            'res_id': purchase_id.id,
        })
        return result

    def action_view_stock_picking_order(self):
        view_id = self.env.ref('stock.vpicktree').id
        view_form_id = self.env.ref('stock.view_picking_form').id
        stock_picking_ids = self.env['stock.picking'].search([
            '|',
            '|',
            ('sale_id', '=', self.sale_id.id),
            ('sale_purchase_id', '=', self.sale_id.id),
            ('origin', '=', self.sale_id.name),
        ])
        if not stock_picking_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Cảnh báo',
                    'type': 'warning',
                    'message': 'Không tìm thấy phiếu kho',
                    'sticky': True,
                }
            }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'name': 'Phiếu kho',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', stock_picking_ids.ids)],
            'views': [[view_id, 'tree'], [view_form_id, 'form']],
        }

    def action_view_approval_request(self):
        if not self.sale_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Cảnh báo',
                    'type': 'warning',
                    'message': 'Không tìm thấy đơn hàng',
                    'sticky': True,
                }
            }
        sale_id = self.sale_id
        view_id = self.env.ref('approvals.approval_request_view_kanban').id
        view_tree_id = self.env.ref('approvals.approval_request_view_tree').id
        view_form_id = self.env.ref('approvals.approval_request_view_form').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'approval.request',
            'name': 'Phê duyệt',
            'view_mode': 'kanban,tree,form',
            'domain': [('sale_id', '=', sale_id.id)],
            'views': [[view_id, 'kanban'], [view_tree_id, 'tree'], [view_form_id, 'form']],
        }


    def action_view_contract(self):
        if not self.purchase_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Cảnh báo',
                    'type': 'warning',
                    'message': 'Không tìm thấy đơn mua hàng',
                    'sticky': True,
                }
            }
        purchase_id = self.purchase_id
        if not purchase_id.contract_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Cảnh báo',
                    'type': 'warning',
                    'message': 'Không tìm thấy hợp đồng',
                    'sticky': True,
                }
            }
        contract_id = purchase_id.contract_id
        return {
            'name': "Hợp đồng",
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.contract.management',
            'res_id': contract_id.id,
            'target': 'self',
            'view_mode': 'form',
            'view_id': self.env.ref('dpt_contract_management.view_service_form').id,
        }


    @api.onchange('sale_id')
    def _onchange_sale_id(self):
        if not self.sale_id:
            return False
        sale_id = self.sale_id
        self.service_lines_ids = [
            (0, 0, {
                'sequence': line.sequence,
                'currency_id': line.currency_id.id,
                'service_id': line.service_id.id,
                'description': line.description,
                'qty': line.qty,
                'uom_id': line.uom_id.id,
                'price': line.price,
                'amount_total': line.amount_total,
                'department_id': line.department_id.id,
            })
        for line in sale_id.sale_service_ids]


    @api.depends(
        'purchase_id',
        'sale_id',
    )
    def _compute_pack_name(self):
        for rec in self:
            if not rec.sale_id:
                rec.pack_name = False
                continue
            picking_id = self.env['stock.picking'].search([
                ('origin', '=', rec.sale_id.name),
            ])
            if not picking_id or not picking_id.mapped('packing_lot_name'):
                rec.pack_name = False
                continue
            rec.pack_name = ','.join(picking_id.mapped('packing_lot_name'))


    @api.depends(
        'service_lines_ids',
        'service_lines_ids.service_id'
    )
    def _compute_service_ids(self):
        for rec in self:
            if not rec.service_lines_ids:
                rec.service_ids = [(6, 0, [])]
                continue
            rec.service_ids = [(6, 0, rec.service_lines_ids.mapped('service_id.id'))]

    @api.model
    def create(self, vals):
        res = super(HelpdeskTicket, self).create(vals)
        res.name = self._generate_service_code()
        return res

    @api.onchange('purchase_id')
    def _onchange_purchase_id(self):
        for rec in self:
            rec.lot_name = rec.purchase_id.packing_lot_name

    def _generate_service_code(self):
        sequence = self.env['ir.sequence'].next_by_code('helpdesk.ticket') or '00'
        return f'{sequence}'

    def action_create_po(self):
        pass


class DPTSaleChangePriceServiceLine(models.Model):
    _name = 'dpt.helpdesk.servie.line'

    sequence = fields.Integer()
    parent_id = fields.Many2one('helpdesk.ticket')
    service_id = fields.Many2one('dpt.service.management', string='Service')
    description = fields.Char(string='Description')
    qty = fields.Float(string='QTY')
    uom_id = fields.Many2one('uom.uom')
    price = fields.Monetary(currency_field='currency_id', string='Price')
    currency_id = fields.Many2one('res.currency', string='Currency')
    amount_total = fields.Float(string="Amount Total")
    status = fields.Char(string='Status')
    department_id = fields.Many2one('hr.department', related='parent_id.department_id')




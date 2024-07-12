from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    count_ticket = fields.Integer(compute='_compute_count_ticket')
    ticket_ids = fields.One2many('helpdesk.ticket', 'sale_id', 'Tickets')

    def write(self, vals):
        ret = super(SaleOrder, self).write(vals)
        if 'sale_service_ids' not in vals:
            return ret
        for value in vals['sale_service_ids']:
            if value[0] != 0:
                continue
            val_create = value[2]
            service_id = self.env['dpt.service.management'].browse(val_create['service_id'])
            ticket_id = self.env['helpdesk.ticket'].create({
                'sale_id': self.id,
                'partner_id': self.partner_id.id,
                'department_id': service_id.department_id.id,
                'team_id': service_id.helpdesk_team_id.id,
            })
            print(val_create)
            self.env['dpt.helpdesk.servie.line'].create({
                'service_id': val_create.get('service_id'),
                'description': val_create.get('description'),
                'qty': val_create.get('qty'),
                'uom_id': val_create.get('uom_id'),
                'price': val_create.get('price'),
                'currency_id': val_create.get('currency_id'),
                'amount_total': val_create.get('amount_total'),
                'parent_id': ticket_id.id
                # 'status': r.price_status,
            })
        return ret

    def get_tickets(self):
        return {
            'name': "Service Ticket",
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'target': 'self',
            'views': [[False, 'tree'], [False, 'form']],
            'domain': [('sale_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def _compute_count_ticket(self):
        for record in self:
            record.count_ticket = self.env['helpdesk.ticket'].search_count([('sale_id', '=', record.id)])

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        self.action_create_ticket()
        return res

    def action_create_ticket(self):
        list_department = []
        # for r in self.sale_service_ids:
        #     if r.department_id:
        #         list_department.append(r.department_id.id)
        # for department in list_department:
        for service in self.sale_service_ids:
            service_ids = []
            # if department == service.department_id.id:
            service_ids.append((0, 0, {
                'service_id': service.service_id.id,
                'description': service.description,
                'qty': service.qty,
                'uom_id': service.uom_id.id,
                'price': service.price,
                'currency_id': service.currency_id.id,
                'amount_total': service.amount_total,
                # 'status': r.price_status,
            }))
            stage_done_id = self.env['helpdesk.stage'].search(
                [('is_done_stage', '=', True), ('team_ids', 'in', [service.service_id.helpdesk_team_id.id])])
            if service.service_id.auo_complete:
                self.env['helpdesk.ticket'].create({
                    'sale_id': self.id,
                    'partner_id': self.partner_id.id,
                    'service_lines_ids': service_ids,
                    'department_id': service.department_id.id,
                    'team_id': service.service_id.helpdesk_team_id.id,
                    'stage_id': stage_done_id.id,
                })
            else:
                self.env['helpdesk.ticket'].create({
                    'sale_id': self.id,
                    'partner_id': self.partner_id.id,
                    'service_lines_ids': service_ids,
                    'department_id': service.department_id.id,
                    'team_id': service.service_id.helpdesk_team_id.id,
                })

            # team_id = self.env['helpdesk.team'].search([('service_type_ids', 'in', [service.service_type_id.id])],
            #                                            limit=1)
            # if team_id:
            #     self.env['helpdesk.ticket'].create({
            #         'sale_id': self.id,
            #         'partner_id': self.partner_id.id,
            #         'service_lines_ids': service_ids,
            #         'department_id': department,
            #         'team_id': team_id,
            #     })
            # else:
            #     self.env['helpdesk.ticket'].create({
            #         'sale_id': self.id,
            #         'partner_id': self.partner_id.id,
            #         'service_lines_ids': service_ids,
            #         'department_id': department,
            #     })
        # return {
        #     'name': "Service Ticket",
        #     'type': 'ir.actions.act_window',
        #     'res_model': 'helpdesk.ticket',
        #     'target': 'self',
        #     'views': [[False, 'form']],
        #     'context': {
        #         'default_sale_id': self.id,
        #         'default_partner_id': self.partner_id.id,
        #         'default_service_lines_ids': service_ids,
        #         'default_department_id': department,
        #     },
        # }

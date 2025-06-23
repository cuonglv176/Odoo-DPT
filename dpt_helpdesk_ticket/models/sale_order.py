from odoo import models, fields, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    count_ticket = fields.Integer(compute='_compute_count_ticket')
    ticket_ids = fields.One2many('helpdesk.ticket', 'sale_id', 'Tickets')

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        self.action_create_ticket_first()
        return res

    def write(self, vals):
        rec = super(SaleOrder, self).write(vals)
        if 'sale_service_ids' not in vals:
            return rec
        if self.state == 'sale':
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
                sale_service_id = self.sale_service_ids.search(
                    [('service_id', '=', service_id.id), ('sale_id', '=', self.id)], limit=1)
                self.env['dpt.helpdesk.servie.line'].create({
                    'sale_service_id': sale_service_id.id,
                    'service_id': val_create.get('service_id'),
                    'description': val_create.get('description'),
                    'qty': val_create.get('compute_value'),
                    'uom_id': val_create.get('uom_id'),
                    'price': val_create.get('price'),
                    'currency_id': val_create.get('currency_id'),
                    'amount_total': val_create.get('amount_total'),
                    'parent_id': ticket_id.id
                    # 'status': r.price_status,
                })
        self.action_create_ticket_first()
        return rec

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
        self.action_create_ticket()
        res = super(SaleOrder, self).action_confirm()
        return res

    def action_create_ticket_first(self):
        for service in self.planned_sale_service_ids:
            if service.is_create_ticket_first:
                # Kiểm tra nếu dịch vụ đã có ticket thì bỏ qua
                if service.ticket_id:
                    continue

                # Kiểm tra nếu dịch vụ chưa được xác nhận tạo ticket thì bỏ qua
                # trừ khi dịch vụ có is_create_ticket hoặc đơn hàng có confirm_service_ticket
                if not service.is_confirmed_for_ticket and not service.service_id.is_create_ticket and not self.confirm_service_ticket:
                    continue

                service_ids = []
                if service.service_id.is_tth_service and (service.service_id.is_create_ticket or self.confirm_service_ticket or service.is_confirmed_for_ticket):
                    vals = {
                        'purchase_type': 'buy_cny',
                        'department_id': service.department_id.id,
                        'partner_id': self.partner_id.id,
                        'sale_id': self.id,
                    }
                    res = self.env['purchase.order'].create(vals)
                    continue
                # if department == service.department_id.id:
                if service.service_id.is_create_ticket or self.confirm_service_ticket or service.is_confirmed_for_ticket:
                    service_ids.append((0, 0, {
                        'service_id': service.service_id.id,
                        'sale_service_id': service.id,
                        'description': service.description,
                        'qty': service.compute_value,
                        'uom_id': service.uom_id.id,
                        'price': service.price,
                        'currency_id': service.currency_id.id,
                        'amount_total': service.amount_total,
                        # 'status': r.price_status,
                    }))
                stage_done_id = self.env['helpdesk.stage'].search(
                    [('is_done_stage', '=', True), ('team_ids', 'in', [service.service_id.helpdesk_team_id.id])])
                if service.service_id.auo_complete and (service.service_id.is_create_ticket or self.confirm_service_ticket or service.is_confirmed_for_ticket):
                    ticket_id = self.env['helpdesk.ticket'].create({
                        'sale_id': self.id,
                        'partner_id': self.partner_id.id,
                        'service_lines_ids': service_ids,
                        'department_id': service.department_id.id,
                        'team_id': service.service_id.helpdesk_team_id.id,
                        'stage_id': stage_done_id.id,
                    })
                    service.ticket_id = ticket_id
                else:
                    if service.service_id.is_create_ticket or self.confirm_service_ticket or service.is_confirmed_for_ticket:
                        ticket_id = self.env['helpdesk.ticket'].create({
                            'sale_id': self.id,
                            'partner_id': self.partner_id.id,
                            'service_lines_ids': service_ids,
                            'department_id': service.department_id.id,
                            'team_id': service.service_id.helpdesk_team_id.id,
                        })
                        service.ticket_id = ticket_id
        for service in self.sale_service_ids:
            if service.is_create_ticket_first:
                # Kiểm tra nếu dịch vụ đã có ticket thì bỏ qua
                if service.ticket_id:
                    continue

                # Kiểm tra nếu dịch vụ chưa được xác nhận tạo ticket thì bỏ qua
                # trừ khi dịch vụ có is_create_ticket hoặc đơn hàng có confirm_service_ticket
                if not service.is_confirmed_for_ticket and not service.service_id.is_create_ticket and not self.confirm_service_ticket:
                    continue

                service_ids = []
                if service.service_id.is_tth_service and (service.service_id.is_create_ticket or self.confirm_service_ticket or service.is_confirmed_for_ticket):
                    vals = {
                        'purchase_type': 'buy_cny',
                        'department_id': service.department_id.id,
                        'partner_id': self.partner_id.id,
                        'sale_id': self.id,
                    }
                    res = self.env['purchase.order'].create(vals)
                    continue
                # if department == service.department_id.id:
                if service.service_id.is_create_ticket or self.confirm_service_ticket or service.is_confirmed_for_ticket:
                    service_ids.append((0, 0, {
                        'service_id': service.service_id.id,
                        'sale_service_id': service.id,
                        'description': service.description,
                        'qty': service.compute_value,
                        'uom_id': service.uom_id.id,
                        'price': service.price,
                        'currency_id': service.currency_id.id,
                        'amount_total': service.amount_total,
                        # 'status': r.price_status,
                    }))
                stage_done_id = self.env['helpdesk.stage'].search(
                    [('is_done_stage', '=', True), ('team_ids', 'in', [service.service_id.helpdesk_team_id.id])])
                if service.service_id.auo_complete and (service.service_id.is_create_ticket or self.confirm_service_ticket or service.is_confirmed_for_ticket):
                    ticket_id = self.env['helpdesk.ticket'].create({
                        'sale_id': self.id,
                        'partner_id': self.partner_id.id,
                        'service_lines_ids': service_ids,
                        'department_id': service.department_id.id,
                        'team_id': service.service_id.helpdesk_team_id.id,
                        'stage_id': stage_done_id.id,
                    })
                    service.ticket_id = ticket_id
                else:
                    if service.service_id.is_create_ticket or self.confirm_service_ticket or service.is_confirmed_for_ticket:
                        ticket_id = self.env['helpdesk.ticket'].create({
                            'sale_id': self.id,
                            'partner_id': self.partner_id.id,
                            'service_lines_ids': service_ids,
                            'department_id': service.department_id.id,
                            'team_id': service.service_id.helpdesk_team_id.id,
                        })
                        service.ticket_id = ticket_id
        for combo in self.service_combo_ids:
            for service_id in combo.service_ids:
                service_ids = []
                if service_id.is_create_ticket_first:
                    if service_id.is_create_ticket or self.confirm_service_ticket:
                        service_ids.append((0, 0, {
                            'service_id': service_id.id,
                            'sale_service_id': service.id,
                            'description': service.description,
                            'qty': service.compute_value,
                            'uom_id': service.uom_id.id,
                            'price': service.price,
                            'currency_id': service.currency_id.id,
                            'amount_total': service.amount_total,
                            # 'status': r.price_status,
                        }))
                    stage_done_id = self.env['helpdesk.stage'].search(
                        [('is_done_stage', '=', True), ('team_ids', 'in', [service_id.helpdesk_team_id.id])])
                    if service_id.auo_complete and (
                            service_id.is_create_ticket or self.confirm_service_ticket):
                        ticket_id = self.env['helpdesk.ticket'].create({
                            'sale_id': self.id,
                            'partner_id': self.partner_id.id,
                            'service_lines_ids': service_ids,
                            'department_id': service_id.department_id.id,
                            'team_id': service_id.helpdesk_team_id.id,
                            'stage_id': stage_done_id.id,
                        })
                    else:
                        if service_id.is_create_ticket or self.confirm_service_ticket:
                            ticket_id = self.env['helpdesk.ticket'].create({
                                'sale_id': self.id,
                                'partner_id': self.partner_id.id,
                                'service_lines_ids': service_ids,
                                'department_id': service_id.department_id.id,
                                'team_id': service_id.helpdesk_team_id.id,
                            })



    def action_create_ticket(self):
        list_department = []
        # for r in self.sale_service_ids:
        #     if r.department_id:
        #         list_department.append(r.department_id.id)
        # for department in list_department:
        for service in self.sale_service_ids:
            # Kiểm tra nếu dịch vụ đã có ticket thì bỏ qua
            if service.ticket_id:
                continue

            # Kiểm tra nếu dịch vụ chưa được xác nhận tạo ticket thì bỏ qua
            # trừ khi dịch vụ có is_create_ticket hoặc đơn hàng có confirm_service_ticket
            if not service.is_confirmed_for_ticket and not service.service_id.is_create_ticket and not self.confirm_service_ticket:
                continue

            service_ids = []
            if service.service_id.is_tth_service and (service.service_id.is_create_ticket or self.confirm_service_ticket or service.is_confirmed_for_ticket):
                vals = {
                    'purchase_type': 'buy_cny',
                    'department_id': service.department_id.id,
                    'partner_id': self.partner_id.id,
                    'sale_id': self.id,
                }
                res = self.env['purchase.order'].create(vals)
                continue
            # if department == service.department_id.id:
            if service.service_id.is_create_ticket or self.confirm_service_ticket or service.is_confirmed_for_ticket:
                service_ids.append((0, 0, {
                    'service_id': service.service_id.id,
                    'sale_service_id': service.id,
                    'description': service.description,
                    'qty': service.compute_value,
                    'uom_id': service.uom_id.id,
                    'price': service.price,
                    'currency_id': service.currency_id.id,
                    'amount_total': service.amount_total,
                    # 'status': r.price_status,
                }))
            stage_done_id = self.env['helpdesk.stage'].search(
                [('is_done_stage', '=', True), ('team_ids', 'in', [service.service_id.helpdesk_team_id.id])])
            if service.service_id.auo_complete and (service.service_id.is_create_ticket or self.confirm_service_ticket or service.is_confirmed_for_ticket):
                ticket_id = self.env['helpdesk.ticket'].create({
                    'sale_id': self.id,
                    'partner_id': self.partner_id.id,
                    'service_lines_ids': service_ids,
                    'department_id': service.department_id.id,
                    'team_id': service.service_id.helpdesk_team_id.id,
                    'stage_id': stage_done_id.id,
                })
                service.ticket_id = ticket_id
            else:
                if service.service_id.is_create_ticket or self.confirm_service_ticket or service.is_confirmed_for_ticket:
                    ticket_id = self.env['helpdesk.ticket'].create({
                        'sale_id': self.id,
                        'partner_id': self.partner_id.id,
                        'service_lines_ids': service_ids,
                        'department_id': service.department_id.id,
                        'team_id': service.service_id.helpdesk_team_id.id,
                    })
                    service.ticket_id = ticket_id

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

# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, exceptions, fields, models, modules
from datetime import timedelta as td


class Users(models.Model):
    _inherit = 'res.users'

    @api.model
    def ev_systray_get_activities(self):
        query = """
                    SELECT act.url_portal ,act.id as message_id,(select id from ir_model where model = act.model) as model_id, act.res_id as res_id, 
                    act.model as model, act.subject as subject, act.status as status, act.icon as icon, act.create_date as create_date
                    from mail_message as act
                    inner join mail_message_res_partner_rel as mmrpr on mmrpr.mail_message_id = act.id
                     where act.message_type = 'system_notification' and
                     mmrpr.res_partner_id = %(partner_id)s   
                     order by act.status desc, act.create_date desc                 
                    """
        self.env.cr.execute(query, {
            'partner_id': self.env.user.partner_id.id,
        })
        activity_data = self.env.cr.dictfetchall()
        model_ids = [a['model_id'] for a in activity_data]
        model_names = {n[0]: n[1] for n in self.env['ir.model'].browse(model_ids).name_get()}
        user_activities = {}
        for activity in activity_data:
            if not user_activities.get((activity['res_id'], activity['model'])):
                create_date = activity['create_date'] + td(hours=7)
                if not create_date:
                    continue
                str_time = str(create_date).split(' ')
                s_time = str_time[1].split('.')
                time = s_time[0] if len(s_time) > 1 else s_time[0]
                day = create_date.day if create_date.day >= 10 else f'0{create_date.day}'
                month = create_date.month if create_date.month >= 10 else f'0{create_date.month}'
                str_create_date = f'{day}-{month}-{create_date.year} {time}'
                user_activities[(activity['message_id'], activity['model'])] = {
                    'id': activity['message_id'],
                    'name': model_names[activity['model_id']],
                    'url_portal': activity['url_portal'],
                    'model': activity['model'],
                    'res_id': activity['res_id'],
                    'res_name': activity['subject'],
                    'status': activity['status'],
                    'create_date': str_create_date,
                    'type': 'activity',
                    'total_count': 1 if activity['status'] == 'unseen' else 0,
                    'icon': activity['icon'] if activity['icon'] else 'fa-clock-o',
                }
            user_activities[(activity['message_id'], activity['model'])]['actions'] = [{
                'icon': activity['icon'] if activity['icon'] else 'fa-clock-o',
                'name': 'Summary',
            }]
        return list(user_activities.values())

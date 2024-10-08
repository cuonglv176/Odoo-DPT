from odoo import models, fields, api
import logging
_logger = logging.getLogger(__name__)

class BaseAutomation(models.Model):
    _inherit = 'base.automation'

    type = fields.Selection([
        ('normal', 'Normal'),
        ('notification', 'Notification'),
    ], default='normal')
    message_notification = fields.Text(string='Nội dung thông báo',
                                       help='Có thể kèm nội dung của record (Tương đương với bản ghi đang được kích hoạt hiện tại) ví dụ : Thông báo đơn hàng {record.name} đã xác nhận')
    notification_type = fields.Selection([
        ('success', 'Success'),
        ('danger', 'Danger'),
        ('warning', 'Warning'),
        ('info', 'Info'),
    ])
    partner_ids = fields.Many2many('res.partner', string='Người nhận')
    partner_ids_by_record = fields.Many2many(
        'ir.model.fields',
        'base_automation_res_partner_filter_rel',
        'partner_ids_by_record_id',
        'base_automation_id',
        string='Field',
        domain="[('model_id', '=', model_id), ('relation', 'in', ['res.users', 'res.partner'])]"
    )

    def exec_and_get_return(code, record, python_code):
        # Create a local dictionary to hold the execution context
        local_context = {}

        # Define a function in the exec code to return a value
        exec_code = f"""
def dynamic_message(record):
    {python_code}
    return message  # Ensure 'message' is defined in the executed code
        """

        _logger.log(logging.INFO, exec_code)

        # Execute the code to define the function
        exec(exec_code, {}, local_context)

        # Check if the function was created successfully
        if 'dynamic_message' in local_context:
            # Call the dynamically created function with provided arguments
            return local_context['dynamic_message'](record)
        else:
            raise KeyError("The dynamic_message function was not created.")


    @api.onchange('model_id')
    def _onchange_model_id(self):
        for rec in self:
            rec.partner_ids_by_record = [(6, 0, [])]

    def _execute_notification_web(self, record_id):
        res_partner_ids = self.get_partner_by_records(record_id)
        if record_id and res_partner_ids:
            message = self.exec_and_get_return(record_id, self.message_notification)
            self.env['mail.message']._push_system_notification(
                self.create_uid.id,
                res_partner_ids.ids, message,
                self.model_id.model, record_id.id
            )

    def get_partner_by_records(self, record_id):
        res_partner_ids = self.partner_ids or self.env['res.partner']
        for field in self.partner_ids_by_record:
            field_data = getattr(record_id, field.name)
            if not field_data:
                continue
            if field_data._name == 'res.users':
                res_partner_ids += field_data.partner_id
                continue
            if field_data:
                res_partner_ids += field_data
        return res_partner_ids

    # res_partner_ids = automation_id.get_partner_by_records(record)
    # env['mail.message']._push_system_notification(
    #     {result.create_uid.id},
    #     automation_id.partner_ids.ids, automation_id.message_notification.format(record=record),
    #     '{result.model_id.model}', record.id
    # )

    @api.model_create_multi
    def create(self, vals_list):
        result = super().create(vals_list)
        if result.type != 'notification':
            return result
        self.env["ir.actions.server"].create({
            "name": "Modify name",
            "base_automation_id": result.id,
            "model_id": result.model_id.id,
            "state": "code",
            "code": f"""
automation_id = env['base.automation'].browse({result.id})
automation_id._execute_notification_web(record)
"""
        })
        return result

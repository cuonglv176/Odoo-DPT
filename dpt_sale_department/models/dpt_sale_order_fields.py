from odoo import models, fields, api, _
from odoo.osv.expression import AND, OR


class DPTSaleOrderFields(models.Model):
    _inherit = 'dpt.sale.order.fields'

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None, access_rights_uid=None):
        if not self.env.context.get('separate_for_department', False):
            return super()._search(domain, offset, limit, order, access_rights_uid)
        domain = self.process_domain(domain)
        return super()._search(domain, offset, limit, order, access_rights_uid)

    def process_domain(self, domain):
        """
        Process domain to filter out detail
        """
        # Skip process domain if system user or skip_process_domain context is set
        if not self.env.context.get('separate_for_department', False):
            return domain
        current_employee_id = self.env.user.employee_ids[:1]
        if not current_employee_id:
            return domain
        department_and_child_ids = current_employee_id.department_id | current_employee_id.department_id.child_ids
        domain = AND([domain, [('service_id.department_id', 'in', department_and_child_ids.ids)]])
        return domain

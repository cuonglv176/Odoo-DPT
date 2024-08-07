from odoo import models, fields, api, _
from odoo.osv.expression import AND, OR


class SaleOrder(models.Model):
    _inherit = 'sale.order'

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
        if not self.env.context.get('separate_for_department', False) and not self.env.context.get(
                'separate_purchase_for_department', False) and not self.env.context.get(
            'separate_inventory_for_department', False) and not self.env.context.get(
            'separate_import_export_for_department', False):
            return domain
        current_employee_id = self.env.user.employee_ids[:1]
        if not current_employee_id:
            return domain
        if self.env.context.get('separate_purchase_for_department', False):
            service_purchase_type_id = self.env['dpt.service.management.type'].search([('code', '=', 'purchase')])
            domain = AND(
                [domain, [('sale_service_ids.service_id.service_type_id', 'in', service_purchase_type_id.ids)]])
        if self.env.context.get('separate_inventory_for_department', False):
            service_inventory_type_id = self.env['dpt.service.management.type'].search([('code', '=', 'inventory')])
            domain = AND(
                [domain, [('sale_service_ids.service_id.service_type_id', 'in', service_inventory_type_id.ids)]])
        if self.env.context.get('separate_import_export_for_department', False):
            service_import_export_type_id = self.env['dpt.service.management.type'].search(
                [('code', '=', 'import_export')])
            domain = AND(
                [domain, [('sale_service_ids.service_id.service_type_id', 'in', service_import_export_type_id.ids)]])
        # department_and_child_ids = current_employee_id.department_id | current_employee_id.department_id.child_ids
        # domain = AND([domain, [('sale_service_ids.service_id.department_id', 'in', department_and_child_ids.ids)]])
        return domain

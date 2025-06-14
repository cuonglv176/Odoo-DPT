# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, _
from collections import defaultdict

class AgedPartnerBalanceCustomHandler(models.AbstractModel):
    _inherit = 'account.aged.partner.balance.report.handler'

    def _aged_partner_report_custom_engine_common(self, options, internal_type, current_groupby, next_groupby, offset=0, limit=None):
        """Override to include child companies when querying for a parent company."""
        result = super()._aged_partner_report_custom_engine_common(options, internal_type, current_groupby, next_groupby, offset=offset, limit=limit)
        
        # If we're not grouping by partner_id, we don't need to do anything special
        if current_groupby != 'partner_id':
            return result
        
        # Get all partners with their results
        partners_data = {}
        for partner_id, partner_values in result:
            if partner_id:
                partners_data[partner_id] = partner_values
        
        # If no partners, return the original result
        if not partners_data:
            return result
        
        # Get all partners
        partners = self.env['res.partner'].browse(partners_data.keys())
        
        # Process parent-child relationships
        parent_partners = partners.filtered(lambda p: p.is_company and not p.parent_id)
        child_partners = partners.filtered(lambda p: p.is_company and p.parent_id)
        
        # Create a mapping of parent to children
        parent_to_children = {}
        for child in child_partners:
            if child.parent_id in parent_partners:
                parent_to_children.setdefault(child.parent_id.id, []).append(child.id)
        
        # Add child values to parent
        for parent_id, child_ids in parent_to_children.items():
            if parent_id in partners_data:
                parent_values = partners_data[parent_id]
                
                # Add child values to parent for each period
                for i in range(6):  # 6 periods in aged partner balance
                    period_key = f'period{i}'
                    for child_id in child_ids:
                        if child_id in partners_data:
                            child_values = partners_data[child_id]
                            parent_values[period_key] += child_values[period_key]
                
                # Update total
                parent_values['total'] = sum(parent_values[f'period{i}'] for i in range(6))
        
        # Rebuild the result with updated values
        updated_result = []
        for partner_id, partner_values in result:
            if partner_id in partners_data:
                updated_result.append((partner_id, partners_data[partner_id]))
            else:
                updated_result.append((partner_id, partner_values))
        
        return updated_result

    def _common_custom_unfold_all_batch_data_generator(self, internal_type, report, options, lines_to_expand_by_function):
        """Override to include child companies when a parent company is expanded."""
        result = super()._common_custom_unfold_all_batch_data_generator(internal_type, report, options, lines_to_expand_by_function)
        
        # If no result, return the original result
        if not result:
            return result
        
        # Process the result to add child companies
        for expand_function_name, lines_to_expand in lines_to_expand_by_function.items():
            if expand_function_name == '_report_expand_unfoldable_line_with_groupby':
                for line_to_expand in lines_to_expand:
                    report_line_id = report._get_res_id_from_line_id(line_to_expand['id'], 'account.report.line')
                    
                    # Get all partners with their values
                    partners_data = {}
                    for key, column_group_data in result.items():
                        if key.startswith(f"[{report_line_id}]=>partner_id"):
                            for column_group_key, expressions_data in column_group_data.items():
                                for expression, expression_data in expressions_data.items():
                                    for partner_id, partner_values in expression_data['value']:
                                        partners_data.setdefault(partner_id, {}).setdefault(column_group_key, {}).setdefault(expression, partner_values)
                    
                    # If no partners, continue
                    if not partners_data:
                        continue
                    
                    # Get all partners
                    partners = self.env['res.partner'].browse(partners_data.keys())
                    
                    # Process parent-child relationships
                    parent_partners = partners.filtered(lambda p: p.is_company and not p.parent_id)
                    child_partners = partners.filtered(lambda p: p.is_company and p.parent_id)
                    
                    # Create a mapping of parent to children
                    parent_to_children = {}
                    for child in child_partners:
                        if child.parent_id in parent_partners:
                            parent_to_children.setdefault(child.parent_id.id, []).append(child.id)
                    
                    # Add child values to parent
                    for parent_id, child_ids in parent_to_children.items():
                        for column_group_key in partners_data.get(parent_id, {}):
                            for expression in partners_data[parent_id][column_group_key]:
                                parent_values = partners_data[parent_id][column_group_key][expression]
                                
                                # Add child values to parent for each period
                                for i in range(6):  # 6 periods in aged partner balance
                                    period_key = f'period{i}'
                                    for child_id in child_ids:
                                        if child_id in partners_data and column_group_key in partners_data[child_id] and expression in partners_data[child_id][column_group_key]:
                                            child_values = partners_data[child_id][column_group_key][expression]
                                            if period_key in parent_values and period_key in child_values:
                                                parent_values[period_key] += child_values[period_key]
                                
                                # Update total
                                if 'total' in parent_values:
                                    parent_values['total'] = sum(parent_values.get(f'period{i}', 0) for i in range(6))
                                
                                # Update the result
                                for key, column_group_data in result.items():
                                    if key.startswith(f"[{report_line_id}]=>partner_id"):
                                        for col_group_key, expressions_data in column_group_data.items():
                                            for expr, expression_data in expressions_data.items():
                                                for i, (pid, values) in enumerate(expression_data['value']):
                                                    if pid == parent_id:
                                                        expression_data['value'][i] = (parent_id, parent_values)
        
        return result

class AgedPayableCustomHandler(models.AbstractModel):
    _inherit = 'account.aged.payable.report.handler'

class AgedReceivableCustomHandler(models.AbstractModel):
    _inherit = 'account.aged.receivable.report.handler'
# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, _
from odoo.osv import expression

class PartnerLedgerCustomHandler(models.AbstractModel):
    _inherit = 'account.partner.ledger.report.handler'

    def _query_partners(self, options):
        """ Override to include child companies when querying for a parent company.
        This method executes the queries and performs all the computation.
        :return:        A list of tuple (partner, column_group_values) sorted by the table's model _order:
                        - partner is a res.parter record.
                        - column_group_values is a dict(column_group_key, fetched_values), where
                            - column_group_key is a string identifying a column group, like in options['column_groups']
                            - fetched_values is a dictionary containing:
                                - sum:                              {'debit': float, 'credit': float, 'balance': float}
                                - (optional) initial_balance:       {'debit': float, 'credit': float, 'balance': float}
                                - (optional) lines:                 [line_vals_1, line_vals_2, ...]
        """
        def assign_sum(row):
            fields_to_assign = ['balance', 'debit', 'credit']
            if any(not company_currency.is_zero(row[field]) for field in fields_to_assign):
                groupby_partners.setdefault(row['groupby'], {})
                for field in fields_to_assign:
                    groupby_partners[row['groupby']].setdefault(row['column_group_key'], {}).setdefault(field, 0.0)
                    groupby_partners[row['groupby']][row['column_group_key']][field] += row[field]

        company_currency = self.env.company.currency_id

        # Execute the queries and dispatch the results.
        query, params = self._get_query_sums(options)

        groupby_partners = {}

        self._cr.execute(query, params)
        for res in self._cr.dictfetchall():
            assign_sum(res)

        # Correct the sums per partner, for the lines without partner reconciled with a line having a partner
        query, params = self._get_sums_without_partner(options)

        self._cr.execute(query, params)
        totals = {}
        for total_field in ['debit', 'credit', 'balance']:
            totals[total_field] = {col_group_key: 0 for col_group_key in options['column_groups']}

        for row in self._cr.dictfetchall():
            totals['debit'][row['column_group_key']] += row['debit']
            totals['credit'][row['column_group_key']] += row['credit']
            totals['balance'][row['column_group_key']] += row['balance']

            if row['groupby'] not in groupby_partners:
                continue

            assign_sum(row)

        if None in groupby_partners:
            # Debit/credit are inverted for the unknown partner as the computation is made regarding the balance of the known partner
            for column_group_key in options['column_groups']:
                groupby_partners.setdefault(None, {}).setdefault(column_group_key, {}).setdefault('debit', 0.0)
                groupby_partners.setdefault(None, {}).setdefault(column_group_key, {}).setdefault('credit', 0.0)
                groupby_partners.setdefault(None, {}).setdefault(column_group_key, {}).setdefault('balance', 0.0)
                groupby_partners[None][column_group_key]['debit'] += totals['credit'][column_group_key]
                groupby_partners[None][column_group_key]['credit'] += totals['debit'][column_group_key]
                groupby_partners[None][column_group_key]['balance'] -= totals['balance'][column_group_key]

        # Retrieve the partners to browse.
        # groupby_partners.keys() contains all account ids affected by:
        # - the amls in the current period.
        # - the amls affecting the initial balance.
        if groupby_partners:
            # Note a search is done instead of a browse to preserve the table ordering.
            partners = self.env['res.partner'].with_context(active_test=False).search([('id', 'in', list(groupby_partners.keys()))])
        else:
            partners = []

        # Add 'Partner Unknown' if needed
        if None in groupby_partners.keys():
            partners = [p for p in partners] + [None]

        # Process parent-child relationships
        parent_partners = partners.filtered(lambda p: p and p.is_company and not p.parent_id)
        child_partners = partners.filtered(lambda p: p and p.is_company and p.parent_id)
        
        # Create a mapping of parent to children
        parent_to_children = {}
        for child in child_partners:
            if child.parent_id in parent_partners:
                parent_to_children.setdefault(child.parent_id.id, []).append(child.id)
        
        # Add child values to parent
        for parent_id, child_ids in parent_to_children.items():
            for child_id in child_ids:
                if child_id in groupby_partners:
                    for column_group_key in options['column_groups']:
                        if column_group_key in groupby_partners.get(parent_id, {}):
                            for field in ['debit', 'credit', 'balance']:
                                groupby_partners[parent_id][column_group_key][field] += groupby_partners[child_id][column_group_key].get(field, 0.0)

        return [(partner, groupby_partners[partner.id if partner else None]) for partner in partners]

    def _report_expand_unfoldable_line_partner_ledger(self, line_dict_id, groupby, options, progress, offset, unfold_all_batch_data=None):
        """Override to show child companies when a parent company is expanded."""
        result = super()._report_expand_unfoldable_line_partner_ledger(line_dict_id, groupby, options, progress, offset, unfold_all_batch_data)
        
        report = self.env['account.report'].browse(options['report_id'])
        markup, model, record_id = report._parse_line_id(line_dict_id)[-1]
        
        if model == 'res.partner':
            partner = self.env['res.partner'].browse(record_id)
            if partner.is_company and not partner.parent_id:
                # This is a parent company, add child companies
                child_companies = self.env['res.partner'].search([
                    ('parent_id', '=', partner.id),
                    ('is_company', '=', True)
                ])
                
                if child_companies:
                    # Add a section for child companies
                    child_section_line = {
                        'id': report._get_generic_line_id('child.companies', partner.id, parent_line_id=line_dict_id),
                        'parent_id': line_dict_id,
                        'name': _("Child Companies"),
                        'columns': [{'name': ''} for _ in options['columns']],
                        'level': 4,
                        'unfoldable': False,
                    }
                    
                    # Insert the child section line at the end of the lines
                    result['lines'].append(child_section_line)
                    
                    # Add lines for each child company
                    for child in child_companies:
                        # Get the child company's data
                        child_data = self._get_aml_values(options, [child.id], offset=0, limit=None)[child.id]
                        
                        if child_data:
                            # Create a line for the child company
                            child_line = {
                                'id': report._get_generic_line_id('res.partner', child.id, parent_line_id=child_section_line['id']),
                                'parent_id': child_section_line['id'],
                                'name': child.name,
                                'columns': [{'name': ''} for _ in options['columns']],
                                'level': 5,
                                'unfoldable': True,
                                'expand_function': '_report_expand_unfoldable_line_partner_ledger',
                            }
                            
                            # Add the child company line
                            result['lines'].append(child_line)
        
        return result
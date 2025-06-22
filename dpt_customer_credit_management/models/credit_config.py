from odoo import models, fields, api, _


class CreditConfig(models.TransientModel):
    _name = 'credit.config.settings'
    _inherit = 'res.config.settings'
    _description = 'Credit Management Configuration'

    default_credit_limit = fields.Monetary(
        string='Default Credit Limit',
        currency_field='currency_id',
        config_parameter='dpt_credit.default_credit_limit'
    )

    default_interest_rate = fields.Float(
        string='Default Interest Rate (%)',
        config_parameter='dpt_credit.default_interest_rate'
    )

    interest_calculation_frequency = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly')
    ], string='Interest Calculation Frequency',
        config_parameter='dpt_credit.interest_frequency',
        default='monthly')

    auto_block_on_limit = fields.Boolean(
        string='Auto Block on Credit Limit',
        config_parameter='dpt_credit.auto_block_on_limit',
        default=True
    )

    warning_threshold = fields.Float(
        string='Warning Threshold (%)',
        config_parameter='dpt_credit.warning_threshold',
        default=80.0,
        help="Show warning when credit utilization exceeds this percentage"
    )

    currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id'
    )

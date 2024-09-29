from odoo import fields, models, api, _
import math
import logging

_logger = logging.getLogger(__name__)


class PurchaseOrderLinePackage(models.Model):
    _inherit = 'purchase.order.line.package'

    lot_id = fields.Many2one('stock.lot', 'Lot')

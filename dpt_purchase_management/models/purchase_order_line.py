from odoo import fields, models, api
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, get_lang
from odoo.tools.float_utils import float_compare, float_round


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    buying_url = fields.Char('Buying URL')
    cost = fields.Monetary('Cost')
    price_unit2 = fields.Float('Price Unit 2')
    price_cost2 = fields.Float('Price Cost 2')
    price_subtotal2 = fields.Float('Price Subtotal 2', compute='_compute_price_subtotal2', store=True)
    price_unit3 = fields.Float('Price Unit 3')
    price_cost3 = fields.Float('Price Cost 3')
    price_subtotal3 = fields.Float('Price Subtotal 3', compute='_compute_price_subtotal3', store=True)

    @api.depends('price_unit2', 'product_qty', 'price_cost2')
    def _compute_price_subtotal2(self):
        for r in self:
            r.price_subtotal2 = r.price_unit2 * r.product_qty + r.price_cost2

    @api.depends('price_unit3', 'product_qty', 'price_cost3')
    def _compute_price_subtotal3(self):
        for r in self:
            r.price_subtotal3 = r.price_unit3 * r.product_qty + r.price_cost3

    @api.depends('product_qty', 'product_uom', 'company_id')
    def _compute_price_unit_and_date_planned_and_name(self):
        for line in self:
            if not line.product_id or line.invoice_lines or not line.company_id or self.env.context.get(
                    'no_compute_price', False):
                continue
            params = {'order_id': line.order_id}
            seller = line.product_id._select_seller(
                partner_id=line.partner_id,
                quantity=line.product_qty,
                date=line.order_id.date_order and line.order_id.date_order.date() or fields.Date.context_today(line),
                uom_id=line.product_uom,
                params=params)

            if seller or not line.date_planned:
                line.date_planned = line._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

            # If not seller, use the standard price. It needs a proper currency conversion.
            if not seller:
                unavailable_seller = line.product_id.seller_ids.filtered(
                    lambda s: s.partner_id == line.order_id.partner_id)
                if not unavailable_seller and line.price_unit and line.product_uom == line._origin.product_uom:
                    # Avoid to modify the price unit if there is no price list for this partner and
                    # the line has already one to avoid to override unit price set manually.
                    continue
                po_line_uom = line.product_uom or line.product_id.uom_po_id
                price_unit = line.env['account.tax']._fix_tax_included_price_company(
                    line.product_id.uom_id._compute_price(line.product_id.standard_price, po_line_uom),
                    line.product_id.supplier_taxes_id,
                    line.taxes_id,
                    line.company_id,
                )
                price_unit = line.product_id.cost_currency_id._convert(
                    price_unit,
                    line.currency_id,
                    line.company_id,
                    line.date_order or fields.Date.context_today(line),
                    False
                )
                line.price_unit = float_round(price_unit, precision_digits=max(line.currency_id.decimal_places,
                                                                               self.env[
                                                                                   'decimal.precision'].precision_get(
                                                                                   'Product Price')))
                continue

            price_unit = line.env['account.tax']._fix_tax_included_price_company(seller.price,
                                                                                 line.product_id.supplier_taxes_id,
                                                                                 line.taxes_id,
                                                                                 line.company_id) if seller else 0.0
            price_unit = seller.currency_id._convert(price_unit, line.currency_id, line.company_id,
                                                     line.date_order or fields.Date.context_today(line), False)
            price_unit = float_round(price_unit, precision_digits=max(line.currency_id.decimal_places,
                                                                      self.env['decimal.precision'].precision_get(
                                                                          'Product Price')))
            line.price_unit = seller.product_uom._compute_price(price_unit, line.product_uom)
            line.discount = seller.discount or 0.0

            # record product names to avoid resetting custom descriptions
            default_names = []
            vendors = line.product_id._prepare_sellers({})
            product_ctx = {'seller_id': None, 'partner_id': None, 'lang': get_lang(line.env, line.partner_id.lang).code}
            default_names.append(line._get_product_purchase_description(line.product_id.with_context(product_ctx)))
            for vendor in vendors:
                product_ctx = {'seller_id': vendor.id, 'lang': get_lang(line.env, line.partner_id.lang).code}
                default_names.append(line._get_product_purchase_description(line.product_id.with_context(product_ctx)))
            if not line.name or line.name in default_names:
                product_ctx = {'seller_id': seller.id, 'lang': get_lang(line.env, line.partner_id.lang).code}
                line.name = line._get_product_purchase_description(line.product_id.with_context(product_ctx))

    @api.depends('product_qty', 'price_unit', 'taxes_id', 'discount', 'cost')
    def _compute_amount(self):
        for line in self:
            tax_results = self.env['account.tax']._compute_taxes([line._convert_to_tax_base_line_dict()])
            totals = next(iter(tax_results['totals'].values()))
            amount_untaxed = totals['amount_untaxed']
            amount_tax = totals['amount_tax']

            line.update({
                'price_subtotal': amount_untaxed + line.cost,
                'price_tax': amount_tax + line.cost,
                'price_total': amount_untaxed + amount_tax + line.cost,
            })

from odoo import models, fields

class ImportLine(models.Model):
    _name = "dpt.import.line"
    _description = "Import Line"

    import_history_id = fields.Many2one("dpt.import.history", string="Import History")
    buyer_id = fields.Many2one("res.partner", string="Buyer")
    seller_id = fields.Many2one("res.partner", string="Seller")
    hs_code = fields.Char("HS Code")
    product_details = fields.Text("Product Details")
    arrival_port_id = fields.Many2one("dpt.import.port", string="Port of Arrival")
    departure_port_id = fields.Many2one("dpt.import.port", string="Port of Departure")
    brand_id = fields.Many2one("dpt.import.brand", string="Brand")
    state = fields.Selection(
        [("draft", "Draft"), ("done", "Done"), ("error", "Error")],
        string="Status",
        default="draft",
    )
    error_message = fields.Text("Error Message")

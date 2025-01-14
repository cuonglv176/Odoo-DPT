from odoo import models, fields, api

class ImportHistory(models.Model):
    _name = "dpt.import.history"
    _description = "Import History"

    name = fields.Char("File Name", required=True)
    import_date = fields.Datetime("Import Date", default=fields.Datetime.now)
    user_id = fields.Many2one("res.users", "Imported By", default=lambda self: self.env.user)
    total_rows = fields.Integer("Total Rows")
    success_rows = fields.Integer("Successful Rows")
    failed_rows = fields.Integer("Failed Rows")
    error_log = fields.Text("Error Log")
    state = fields.Selection(
        [("draft", "Draft"), ("done", "Done"), ("failed", "Failed")],
        string="Status",
        default="draft",
    )

    import_line_ids = fields.One2many("dpt.import.line", "import_history_id", string="Import Lines")

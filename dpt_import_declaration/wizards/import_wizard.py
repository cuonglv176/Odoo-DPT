import base64
import xlrd
from odoo import models, fields, api
from odoo.exceptions import UserError

class ImportWizard(models.TransientModel):
    _name = "dpt.import.wizard"
    _description = "Import Wizard"

    file = fields.Binary("Excel File", required=True)
    filename = fields.Char("Filename")

    def action_import(self):
        try:
            # Decode file
            excel_data = base64.b64decode(self.file)
            workbook = xlrd.open_workbook(file_contents=excel_data)
            sheet = workbook.sheet_by_index(0)

            # Create import history
            import_history = self.env["dpt.import.history"].create({
                "name": self.filename,
                "state": "draft",
            })

            for row_idx in range(1, sheet.nrows):
                row = sheet.row_values(row_idx)
                try:
                    # Process row data here
                    self.env["dpt.import.line"].create({
                        "import_history_id": import_history.id,
                        "buyer_id": self._get_partner(row[2]),
                        "seller_id": self._get_partner(row[5]),
                        "hs_code": row[8],
                        "product_details": row[10],
                        "state": "done",
                    })
                except Exception as e:
                    import_history.error_log += f"Row {row_idx}: {str(e)}\n"

            import_history.state = "done"
        except Exception as e:
            raise UserError(f"Import failed: {str(e)}")

    def _get_partner(self, name):
        partner = self.env["res.partner"].search([("name", "=", name)], limit=1)
        if not partner:
            partner = self.env["res.partner"].create({"name": name})
        return partner.id

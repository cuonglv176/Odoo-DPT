# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.drawing.image import Image
from datetime import timedelta
import os
import io
import base64


class StockPicking(models.Model):
    _inherit = 'stock.picking'
    _rec_name = 'picking_lot_name'

    def action_export_picking_report(self, file_type):
        if file_type == 'outgoing':
            file = self.export_outgoing_report_file()
            file_name = "Danh sách phiếu xuất kho.xlsx"
        else:
            return
        if file_name and file:
            attachment_id = self.env['ir.attachment'].search([('name', 'ilike', file_name)])
            if attachment_id:
                attachment_id.unlink()
            attachment_id = self.env['ir.attachment'].sudo().create({
                'name': file_name,
                'type': 'binary',
                'datas': base64.b64encode(file),
                'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            })
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{attachment_id.id}?download=true',
                'target': 'self',
            }

    def export_outgoing_report_file(self):
        logo_path = "D:\Odoo17\Source\Odoo-DPT\dpt_stock_management\static\description\logo.png"
        # Create a new workbook and select the active worksheet
        wb = Workbook()
        ws = wb.active
        ws.title = "Danh sách phiếu xuất kho"

        font_1 = Font(name='Times New Roman', size=24, bold=True)
        font_2 = Font(name='Times New Roman', size=12)
        font_3 = Font(name='Times New Roman', size=12, bold=True)

        # Define styles
        # Header title style - light blue
        title_fill = PatternFill(fill_type="solid")
        title_alignment = Alignment(horizontal='center', vertical='center')

        # Border style
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # First merge horizontally for each row
        for row in range(2, 4):
            # Apply borders to all cells in the row
            for col in range(1, 4):
                cell = ws.cell(row=row, column=col)
                cell.border = thin_border
        # Add company logo if provided
        if logo_path and os.path.exists(logo_path):
            img = Image(logo_path)
            # Position the image in cell A1
            ws.add_image(img, 'A2')

        ws.merge_cells('D2:K2')
        cell = ws.cell(row=2, column=3)
        cell.value = "PHIẾU XUẤT KHO"
        cell.font = font_1
        cell.alignment = title_alignment
        cell.fill = title_fill

        ws.merge_cells('H4:I4')
        cell = ws.cell(row=4, column=8)
        cell.value = "Số phiếu:"
        cell.font = font_2
        cell.alignment = title_alignment
        cell.fill = title_fill

        ws.merge_cells('J4:K4')
        cell = ws.cell(row=4, column=10)
        cell.value = self.name
        cell.font = font_2
        cell.alignment = title_alignment
        cell.fill = title_fill

        ws.merge_cells('C5:D5')
        cell = ws.cell(row=5, column=3)
        cell.value = f"Họ và tên người nhận: {self.partner_id.name}"
        cell.font = font_2
        cell.alignment = title_alignment
        cell.fill = title_fill

        cell = ws.cell(row=5, column=8)
        cell.value = f"Mã KH: "
        cell.font = font_2
        cell.alignment = title_alignment
        cell.fill = title_fill

        ws.merge_cells('C6:D6')
        cell = ws.cell(row=6, column=3)
        cell.value = f"Địa chỉ: {self.partner_id.street}"
        cell.font = font_2
        cell.alignment = title_alignment
        cell.fill = title_fill

        ws.merge_cells('C7:D7')
        cell = ws.cell(row=7, column=3)
        cell.value = f"Số điện thoại liên hệ: {self.partner_id.phone}"
        cell.font = font_2
        cell.alignment = title_alignment
        cell.fill = title_fill

        ws.merge_cells('C8:D8')
        cell = ws.cell(row=8, column=3)
        cell.value = f"Xuất tại kho: {self.partner_id.phone}"
        cell.font = font_2
        cell.alignment = title_alignment
        cell.fill = title_fill

        # Add company logo if provided
        if logo_path and os.path.exists(logo_path):
            img = Image(logo_path)
            # Position the image in cell A1
            ws.add_image(img, 'C2')

        # # Define column headers (row 9)
        headers = ["Số TT", "Mã đơn(ID)", "Mã Lô", "Sản phẩm", "Nhóm kiện", "Trọng lượng(kg)", "Thể tích(m3)",
                   "Ghi chú"]
        #
        # Add column headers
        for col_idx, header in enumerate(headers, 2):
            cell = ws.cell(row=9, column=col_idx)
            cell.value = header
            cell.font = font_3
            cell.alignment = title_alignment
            cell.fill = title_fill
            cell.border = thin_border

        data_list = self.get_data()

        # # Add sample data to worksheet
        row_idx = 10  # Start from row 10 (after headers)
        alt_row_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")  # Light gray

        for idx, data in enumerate(data_list):
            # Apply alternating row colors
            row_fill = alt_row_fill if idx % 2 == 0 else None

            for col_idx, header in enumerate(headers, 2):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.value = data.get(header, "")
                cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                cell.border = thin_border
                if row_fill:
                    cell.fill = row_fill

            row_idx += 1
        #
        # # Set column widths
        # column_widths = {
        #     1: 5,  # No.
        #     2: 15,  # 문서번호
        #     3: 30,  # 보관부서
        #     4: 15,  # 기기번호
        #     5: 50,  # 기기명
        #     6: 30,  # 형식
        #     7: 30,  # 제작회사
        #     8: 12,  # 교정일자
        #     9: 12,  # 차기교정 예정일
        #     10: 12,  # 관리주기 (월)
        #     11: 10,  # 교정대상
        #     12: 50,  # 교정기관
        #     13: 25,  # 용도
        #     14: 50,  # 기타
        #     15: 20,  # 교정유형
        #     16: 8,  # 검증여부
        #     17: 8,  # 사용여부
        # }
        #
        # for col_num, width in column_widths.items():
        #     ws.column_dimensions[get_column_letter(col_num)].width = width

        # Instead of saving to file, save to BytesIO object
        excel_bytes = io.BytesIO()
        wb.save(excel_bytes)
        excel_bytes.seek(0)  # Move to the beginning of the BytesIO object

        # Return the bytes
        return excel_bytes.getvalue()

    def get_data(self):
        data = []
        if not self:
            return data
        index = 1
        for package_id in self.package_ids:
            data.append({
                "Số TT": index,
                "Mã đơn(ID)": self.sale_purchase_id.name or "",
                "Mã Lô": self.picking_lot_name or "",
                "Sản phẩm": "",
                "Nhóm kiện": f"{package_id.quantity}{package_id.uom_id.packing_code}",
                "Trọng lượng(kg)": package_id.total_weight,
                "Thể tích(m3)": package_id.total_volume,
                "Ghi chú": "",
            })
            index += 1
        return data

    def export_incoming_report_file(self):
        logo_path = "D:\Odoo17\Source\Odoo-DPT\dpt_stock_management\static\description\logo.png"
        # Create a new workbook and select the active worksheet
        wb = Workbook()
        ws = wb.active
        ws.title = "Phiếu xuất kho"

        font_1 = Font(name='Times New Roman', size=24, bold=True)
        font_2 = Font(name='Times New Roman', size=12, bold=True, italic=True)
        font_3 = Font(name='Times New Roman', size=12, bold=True)

        # Define styles
        # Header title style - light blue
        title_fill = PatternFill(fill_type="solid")
        title_alignment = Alignment(horizontal='center', vertical='center')

        # Column header style - darker blue
        # header_fill = PatternFill(start_color="BDD7EE", end_color="BDD7EE", fill_type="solid")
        # header_alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)

        # Border style
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

        # First merge horizontally for each row
        for row in range(2, 4):
            # Apply borders to all cells in the row
            for col in range(1, 4):
                cell = ws.cell(row=row, column=col)
                cell.border = thin_border
        # Add company logo if provided
        if logo_path and os.path.exists(logo_path):
            img = Image(logo_path)
            # Position the image in cell A1
            ws.add_image(img, 'A2')

        ws.merge_cells('E2:I2')
        cell = ws.cell(row=2, column=4)
        cell.value = "PHIẾU NHẬP KHO"
        cell.font = font_1
        cell.alignment = title_alignment
        cell.fill = title_fill

        cell = ws.cell(row=2, column=10)
        cell.value = "Mẫu số : 01 - VT"
        cell.font = font_2
        cell.alignment = title_alignment
        cell.fill = title_fill

        # # Define column headers (row 9)
        # headers = [
        #     "No.", "문서번호", "보관부서", "기기번호\n(S/N)", "기기명\n(Description)",
        #     "형식\n(Model name)", "제작회사\n(Manufacturer)", "교정일자", "차기교정\n예정일",
        #     "관리주기 (월)", "교정대상", "교정기관", "용도", "기타", "교정유형", "검증\n여부", "사용\n여부"
        # ]
        #
        # # Add column headers
        # for col_idx, header in enumerate(headers, 1):
        #     cell = ws.cell(row=8, column=col_idx)
        #     cell.value = header
        #     cell.font = header_font
        #     cell.alignment = header_alignment
        #     cell.fill = header_fill
        #     cell.border = thin_border
        #
        # data_list = self.get_data()
        #
        # # Add sample data to worksheet
        # row_idx = 9  # Start from row 8 (after headers)
        # alt_row_fill = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")  # Light gray
        #
        # for idx, data in enumerate(data_list):
        #     # Apply alternating row colors
        #     row_fill = alt_row_fill if idx % 2 == 0 else None
        #
        #     for col_idx, header in enumerate(headers, 1):
        #         cell = ws.cell(row=row_idx, column=col_idx)
        #         cell.value = data.get(header, "")
        #         cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        #         cell.border = thin_border
        #         if row_fill:
        #             cell.fill = row_fill
        #
        #     row_idx += 1
        #
        # # Set column widths
        # column_widths = {
        #     1: 5,  # No.
        #     2: 15,  # 문서번호
        #     3: 30,  # 보관부서
        #     4: 15,  # 기기번호
        #     5: 50,  # 기기명
        #     6: 30,  # 형식
        #     7: 30,  # 제작회사
        #     8: 12,  # 교정일자
        #     9: 12,  # 차기교정 예정일
        #     10: 12,  # 관리주기 (월)
        #     11: 10,  # 교정대상
        #     12: 50,  # 교정기관
        #     13: 25,  # 용도
        #     14: 50,  # 기타
        #     15: 20,  # 교정유형
        #     16: 8,  # 검증여부
        #     17: 8,  # 사용여부
        # }
        #
        # for col_num, width in column_widths.items():
        #     ws.column_dimensions[get_column_letter(col_num)].width = width

        # Instead of saving to file, save to BytesIO object
        excel_bytes = io.BytesIO()
        wb.save(excel_bytes)
        excel_bytes.seek(0)  # Move to the beginning of the BytesIO object

        # Return the bytes
        return excel_bytes.getvalue()
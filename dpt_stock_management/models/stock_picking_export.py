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
        if file_type == 'incoming':
            file = self.export_incoming_report_file()
            file_name = "Danh sách phiếu nhập kho.xlsx"
        elif file_type == 'outgoing':
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

    def export_incoming_report_file(self):
        logo_path = "D:\Odoo17\Source\Odoo-DPT\dpt_stock_management\static\description\logo.png"
        # Create a new workbook and select the active worksheet
        wb = Workbook()
        ws = wb.active
        ws.title = "Danh sách phiếu nhập kho"

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

        # Now merge B2:H6 (both horizontally and vertically)
        ws.merge_cells('E2:I2')
        cell = ws.cell(row=2, column=5)
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

    def get_data(self):
        data = []
        picking_ids = self.picking_ids
        if not picking_ids:
            return data
        index = 1
        # for picking_id in picking_ids:
        #
        #     for calibration_schedule_in_year in calibration_schedules_in_year:
        #         installation_location = ''
        #         if hasattr(device_list_id, 'x_dytpl_jpt_04_installation_location'):
        #             installation_location = device_list_id.x_dytpl_jpt_04_installation_location.name or ''
        #             if hasattr(device_list_id, 'x_dytpl_jpt_04_installation_location_text'):
        #                 installation_location = device_list_id.x_dytpl_jpt_04_installation_location_text or installation_location
        #         data.append({
        #             "No.": index,
        #             "문서번호": device_list_id.management_number or "",
        #             "보관부서": installation_location,
        #             "기기번호\n(S/N)": device_list_id.x_dytpl_jpt_04_serial_number if hasattr(device_list_id,
        #                                                                                   'x_dytpl_jpt_04_serial_number') and device_list_id.x_dytpl_jpt_04_serial_number else "",
        #             "기기명\n(Description)": device_list_id.name or "",
        #             "형식\n(Model name)": device_list_id.x_dytpl_jpt_04_model_code if hasattr(device_list_id,
        #                                                                                     'x_dytpl_jpt_04_model_code') and device_list_id.x_dytpl_jpt_04_model_code else "",
        #             "제작회사\n(Manufacturer)": device_list_id.x_dytpl_jpt_04_manufacturer if hasattr(device_list_id,
        #                                                                                           'x_dytpl_jpt_04_manufacturer') and device_list_id.x_dytpl_jpt_04_manufacturer else "",
        #             "교정일자": calibration_schedule_in_year.calibrated_date.strftime(
        #                 "%Y/%m/%d") if calibration_schedule_in_year.calibrated_date else calibration_schedule_in_year.schedule_end_date.strftime(
        #                 "%Y/%m/%d") if calibration_schedule_in_year.schedule_end_date else "",
        #             "차기교정\n예정일": calibration_schedule_in_year.next_calibration_date.strftime(
        #                 "%Y/%m/%d") if calibration_schedule_in_year.next_calibration_date else "",
        #             "관리주기 (월)": device_list_id.management_cycle,
        #             "교정대상": "대상",
        #             "교정기관": device_list_id.x_dytpl_jpt_04_calibration_agency if hasattr(device_list_id,
        #                                                                                 'x_dytpl_jpt_04_calibration_agency') and device_list_id.x_dytpl_jpt_04_calibration_agency else "",
        #             "용도": device_list_id.x_dytpl_jpt_04_usage_purpose if hasattr(device_list_id,
        #                                                                          'x_dytpl_jpt_04_usage_purpose') and device_list_id.x_dytpl_jpt_04_usage_purpose else "",
        #             "기타": calibration_schedule_in_year.x_dytpl_jpt_09_schedule_remark if calibration_schedule_in_year.x_dytpl_jpt_09_schedule_remark and hasattr(
        #                 calibration_schedule_in_year, 'x_dytpl_jpt_09_schedule_remark') else "",
        #             "교정유형": device_list_id.x_dytpl_jpt_04_calibration_place if hasattr(device_list_id,
        #                                                                                'x_dytpl_jpt_04_calibration_place') and device_list_id.x_dytpl_jpt_04_calibration_place else "",
        #             "검증\n여부": "ㅇ",
        #             "사용\n여부": "ㅇ"
        #         })
        #         index += 1
        return data

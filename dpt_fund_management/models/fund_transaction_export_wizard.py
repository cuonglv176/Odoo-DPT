# -*- coding: utf-8 -*-

import base64
import io
from datetime import datetime, date
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import xlsxwriter


class FundTransactionExportWizard(models.TransientModel):
    _name = 'dpt.fund.transaction.export.wizard'
    _description = 'Wizard Export Giao Dịch Quỹ'

    fund_account_id = fields.Many2one(
        'dpt.fund.account',
        string='Tài Khoản Quỹ',
        required=True
    )

    name = fields.Char(
        string='Tên File',
        required=True,
        default=lambda self: f'GiaoDich_{fields.Date.today().strftime("%Y%m%d")}'
    )

    date_from = fields.Date(
        string='Từ Ngày',
        default=lambda self: fields.Date.today().replace(day=1)
    )

    date_to = fields.Date(
        string='Đến Ngày',
        default=fields.Date.today
    )

    transaction_type = fields.Selection([
        ('all', 'Tất cả'),
        ('income', 'Thu nhập'),
        ('expense', 'Chi phí')
    ], string='Loại Giao Dịch', default='all')

    state_filter = fields.Selection([
        ('all', 'Tất cả'),
        ('draft', 'Nháp'),
        ('posted', 'Đã xác nhận'),
        ('cancelled', 'Đã hủy')
    ], string='Trạng Thái', default='posted')

    include_summary = fields.Boolean(
        string='Bao gồm tổng kết',
        default=True
    )

    file_data = fields.Binary(string='File Excel')
    file_name = fields.Char(string='Tên File')
    state = fields.Selection([
        ('draft', 'Cấu hình'),
        ('done', 'Hoàn thành')
    ], default='draft')

    def action_export(self):
        """Thực hiện export"""
        self.ensure_one()

        # Lấy dữ liệu giao dịch
        domain = [('fund_account_id', '=', self.fund_account_id.id)]

        if self.date_from:
            domain.append(('date', '>=', self.date_from))
        if self.date_to:
            domain.append(('date', '<=', self.date_to))
        if self.transaction_type != 'all':
            domain.append(('transaction_type', '=', self.transaction_type))
        if self.state_filter != 'all':
            domain.append(('state', '=', self.state_filter))

        transactions = self.env['dpt.fund.transaction'].search(domain, order='date desc')

        if not transactions:
            raise UserError(_('Không có giao dịch nào phù hợp với điều kiện lọc!'))

        # Tạo file Excel
        file_data = self._create_excel_file(transactions)

        # Lưu file
        filename = f"{self.name}.xlsx"
        self.write({
            'file_data': file_data,
            'file_name': filename,
            'state': 'done'
        })

        # Trả về view download
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.fund.transaction.export.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': {'dialog_size': 'medium'}
        }

    def _create_excel_file(self, transactions):
        """Tạo file Excel"""
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        # Định dạng
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4CAF50',
            'color': 'white',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })

        data_format = workbook.add_format({
            'align': 'left',
            'valign': 'vcenter',
            'border': 1
        })

        number_format = workbook.add_format({
            'num_format': '#,##0',
            'align': 'right',
            'border': 1
        })

        date_format = workbook.add_format({
            'num_format': 'dd/mm/yyyy',
            'align': 'center',
            'border': 1
        })

        # Tạo worksheet
        worksheet = workbook.add_worksheet('Giao Dịch')

        # Tiêu đề
        worksheet.merge_range('A1:H1', f'DANH SÁCH GIAO DỊCH - {self.fund_account_id.name}', header_format)
        worksheet.merge_range('A2:H2',
                              f'Từ {self.date_from.strftime("%d/%m/%Y") if self.date_from else "..."} đến {self.date_to.strftime("%d/%m/%Y") if self.date_to else "..."}',
                              data_format)

        # Header cột
        headers = [
            'STT', 'Ngày', 'Mô tả', 'Loại', 'Số tiền', 'Tham chiếu', 'Trạng thái', 'Ghi chú'
        ]

        for col, header in enumerate(headers):
            worksheet.write(3, col, header, header_format)

        # Dữ liệu
        row = 4
        total_income = 0
        total_expense = 0

        for idx, transaction in enumerate(transactions, 1):
            worksheet.write(row, 0, idx, data_format)
            worksheet.write(row, 1, transaction.date, date_format)
            worksheet.write(row, 2, transaction.name or '', data_format)

            # Loại giao dịch
            trans_type = 'Thu nhập' if transaction.transaction_type == 'income' else 'Chi phí'
            worksheet.write(row, 3, trans_type, data_format)

            # Số tiền
            amount = transaction.amount
            if transaction.transaction_type == 'income':
                total_income += amount
            else:
                total_expense += abs(amount)
                amount = -abs(amount)  # Hiển thị số âm cho chi phí

            worksheet.write(row, 4, amount, number_format)
            worksheet.write(row, 5, transaction.reference or '', data_format)

            # Trạng thái
            state_map = {
                'draft': 'Nháp',
                'posted': 'Đã xác nhận',
                'cancelled': 'Đã hủy'
            }
            worksheet.write(row, 6, state_map.get(transaction.state, transaction.state), data_format)
            worksheet.write(row, 7, transaction.note or '', data_format)

            row += 1

        # Tổng kết nếu được yêu cầu
        if self.include_summary:
            row += 1
            worksheet.merge_range(f'A{row}:C{row}', 'TỔNG KẾT', header_format)

            row += 1
            worksheet.write(row, 0, 'Tổng thu nhập:', data_format)
            worksheet.write(row, 1, total_income, number_format)
            worksheet.write(row, 2, self.fund_account_id.currency_id.name, data_format)

            row += 1
            worksheet.write(row, 0, 'Tổng chi phí:', data_format)
            worksheet.write(row, 1, total_expense, number_format)
            worksheet.write(row, 2, self.fund_account_id.currency_id.name, data_format)

            row += 1
            worksheet.write(row, 0, 'Số dư ròng:', header_format)
            worksheet.write(row, 1, total_income - total_expense, number_format)
            worksheet.write(row, 2, self.fund_account_id.currency_id.name, data_format)

        # Điều chỉnh độ rộng cột
        worksheet.set_column('A:A', 8)  # STT
        worksheet.set_column('B:B', 12)  # Ngày
        worksheet.set_column('C:C', 30)  # Mô tả
        worksheet.set_column('D:D', 12)  # Loại
        worksheet.set_column('E:E', 15)  # Số tiền
        worksheet.set_column('F:F', 20)  # Tham chiếu
        worksheet.set_column('G:G', 12)  # Trạng thái
        worksheet.set_column('H:H', 25)  # Ghi chú

        workbook.close()
        output.seek(0)

        return base64.b64encode(output.read())

    def action_download(self):
        """Download file"""
        self.ensure_one()

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/?model=dpt.fund.transaction.export.wizard&id={self.id}&field=file_data&download=true&filename={self.file_name}',
            'target': 'self',
        }

    def action_back(self):
        """Quay lại cấu hình"""
        self.state = 'draft'
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dpt.fund.transaction.export.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
        }

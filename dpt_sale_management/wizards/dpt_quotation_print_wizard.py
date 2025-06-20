# -*- coding: utf-8 -*-
import base64
import io
import openpyxl
import os
from openpyxl import Workbook
from openpyxl.styles import Font, Border, Side, Alignment, PatternFill
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.drawing.image import Image
from odoo import models, fields, api, _


class DPTQuotationPrintWizard(models.TransientModel):
    _name = 'dpt.quotation.print.wizard'
    _description = 'Print Quotation Wizard'

    type = fields.Selection([
        ('quotation_total', 'Báo giá tổng'),
        ('quotation_product', 'Báo giá theo sản phẩm'),
        ('quotation_service', 'Báo giá theo dịch vụ tầng 1'),
    ], "Loại Form Báo giá", default="quotation_total")
    sale_order_id = fields.Many2one('sale.order', 'Sales Order')

    def action_confirm_print_quotation(self):
        if self.type == 'quotation_product':
            return self.sale_order_id.export_excel_quotation_product()
        if self.type == 'quotation_total':
            return self.sale_order_id.export_excel_quotation_total()
        if self.type == 'quotation_service':
            return self.sale_order_id.export_excel_quotation_service()


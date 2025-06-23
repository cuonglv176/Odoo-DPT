# -*- coding: utf-8 -*-
{
    'name': "Phân bổ chi phí (XHĐ)",
    'summary': "Quản lý và phân bổ chi phí từ Đơn mua hàng (PO) vào Tờ khai",
    'description': """
        Module cho phép tính toán và phân bổ chi phí từ các đơn mua hàng (PO)
        vào giá vốn của các dòng trên tờ khai xuất nhập khẩu.
        
        Tính năng chính:
        - Liên kết đơn mua hàng với tờ khai
        - Phân bổ chi phí theo tỷ lệ giá trị tờ khai
        - Theo dõi lịch sử phân bổ
        - Báo cáo và phân tích chi phí phân bổ
    """,
    'author': "DPT",
    'website': "https://dpt.com.vn",
    'category': 'Accounting',
    'version': '17.0.1.0.0',
    'depends': ['base', 'dpt_purchase_management', 'dpt_export_import', 'account', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/purchase_order_views.xml',
        'views/cost_allocation_views.xml',
        'views/menu_views.xml',
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'sequence': 25,
}
{
    'name': 'DPT Fund Management',
    'version': '17.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Quản lý quỹ tiền mặt VN và TQ',
    'description': """
        Module quản lý quỹ tiền mặt cho DPT:
        - Quản lý tài khoản quỹ VN và TQ
        - Giao dịch thu chi quỹ
        - Chuyển tiền giữa các quỹ
        - Quản lý tỷ giá hối đoái
        - Kiểm kê quỹ định kỳ
    """,
    'author': 'DPT Company',
    'website': 'https://dpt.vn',
    'depends': ['base', 'account', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'views/fund_account_views.xml',
        'views/fund_transaction_views.xml',
        'views/fund_transfer_views.xml',
        'views/exchange_rate_views.xml',
        'views/fund_audit_views.xml',
        'views/pending_transfer_views.xml',
        # 'views/fund_dashboard_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}

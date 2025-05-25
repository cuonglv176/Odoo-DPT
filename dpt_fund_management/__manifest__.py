{
    'name': 'Fund Management',
    'version': '17.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Quản lý quỹ VN và TQ với tỷ giá',
    'description': """
        Module quản lý quỹ bao gồm:
        - Quản lý quỹ VN và TQ
        - Quy đổi tiền tệ
        - Kiểm kê quỹ
        - Theo dõi tiền đang chuyển
        - Quản lý tỷ giá
    """,
    'depends': ['base', 'account', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'data/account_data.xml',
        'data/ir_cron_data.xml',
        'views/fund_account_views.xml',
        'views/fund_transaction_views.xml',
        'views/fund_transfer_views.xml',
        'views/exchange_rate_views.xml',
        'views/fund_audit_views.xml',
        'views/pending_transfer_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}

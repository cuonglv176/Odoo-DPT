{
    'name': "Base District",
    'name_vi_VN': "Quận/Huyện",

    'summary': """
Districts management
""",
    'summary_vi_VN': """
Quản lý quận/huyện""",

    'description': """
What it does
============
The module provides districts management features.

Key Features
============
* Districts management
* Set up data district of Vietnam
    
Supported Editions
==================
1. Community Edition
2. Enterprise Edition

    """,

    'description_vi_VN': """
Mô đun này làm gì
=================
Phân hệ cung cấp các tính năng về quản lý quận/huyện.

Tính năng nổi bật
=================
* Quản lý quận/huyện
* Tạo sẵn dữ liệu quận/huyện của Việt Nam
    
Ấn bản được Hỗ trợ
==================
1. Ấn bản Community
2. Ấn bản Enterprise

    """,

    'author': "DPT",
    'website': "https://DPT.com",
    'live_test_url': "https://v13demo-int.erponline.vn",
    'live_test_url_vi_VN': "https://v13demo-vn.erponline.vn",
    'support': "apps.support@DPT.com",
    'category': 'Tools',
    'version': '0.1.0',
    'depends': ['base'],

    'data': [
        'data/res.country.district.csv',
        'security/ir.model.access.csv',        
        'views/res_country_district_views.xml',
        'views/res_partner_views.xml'
        ],

    'installable': True,
    'application': False,
    'auto_install': False,
    'price': 99.9,
    'currency': 'EUR',
    'license': 'OPL-1',
}

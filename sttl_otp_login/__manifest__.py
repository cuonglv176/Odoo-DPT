# -*- coding: utf-8 -*-
{
    "name": "Email OTP Authentication",
    "version": "17.0.1.0",
    "author": "Silver Touch Technologies Limited",
    'category': 'Tools',
    "website": "https://www.silvertouch.com/",
    "description": """
        """,
    "summary": """
        This module allows the user authentication of the database via OTP.
    """,
    'depends': ['base', 'mail', 'web', 'website', 'auth_signup'],
    'data': [
        "security/ir.model.access.csv",
        "security/security_group.xml",
        "views/otp_verification.xml",
        "views/login_view.xml",
        "views/otp_signup.xml",
        "data/cron.xml"
    ],
    "price": 0,
    "currency": "USD",
    "license": "LGPL-3",
    'installable': True,
    'application': False,
    'images': ['static/description/banner.png']
}
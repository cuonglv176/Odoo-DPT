# pylint: disable=missing-docstring
# Copyright 2016 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Web Notify",
    "summary": """
        Send notification messages to user""",
    "depends": ["web", "bus", "base", "mail"],
    "assets": {
        'web.assets_backend': [
            "ev_web_notify/static/src/js/services/notification.esm.js",
            "ev_web_notify/static/src/js/services/notification_services.esm.js",
        ]
    },
    "demo": ["views/res_users_demo.xml"],
    "installable": True,
}

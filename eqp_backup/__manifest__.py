{
    "name": "Automatic Backup",
    "summary": "Automates Odoo DB/filestore backups, allowing users to schedule and manage routine backups effortlessly.",
    "description": """
        The EQP Automatic Backup module for Odoo 17 simplifies data protection by automating database and filestore
        backups. Users can easily schedule routine backups and choose from various destinations such as local servers,
        SFTP, Google Drive, and Dropbox.
        The module offers configurable email notifications for specific processes, including independent settings for
        successful and failed backups.
        Efficient storage management is ensured by allowing users to set the number of retained backups, providing
        automated maintenance of the specified quantity of the most recent backups. With EQP Automatic Backup,
        users enjoy a streamlined and user-friendly solution for securing their Odoo data.
    """,
    "version": "17.0.4.0",
    "category": "Tools",
    "license": "LGPL-3",
    "images": ["static/description/eqp_backup.gif"],
    "author": "EQP Solutions",
    "website": "https://www.eqpsolutions.com/",
    "contributors": [
        "Esteban Quevedo <esteban.quevedo@eqpsolutions.com>",
    ],
    "depends": ["base", "mail"],
    "data": [
        "security/eqp_backup_security.xml",
        "security/ir.model.access.csv",
        "data/mail_template_data.xml",
        "wizard/backup_dropbox_token_assignment_wizard_views.xml",
        "views/res_config_settings_views.xml",
        "views/backup_record_views.xml",
        "views/backup_server_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "eqp_backup/static/src/**/*",
        ],
    },
    "demo": [],
    "installable": True,
    "application": False,
    "auto_install": False,
}

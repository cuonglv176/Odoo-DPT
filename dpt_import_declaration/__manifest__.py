{
    "name": "Import Declaration Module",
    "version": "17.0.1.0.0",
    "category": "Custom",
    "summary": "Import trade declaration data from Excel files",
    "description": """
        Module for importing trade declaration data from Excel files.
        Features:
        - Import Excel files with validation
        - Save data to related models (Buyer, Seller, Ports, Brands, etc.)
        - Log import history
        - Handle duplicate data
    """,
    "author": "Your Company",
    "website": "https://yourcompany.com",
    "depends": ["base", "contacts"],
    "data": [
        "security/ir.model.access.csv",
        "views/import_history_views.xml",
        "views/import_wizard_views.xml",
        "views/menu_views.xml",
        "views/port_brand_views.xml",
    ],
    "installable": True,
    "application": True,
    "license": "LGPL-3",
}

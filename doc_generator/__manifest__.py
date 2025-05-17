{
    "name": "Doc Generator",
    "category": "Document",
    "description": """
        Doc Generator
    """,
    "version": "1.0",
    "author": "TTMinh",
    "website": "",
    "description": "",
    "depends": ["base", "docx_report_pro", "mail", "documents"],
    "data": [
        "data/ir_actions_report.xml",
        "security/security.xml",
        "security/ir.model.access.csv",
        # "wizards/document_existed_update.xml",
        # "views/document_folder.xml",
        # "views/documents_document.xml",
        "views/doc_generator_markup.xml",
        "views/doc_generator_template.xml",
        "views/doc_generator_template_submit_wizard.xml",
        "views/doc_generator_template_generate_wizard.xml",
    ],
    "demo": [],
    "installable": True,
    "application": True,
}

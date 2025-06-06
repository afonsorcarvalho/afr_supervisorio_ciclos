{
    'name': 'Supervisório Ciclos',
    'version': '16.0.1.0.0',
    'category': 'Manufacturing',
    'summary': 'Módulo para gerenciamento de ciclos',
    'description': """
        Módulo para gerenciamento de ciclos.
        Permite visualizar e analisar dados de ciclos.
    """,
    'author': 'Engenapp',
    'website': 'https://www.engenapp.com.br',
    'depends': [
        'base',
        'engc_os',
        'mail',
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/supervisorio_groups.xml",
        "data/supervisorio_manager_data.xml",
        "views/res_config_settings_views.xml",
        "views/authenticity_check_views.xml",
        "views/cycle_features_views.xml",
        "views/cycle_type_views.xml",
        "views/equipments_views.xml",
        "views/menu_views.xml",
        "views/supervisorio_ciclos_views.xml",
        "reports/report_txt_to_pdf.xml",
    ],
    'assets': {
        'web.assets_backend': [
            'afr_supervisorio_ciclos/static/src/js/ace_editor.js',
            'afr_supervisorio_ciclos/static/src/xml/ace_editor.xml',
            'afr_supervisorio_ciclos/static/src/css/style.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
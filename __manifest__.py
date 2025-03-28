{
    'name': 'Supervisorio ciclos',
    'version': '1.0',
    'description': 'Supervisório de ciclos de equipamento para CME',
    'summary': '',
    'sequence':'0',
    'author': 'Eng. Afonso Carvalho',
    'website': '',
    'license': 'LGPL-3',
    'category': 'Others',
    'depends': [
        'base','engc_os'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/cycle_type_views.xml',
        'views/supervisorio_ciclos_views.xml',
        'views/equipments_views.xml',
        'views/menu_views.xml',
    ],
    'demo': [
       
    ],
    'auto_install': False,
    'application': True,
    'assets': {
        'web.assets_backend': [
            'afr_supervisorio_ciclos/static/src/js/supervisorio_ciclos_tree.js',
        ],
    }
}
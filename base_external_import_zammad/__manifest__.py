# -*- coding: utf-8 -*-

{
    'name': 'Import data from external data sources. Versión para Zammad',
    'version': '1.5',
    'category': 'Tools',
    'description': """
Import data directly from Zammad.

Installed in the Bytacora Helpdesk module, menu Settings -> Technical -> Database Structure
    """,
    'author': "Nahuel Costa Cortez",
	'images':[
        'static/description/snapshot1.png',
    ],
	'depends': [
		'helpdesk_bytacora',
        'base',
        'base_external_dbsource',
    ],
    'data': [
        'views/base_external_import_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [
        #'demo/base_external_import_demo.xml',
    ],
    'test': [],
    'installable': True,
    'active': False,
}

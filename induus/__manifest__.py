# -*- coding: utf-8 -*-
{
    'name': "induus",

    'summary': """""",

    'author': "Ingetive",
    'website': "http://ingetive.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '14.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': [
        'base',
        'web',
        'purchase',
        'sale',
        'stock',
        'l10n_es',
        'l10n_es_partner',
        'account',
        'contacts',
        'sale_stock',
        'sale_margin',
        'sale_purchase',
        'account_payment_partner',
        'delivery',
        'crm',
        'stock_picking_invoice_link',
        'account_due_list',
        'board',
        'l10n_es_partner',
        'google_calendar',
        'utm',
        'account_invoice_extract',
        'account_payment_order',
        'mass_mailing',
        'account_payment_sale',
        'documents',
        'base_address_extended',
               ],

    # always loaded
    'data': [
        'security/portal_security.xml',
#         'security/ir.model.access.csv',
#         #'data/product.xml',
#         #'data/hr_expense.xml',
        'data/mail.xml',
#         'data/mail_activity.xml',
        'data/sale.xml',
        'data/induus_equipo.xml',
        'data/induus_zona.xml',
#         'data/res_partner.xml',
        'data/utm.xml',
        'data/documents.xml',
#         'data/website_crm.xml',
        'report/induus_report.xml',
#         'report/purchase.xml',
        'report/sale.xml',
#         'report/stock_picking.xml',
#         'report/account.xml',
#         'report/product_product.xml',
#         'report/product_template.xml',
        'data/report_layout.xml',
        'views/induus_proyecto_detalle.xml',
        'views/induus_plantilla_proyecto_detalle.xml', # error
        'views/induus_plantilla_proyecto_editor.xml', # error
         'views/sale_order.xml', #campos
        'views/account.xml', # error
        'views/menu_stock.xml',
        'views/web.xml',
        'views/res_company.xml',
        'views/mail.xml',
#         'views/analytic_account.xml', # comentado
        'views/purchase_order.xml',
        'views/account_move.xml', # campos
        'views/account_fiscal_position.xml',
        'views/account_invoice_supplier.xml', # campos
        'views/res_partner.xml', # error
#         'views/product_template.xml', # comentado
        'views/product_product.xml',
        'views/product_category.xml',
        'views/product_supplierinfo.xml',
        'views/induus_referencia_cliente.xml',
        'views/induus_zona.xml',
        'views/base.xml',
        'views/stock.xml',
        'views/stock_picking.xml', # error
        'views/crm_lead.xml', # error
        'views/delivery_carrier.xml',
        'views/payment_view.xml',
        'views/induus_ventas_producto.xml', # error
        'views/induus_equipo.xml',
        'views/induus_genei_envio.xml',
        'views/board.xml',
        'views/documents.xml',
        'views/account_bank_statement.xml',
        'views/mail_tracking_email.xml',
        'views/mail_activity.xml',
        'templates/assets.xml',
#         'templates/portal.xml',
        'templates/mass_mailing.xml',
        'templates/payment.xml',
# #         'templates/website_sale.xml',
# #         'templates/website_crm.xml',
        'templates/sale.xml',
# #         'templates/website_sale_delivery.xml',
# #         'templates/website_legal_page.xml',
# #         'templates/website_cookie_notice.xml',
        'templates/auth_signup.xml',
        'wizard/sale_order_lost.xml',
        'wizard/induus_generar_envio.xml',
        'wizard/induus_anadir_envio.xml',
        'wizard/induus_importar_envio.xml',
        'wizard/induus_dias_cobro.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}

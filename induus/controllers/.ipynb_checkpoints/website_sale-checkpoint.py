# -*- coding: utf-8 -*-
# © 2017 Ingetive - <info@ingetive.com>

import logging

from odoo import fields, http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale

_logger = logging.getLogger(__name__)


class WebsiteSaleInduus(WebsiteSale):

    def _get_mandatory_billing_fields(self):
        res = super(WebsiteSaleInduus, self)._get_mandatory_billing_fields()
        res.append('zip')
        res.append('vat')
        res.append('zona_id')
        return res

    def _get_mandatory_shipping_fields(self):
        res = super(WebsiteSaleInduus, self)._get_mandatory_shipping_fields()
        res.append('zip')
        res.append('zona_id')
        return res

    @http.route(['/shop/product/<model("product.template"):product>'], type='http', auth="public", website=True)
    def product(self, product, category='', search='', **kwargs):
        return super(WebsiteSaleInduus, self).product(product, category, search, **kwargs)

    @http.route(['/product_configurator/get_combination_info_website'], type='json', auth="public", methods=['POST'], website=True)
    def get_combination_info_website(self, product_template_id, product_id, combination, add_qty, **kw):
        res = super(WebsiteSaleInduus, self).get_combination_info_website(product_template_id, product_id, combination, add_qty, **kw)
        product = request.env['product.product'].sudo().search([('id', '=', res['product_id'])], limit=1)

        if product:
            code_pais = 'ES'
            partner_current = request.env.context.get('partner')
            if partner_current:
                addr = partner_current.address_get(['delivery'])
                if addr['delivery']:
                    delivery = request.env['res.partner'].sudo().browse(addr['delivery'])
                    if delivery and delivery.country_id:
                        code_pais = delivery.country_id.code

            res.update({'fecha_entrega': product.sudo().delay_website(add_qty, 'string', code_pais)})
        else:
            res.update({'fecha_entrega': ''})
        return res

    @http.route(auth="user")
    def checkout(self, **post):
        return super(WebsiteSaleInduus, self).checkout(**post)

    def _checkout_form_save(self, mode, checkout, all_values):
        if mode[0] == 'new':
            checkout.update({'validar_campos': False})
        return super(WebsiteSaleInduus, self)._checkout_form_save(mode, checkout, all_values)

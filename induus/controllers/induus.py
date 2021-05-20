# -*- coding: utf-8 -*-
# © 2018 Ingetive - <info@ingetive.com>

import logging

from odoo import http
from odoo.http import Controller, route, request

_logger = logging.getLogger(__name__)


class Induus(http.Controller):

    @http.route(['/contact_form_json'], type='json', auth='none', cors='*', csrf=False)
    def contact_form_json(self, name, email_from, phone, description=None, empresa=None, country_code=None, **post):
        values = {
            "type": "opportunity",
            "name": name,
            "contact_name": name,
            "email_from": email_from,
            "phone": phone,
            "description": description,
            "empresa": empresa,
            'medium_id': request.env.ref("induus.utm_medium_website_external").id,
        }

        if country_code:
            country = request.env['res.country'].search([('code', '=ilike', country_code)], limit=1)
            if country:
                values.update({'country_id': country.id})

        opp = request.env['crm.lead'].sudo().create(values)

        if opp:
            return {"id": opp.id, "resultado": "OPP creada correctamente."}
        else:
            return {"id": None, "resultado": "Error al crear el OPP."}

    @http.route(['/newsletter/order/<int:order_id>/add'], type='json', auth='none', cors='*', csrf=False)
    def add_newsletter_order(self, order_id, anadir_suscripcion, **post):
        order = request.env['sale.order'].sudo().search([('id', '=', order_id)], limit=1)
        if order:
            order.write({'anadir_suscripcion': anadir_suscripcion})
        return True

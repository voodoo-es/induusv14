# -*- coding: utf-8 -*-
# © 2019 Ingetive - <info@ingetive.com>

import logging
from odoo import http, _
from odoo.http import Controller, route, request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AuthSignupHomeInduus(AuthSignupHome):

    def _signup_with_values(self, token, values):
        values.update({
            'property_payment_term_id': request.env.ref("account.account_payment_term_immediate").id,
            'validar_campos': False,
            'property_product_pricelist': 2 # es la tarifa 'TARIFA WEB'
        })
        res = super(AuthSignupHomeInduus, self)._signup_with_values(token, values)
        country = request.env['res.country'].sudo().search([('id', '=', request.params.get('country_id'))], limit=1)
        if not country:
            raise UserError(_("The form was not properly filled in."))
        user_sudo = request.env['res.users'].sudo().search([('login', '=', values.get('login'))])
        if user_sudo and user_sudo.partner_id:
            # 1-> Regimen nacional ; 3-> Regimen extracomunitario
            user_sudo.partner_id.write({
                'country_id': country.id,
                'property_account_position_id': 1 if country.code == 'ES' else 3
            })
            user_sudo.partner_id.write({'property_product_pricelist': 2})
        return res

# -*- coding: utf-8 -*-
# © 2018 Ingetive - <info@ingetive.com>

import logging
from email.utils import getaddresses

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Lead(models.Model):
    _inherit = 'crm.lead'

    zona_id = fields.Many2one(related="partner_id.zona_id", store=True)
    crear_actividad = fields.Boolean('Crear actividad')
    empresa = fields.Char('Empresa')
    type = fields.Selection(default='opportunity')
    cntc_newletter = fields.Boolean('Acepta recibir publicidad')

    @api.model
    def create(self, vals):
        medium_website = self.env.ref("utm.utm_medium_website")
        medium_website_external = self.env.ref("induus.utm_medium_website_external")

        # cuando viene de la website odoo poner como comercial a Marc
        if vals.get('medium_id') == medium_website.id:
            vals.update({
                'user_id': 7, # Usuario Marc
                'team_id': 10 # Equipo de ventas "Ecommerce"
            })
        elif vals.get('medium_id') == medium_website_external.id:
            vals.update({
                'team_id': 5 # Equipo de ventas "Web coorporativa"
            })

        email_list = None
        if vals.get('email_from'):
            email_list = getaddresses([vals.get('email_from').strip()])
            vals.update({'email_from': email_list[0][1]})

        if not vals.get('desde_email') and not vals.get('team_id'):
            vals.update({
                'team_id': 11  # Equipo de ventas "Cliente Habitual"
            })

        res = super(Lead, self).create(vals)

        medium_email = self.env.ref("utm.utm_medium_email")
        if vals.get('desde_email'):
            res.write({
                'medium_id': medium_email.id,
                'team_id': 5  # Equipo de ventas "Web coorporativa"
            })


        if not res.partner_id and res.medium_id and \
            res.medium_id.id in [medium_email.id, medium_website.id, medium_website_external.id]:
            partner = self.env['res.partner'].search([('email', '=', res.email_from)], limit=1)

            partner_lang = 'es_ES'
            partner_country_id = None
            if res.country_id:
                partner_lang = 'en_US'
                partner_country_id = res.country_id.id
                lang = self.env['res.lang'].search(['|',
                    ('active', '=', True),
                    ('active', '=', False),
                    ('code', '=', 'es_%s' % res.country_id.code)
                ], limit=1)
                
                if lang:
                    partner_lang = lang.code
                      
            empresa = None
            if res.empresa:
                empresa = self.env['res.partner'].sudo().search([('name', '=', res.empresa)], limit=1)
                if not empresa:
                    empresa = self.env['res.partner'].sudo().with_context(partner_no_validation=True).create({
                        'name': res.empresa,
                        'is_company': True,
                        'country_id': partner_country_id,
                        'lang': partner_lang,
                        'sale_order_team_id': res.team_id.id if res.team_id else None
                    })

            if not partner:
                values_partner = {
                    'type': 'contact',
                    'validar_campos': False,
                    'is_company': (res.empresa),
                    'property_payment_term_id': self.env.ref("account.account_payment_term_immediate").id,
                    'property_product_pricelist': 108, # Tarifa nuevos clientes
                    'country_id': partner_country_id,
                    'lang': partner_lang,
                    'sale_order_team_id': res.team_id.id if res.team_id else None
                }

                if res.medium_id.id == medium_email.id:
                    values_partner.update({'name': email_list and email_list[0][0] or res.email_from})
                elif res.medium_id.id in [medium_website.id, self.env.ref("induus.utm_medium_website_external").id]:
                    values_partner.update({'name': res.contact_name or res.email_from or res.name})
                    if res.phone:
                        values_partner.update({'phone': res.phone})

                if res.email_from:
                    values_partner.update({'email': res.email_from})

                if empresa:
                    values_partner.update({'parent_id': empresa.id})

                partner = self.env['res.partner'].sudo().create(values_partner)
            else:
                if empresa:
                    partner.with_context(partner_no_validation=True).write({'parent_id': empresa.id})

            res.write({'partner_id': partner.id})

        if res.cntc_newletter:
            email = None
            contact_name = None
            if res.partner_id:
                email = res.partner_id.email
                contact_name = res.partner_id.name

            if not email:
                email = res.email_from

            if not contact_name:
                contact_name = res.contact_name

            MailingContact = self.env['mail.mass_mailing.contact'].sudo()
            contact = MailingContact.search([
                ('email', '=', email),
                ('list_ids', 'in', [1])
            ])
            if not contact:
                MailingContact.create({
                    'name': contact_name,
                    'email': email,
                    'list_ids': [(4, 1)]
                })

        return res

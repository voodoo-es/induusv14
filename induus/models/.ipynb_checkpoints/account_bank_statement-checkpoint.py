# -*- coding: utf-8 -*-
# © 2021 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"
    
    def rellenar_empresas_lineas(self):
        contactos = self.env['res.partner'].search([])
        for r in self:
            for line in r.line_ids:
                if not line.name or line.partner_id:
                    continue
                
                for contacto in contactos:
                    if not contacto.name or len(contacto.name) <= 4:
                        continue
                        
                    nombre_contacto = contacto.name.lower()
                    line_name = line.name.lower()
                    
                    if line_name.find(nombre_contacto) > -1:
                        line.write({'partner_id': contacto.id})
                        break
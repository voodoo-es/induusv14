# -*- coding: utf-8 -*-
# © 2018 Ingetive - <info@ingetive.com>

import logging
import json

from odoo import http
from odoo.http import Controller, route, request

_logger = logging.getLogger(__name__)


class BankStatementLine(http.Controller):
    @http.route(['/api/v1/account.bank.statement.line'], type='http', auth='api_key')
    def listado_account_move_line(self, offset=0, limit=1000000, **kwargs):
        domain=[]
        
        if limit:
            limit = int(limit)
            
        if offset:
            offset = int(offset)        
            
        lines = request.env['account.bank.statement.line'].sudo().with_context(lang="es_ES").search(domain, offset=offset, limit=limit)
        data = []
        for line in lines:
            data.append(self.get_values_line(line))

        return request.make_response(json.dumps(data), headers=[('Content-Type', 'application/json')])
    
    def get_values_line(self, line):
        values = {
            'id': line.id,
            'fecha': line.date.strftime("%d/%m/%Y") if line.date else '',
            'referencia': line.ref or '/',
            'etiqueta': line.name or '',
            'empresa': line.partner_id.name or '',
            'importe': line.amount or 0,
            'extracto': line.statement_id.name or False,
            'banco': line.journal_id.name or ''
        }
        
        return values
        
        
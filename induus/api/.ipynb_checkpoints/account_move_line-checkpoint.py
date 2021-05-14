# -*- coding: utf-8 -*-
# © 2018 Ingetive - <info@ingetive.com>

import logging
import json

from odoo import http
from odoo.http import Controller, route, request

_logger = logging.getLogger(__name__)


class MoveLine(http.Controller):
    @http.route(['/api/v1/account.move.line'], type='http', auth='api_key')
    def listado_account_move_line(self, offset=0, limit=1000000, **kwargs):
        domain=[]
        
        if limit:
            limit = int(limit)
            
        if offset:
            offset = int(offset)
            
        lines = request.env['account.move.line'].sudo().with_context(lang="es_ES").search(domain, offset=offset, limit=limit)
        data = []
        for line in lines:
            data.append(self.get_values_line(line))

        return request.make_response(json.dumps(data), headers=[('Content-Type', 'application/json')])
    
    def get_values_line(self, line):
        values = {
            'id': line.id,
            'fecha': line.date.strftime("%d/%m/%Y") if line.date else '',
            'asiento_contable': line.move_id.name or '',
            'diario': line.journal_id.name  or '',
            'etiqueta': line.name or '',
            'referencia': line.ref or '',
            'empresa': line.partner_id.name  or '',
            'cuenta': line.account_id.name  or '',
            'cuenta_analitica': line.analytic_account_id.name  or '',
            'etiqueta_analitica': [r.name for l in line.analytic_tag_ids],
            'asiento_conciliacion': line.full_reconcile_id.name  or '',
            'debe': line.debit or 0,
            'haber': line.credit or 0,
            'saldo_pendiente': line.balance or 0,
            'moneda_importes': line.amount_currency or 0,
            'fecha_vencimiento': line.date_maturity.strftime("%d/%m/%Y") if line.date_maturity else '',
            'importe_residual': line.amount_residual or 0,
            'treas': line.treasury_date.strftime("%d/%m/%Y") if line.treasury_date else '',
            'fp': line.treasury_planning or False,
            'prevision': line.forecast_id.name or '',
            'codigo_cuenta': line.account_id.code or ''
        }
        
        return values
        
        
# -*- coding: utf-8 -*-
# © 2018 Ingetive - <info@ingetive.com>

import logging
import json

from odoo import http
from odoo.http import Controller, route, request

_logger = logging.getLogger(__name__)


class Invoice(http.Controller):
    @http.route(['/api/v1/account.invoice'], type='http', auth='api_key')
    def listado_account_invoice(self, fecha_desde=None, fecha_hasta=None, 
                                         offset=0, limit=10000, **kwargs):
        domain=[]
        
        if fecha_desde:
            domain += [('date_invoice', '>=', fecha_desde)]
            
        if fecha_hasta:
            domain += [('date_invoice', '<=', fecha_hasta)]
            
        if limit:
            limit = int(limit)
            
        if offset:
            offset = int(offset)
        
        invoices = request.env['account.invoice'].sudo().with_context(lang="es_ES").search(domain, offset=offset, limit=limit)
        data = []
        for invoice in invoices:
            data.append(self.get_values_invoice(invoice))

        return request.make_response(json.dumps(data), headers=[('Content-Type', 'application/json')])
    
    def get_values_invoice(self, invoice):
        values = {
            'id': invoice.id,
            'fecha': invoice.date_invoice.strftime("%d/%m/%Y") if invoice.date_invoice else '',
            'fecha_vencimiento': invoice.date_due.strftime("%d/%m/%Y") if invoice.date_due else '',
            'nombre': invoice.number or '',
            'referencia': invoice.name or '',
            'estado': invoice.state or '',
            'equipo_ventas': invoice.team_id.name if invoice.team_id else '',
            'origin': invoice.origin or '',
            'termino_pago': invoice.payment_term_id.name if invoice.payment_term_id else '',
            'modo_pago': invoice.payment_mode_id.name if invoice.payment_mode_id else '',
            'tipo': invoice.type,
            'ref_pago': invoice.reference,
            'subtotal': invoice.amount_untaxed,
            'impuestos': invoice.amount_tax,
            'total': invoice.amount_total,
            'residual': invoice.residual,
            'beneficio_analitico': invoice.margen_analitico,
            'margen_analitico': invoice.margen_analitico_porcentaje,
            'beneficio': invoice.margin,
            'margen': invoice.margin_porcentaje
        }
        
        return values
        
        
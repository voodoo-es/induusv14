# -*- coding: utf-8 -*-
# © 2018 Ingetive - <info@ingetive.com>

import logging
import json

from odoo import http
from odoo.http import Controller, route, request

_logger = logging.getLogger(__name__)

class AnalyticAccount(http.Controller):
    @http.route(['/api/v1/account.analytic.account'], type='http', auth='api_key')
    def listado_account_analytic_account(self, fecha_desde=None, fecha_hasta=None, 
                                         offset=0, limit=10000, **kwargs):
        domain=[]
        
        if fecha_desde:
            domain += [('invoice_date_invoice', '>=', fecha_desde)]
            
        if fecha_hasta:
            domain += [('invoice_date_invoice', '<=', fecha_hasta)]
            
        if limit:
            limit = int(limit)
            
        if offset:
            offset = int(offset)
        
        analytics = request.env['account.analytic.account'].sudo().search(domain, offset=offset, limit=limit)
        data = []
        for analytic in analytics:
            data.append(self.get_values_analytic_account(analytic))

        return request.make_response(json.dumps(data), headers=[('Content-Type', 'application/json')])
    
    def get_values_analytic_account(self, analytic):
        values = {
            'id': analytic.id,
            'fecha_factura': analytic.invoice_date_invoice.strftime("%d/%m/%Y") if analytic.invoice_date_invoice else '',
            'cuenta_analitica': analytic.name or '',
            'cliente': analytic.partner_id.name,
            'nombre_factura': analytic.invoice_name or '',
            'coste': analytic.coste_margenes,
            'venta': analytic.venta_margenes,
            'beneficio': analytic.beneficio,
            'margen': analytic.margen,
            'fecha_vencimiento': analytic.invoice_date_due.strftime("%d/%m/%Y") if analytic.invoice_date_due else '',
            'estado': analytic.invoice_state or '',
        }
        
        return values
        
        
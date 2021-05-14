# -*- coding: utf-8 -*-
# © 2018 Ingetive - <info@ingetive.com>

import logging
import json

from odoo import http
from odoo.http import Controller, route, request

_logger = logging.getLogger(__name__)


class SaleOrderAPI(http.Controller):
    @http.route(['/api/v1/sale.order'], type='http', auth='api_key')
    def listado_sale_order(self, fecha_desde=None, fecha_hasta=None, offset=0, 
                           pedidos='0', limit=10000, **kwargs):
        domain=[]
        
        if fecha_desde:
            domain += [('date_order', '>=', fecha_desde)]
            
        if fecha_hasta:
            domain += [('date_order', '<=', fecha_hasta)]

        if pedidos == '1':
            domain += [('state', 'not in', ('draft', 'sent', 'cancel'))]
        elif pedidos == '2':
            domain += [('state', 'in', ('draft', 'sent', 'cancel'))]
            
        if limit:
            limit = int(limit)
            
        if offset:
            offset = int(offset)
        
        orders = request.env['sale.order'].sudo().search(domain, offset=offset, limit=limit)
        data = []
        for order in orders:
            data.append(self.get_values_order(order))

        return request.make_response(json.dumps(data), headers=[('Content-Type', 'application/json')])
        
    def get_values_order(self, order):  
        values = {
            'id': order.id,
            'fecha': order.date_order.strftime("%d/%m/%Y"),
            'fecha_confirmacion': order.confirmation_date.strftime("%d/%m/%Y") if order.confirmation_date else '',
            'pedido': order.name,
            'empresa': order.partner_id.parent_id.name if order.partner_id.parent_id else order.partner_id.name,
            'cliente': order.partner_id.name,
            'descripcion': order.note or '',
            'coste': order.coste,
            'venta': order.amount_untaxed,
            'portes': order.delivery_price or 0,
            'iva': order.amount_tax,
            'total_venta': order.amount_total,
            'beneficio': order.margin,
            'margen': order.margin_porcentaje,
            'forma_pago': order.payment_mode_id.name if order.payment_mode_id else '',
            'estado_pedido': order.state or '',
            'estado_factura': order.invoice_status or '',
            'cuenta_analitica': order.analytic_account_id.name or '',
            'coste_analitico': order.analytic_account_id.coste_margenes if order.analytic_account_id else 0,
            'coste_analitico_sin_portes': order.analytic_account_id.coste_margenes_sin_portes if order.analytic_account_id else 0,
            'coste_analitico_portes': order.analytic_account_id.coste_margenes_portes if order.analytic_account_id else 0,
            'beneficio_analitico':  order.margen_analitico,
            'ref_clinete': order.client_order_ref or '',
            'equipo_ventas': order.team_id.name if order.team_id else '',
            'es_pedido': 1 if order.state == 'sale' else 0,
            'linea_negocio': order.linea_negocio,
            'prueba': order.prueba,
            'no_facturar_auto': order.no_facturar_auto,
            'comercial': order.user_id.name if order.user_id else '',
            'facturas': []
        }
        
        return values
        
        
# -*- coding: utf-8 -*-
# Copyright 2019 Adrián del Río <a.delrio@ingetive.com>

import logging
import unidecode

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class DiasCobro(models.TransientModel):
    _name = 'induus.dias_cobro'
    _description = 'Días de cobro'
    
    fecha_inicio = fields.Date("Fecha inicio", default=fields.Date.today, required=True)
    fecha_fin = fields.Date("Fecha fin", default=fields.Date.today, required=True)
    partner_id = fields.Many2one("res.partner", string="Contacto")
    linea_ids = fields.One2many('induus.dias_cobro_linea', 'dia_cobro_id')
    
#     @api.multi
    def open_wizard(self, context=None):
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'context': context,
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
        }
    
    def buscar_pedidos(self):
        self.ensure_one()
        self.linea_ids.unlink()
        domain = [
            ('date_order', '>=', self.fecha_inicio),
            ('date_order', '<=', self.fecha_fin),
        ]
        
        if self.partner_id:
            domain += [('partner_id', '=', self.partner_id.id)]
        
        orders = self.env['sale.order'].search(domain)
        for order in orders:
            fecha_pago_venta = None
            for invoice in order.invoice_ids:
                vals = invoice._get_payments_vals()
                if not vals:
                    continue
                    
                for v in vals:
                    if not fecha_pago_venta or v['date'] > fecha_pago_venta:
                        fecha_pago_venta = v['date']
            
            fecha_pago_compra = None
            for invoice in order.purchase_invoice_ids:
                vals = invoice._get_payments_vals()
                if  not vals:
                    continue

                for v in vals:
                    if not fecha_pago_compra or v['date'] > fecha_pago_compra:
                        fecha_pago_compra = v['date']
            
            if not fecha_pago_venta or not fecha_pago_compra:
                continue
            
            if order.partner_id.parent_id:
                partner_id = order.partner_id.parent_id.id
            else:
                partner_id = order.partner_id.id
            
            self.env['induus.dias_cobro_linea'].create({
                'dia_cobro_id': self.id,
                'sale_order_id': order.id,
                'partner_id': partner_id,
                'pago_venta': fecha_pago_venta.strftime("%Y-%m-%d"),
                'pago_compra': fecha_pago_compra.strftime("%Y-%m-%d"),
                'dias': (fecha_pago_venta - fecha_pago_compra).days
            })
                    
    
class LineasDiasCobro(models.TransientModel):
    _name = 'induus.dias_cobro_linea'
    _description = 'Líneas días de cobro'
    
    dia_cobro_id = fields.Many2one('induus.dias_cobro', string="Día de cobro")
    sale_order_id = fields.Many2one("sale.order", string="Pedido venta", ondelete="cascade")
    partner_id = fields.Many2one("res.partner", string="Empresa")
    pago_venta = fields.Date("Fecha pago venta")
    pago_compra = fields.Date("Fecha pago compra")
    dias = fields.Integer("Días")
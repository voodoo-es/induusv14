# -*- coding: utf-8 -*-
# Copyright 2020 Adrián del Río <a.delrio@ingetive.com>

import logging
import unidecode

from datetime import datetime, timedelta
from odoo import api, fields, models
from odoo.addons.induus.models.induus_genei import Genei
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

TIPOS_ENVIO = [
    ("cliente", "Cliente"),
    ("proveedor", "Proveedor"),
    ("actualizador", "Actualizador"),
    ("abono_transporte", "Abono transporte"),
    ("ajuste_kg_transporte", "Ajuste KG transporte"),
]


class ImportarEnvio(models.TransientModel):
    _name = 'induus.importar_envio'
    _description = 'Importar envios'

    invoice_id = fields.Many2one('account.invoice', string="Factura", required=True, ondelete="cascade")
    fecha_inicio = fields.Date('Fecha inicio', required=True, default=fields.Date.context_today)
    fecha_fin = fields.Date('Fecha fin', required=True, default=fields.Date.context_today)
    envio_ids = fields.One2many('induus.importar_envio_dato', 'importar_envios_id')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id)

    def buscar_envios(self):
        result = Genei.send("obtener_transacciones", self.company_id)
        self.envio_ids.unlink()
        for envio in result:
            fecha_creacion = datetime.strptime(envio["fecha_hora_creacion"], '%Y-%m-%d %H:%M:%S').date()
            if fecha_creacion >= self.fecha_inicio and fecha_creacion <= self.fecha_fin:
                self.env['induus.importar_envio_dato'].create({
                    'importar_envios_id': self.id,
                    'codigo_transaccion': envio['codigo_transaccion'],
                    'concepto': envio['concepto'],
                    'fecha_hora_creacion': envio['fecha_hora_creacion'],
                    'importe': float(envio['importe']) * -1
                })
        return self.open_wizard()

    def importar_envios(self):
        producto = self.env['product.product'].search([('id', '=', 105168)], limit=1) # Gastos envio
        

        data = {}
        for envio in self.envio_ids:
            if envio.codigo_envio not in data:
                data.update({envio.codigo_envio: {
                    "precio": 0.0,
                    "tipo_envio": envio.tipo_envio
                }})
            data[envio.codigo_envio]["precio"] += float(envio.importe) / 1.21

        for codigo_envio, item in data.items():
            linea = self.env['account.invoice.line'].search([
                ('invoice_id', '=', self.invoice_id.id),
                ('name', '=', codigo_envio),
            ], limit=1)
            if linea:
                continue

            if item['tipo_envio'] == 'proveedor':
                producto = self.env['product.product'].search([('default_code', '=', "Gastos envio Proveedores")], limit=1)
            elif item['tipo_envio'] == 'cliente':
                producto = self.env['product.product'].search([('default_code', '=', "Gastos envio Clientes")], limit=1)
            elif item['tipo_envio'] == 'actualizador':
                producto = self.env['product.product'].search([('default_code', '=', "IND18869")], limit=1)
            elif item['tipo_envio'] == 'abono_transporte':
                producto = self.env['product.product'].search([('default_code', '=', "IND20305")], limit=1)
            elif item['tipo_envio'] == 'ajuste_kg_transporte':
                producto = self.env['product.product'].search([('default_code', '=', "IND20305")], limit=1)
            
            if not producto:
                raise ValidationError("El producto que se utiliza no existe.")
            
            account_analytic_ids = []
            
            genei_envio = self.env['induus.genei_envio'].search([
                ('name', '=', codigo_envio),
                ('picking_ids', '!=', False)
            ], limit=1)
            
            if genei_envio:
                for picking in genei_envio.picking_ids:
                    if picking.purchase_id and picking.sale_id and picking.sale_id.analytic_account_id:
                        account_analytic_ids.append(picking.sale_id.analytic_account_id.id)
                    else:
                        lines = picking.move_ids_without_package.filtered(lambda m: m.analytic_account_id)
                        for line in lines:
                            if line.analytic_account_id.id not in account_analytic_ids:
                                account_analytic_ids.append(line.analytic_account_id.id)

            values = {
                'account_id': producto.property_account_expense_id.id if producto.property_account_expense_id else False,
                'invoice_line_tax_ids': [(6, 0, [tax.id for tax in producto.supplier_taxes_id])],
                'invoice_id': self.invoice_id.id,
                'product_id': producto.id,
                'name': codigo_envio,
                'price_unit': item['precio'],
                'quantity': 1
            }

            if account_analytic_ids:
                values.update({'price_unit': item['precio'] / len(account_analytic_ids)})
                for analytic_id in account_analytic_ids:
                    values.update({'account_analytic_id': analytic_id})
                    self.env['account.invoice.line'].create(values)
            else:
                self.env['account.invoice.line'].create(values)

        self.invoice_id.compute_taxes()

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


class ImportarEnvioDato(models.TransientModel):
    _name = 'induus.importar_envio_dato'
    _description = 'Envio'

    importar_envios_id = fields.Many2one('induus.importar_envio', string="Importar envíos", ondelete="cascade")
    codigo_transaccion = fields.Char("Código transaccion")
    concepto = fields.Char('Concepto')
    fecha_hora_creacion = fields.Char('Fecha creación')
    importe = fields.Monetary('Importe')
    currency_id = fields.Many2one('res.currency', 'Currency',
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    codigo_envio = fields.Char('Código envío', compute="_compute_codigo_envio")
    existe = fields.Boolean('Existe', compute="_compute_existe")
    tipo_envio = fields.Selection(TIPOS_ENVIO, string="Tipo de envío", compute="_compute_tipo_envio")

    @api.depends('codigo_transaccion', 'concepto')
    def _compute_codigo_envio(self):
        for r in self:
            concepto = r.concepto
            if r.concepto.find("RECTIFICACIÓN") > -1:
                r.codigo_envio = concepto.replace("RECTIFICACIÓN PARA EL ENVÍO ", "")
            elif r.concepto.find("AJUSTE EXCESO MEDIDAS CORREOSEXPRESS - ENVÍO:") > -1:
                r.codigo_envio = concepto.replace("AJUSTE EXCESO MEDIDAS CORREOSEXPRESS - ENVÍO: ", "")
            elif r.concepto.find("(ACTUALIZADOR) DEVOLUCION ENVIO") > -1:
                r.codigo_envio = concepto.replace("(ACTUALIZADOR) DEVOLUCION ENVIO ", "")
            elif r.concepto.find("-> saldo anterior") > -1:
                aux = concepto.split("->")
                if len(aux) == 2:
                    r.codigo_envio = aux[0].replace("(ACTUALIZADOR) DEVOLUCION ENVÍO ", "")
            elif r.concepto.find("ABONO Recanalización envío: ") > -1:
                r.codigo_envio = concepto.replace("ABONO Recanalización envío: ", "")    
            elif r.concepto.find("Recanalización envío:") > -1:
                r.codigo_envio = concepto.replace("Recanalización envío: ", "")    
            elif r.codigo_transaccion in r.concepto:
                r.codigo_envio = r.codigo_transaccion
            elif r.concepto.find("AJUSTE KILOS (WS)") > -1:
                try:
                    r.codigo_envio = concepto.replace("AJUSTE KILOS (WS) ", "").split()[0]
                except:
                    pass

    @api.depends('codigo_envio', 'concepto')
    def _compute_tipo_envio(self):
        for r in self:
            if  r.concepto.find("(ACTUALIZADOR) DEVOLUCION ENVIO") > -1:
                r.tipo_envio = "actualizador"
            elif r.concepto.find("AJUSTE EXCESO MEDIDAS CORREOSEXPRESS - ENVÍO:") > -1 or \
                r.concepto.find("AJUSTE KILOS (WS)") > -1:
                r.tipo_envio = "ajuste_kg_transporte"
            elif r.concepto.find("RECTIFICACIÓN") > -1:
                r.tipo_envio = "abono_transporte"
            else:
                genei_envio = self.env['induus.genei_envio'].search([
                    ('name', '=', r.codigo_envio),
                    ('sincronizado', '=', True)
                ], limit=1)
                
                if genei_envio:
                    if genei_envio.nombre_llegada in ["THE INDUUS SOLUTIONS SL", "ANTONIO FLORES"]:
                        r.tipo_envio = "proveedor"
                    else:
                        r.tipo_envio = "cliente"
                
    def _compute_existe(self):
        for r in self:
            linea = self.env['account.invoice.line'].search([
                ('invoice_id', '=', r.importar_envios_id.invoice_id.id),
                ('name', '=', r.codigo_envio),
            ], limit=1)
            r.existe = True if linea else False

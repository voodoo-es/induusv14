# -*- coding: utf-8 -*-
# Copyright 2019 Adrián del Río <a.delrio@ingetive.com>

import logging
import unidecode

from odoo import api, fields, models
from odoo.addons.induus.models.induus_genei import Genei
from datetime import timedelta

_logger = logging.getLogger(__name__)


class AnadirEnvio(models.TransientModel):
    _name = 'induus.anadir_envio'
    _description = 'Añadir Envío'

    picking_id = fields.Many2one('stock.picking', string="Albarán", required=True)
    envio_ids = fields.Many2many('induus.genei_envio', domain=[('sincronizado', '=', True)])
    envio_genei_ids = fields.One2many('induus.envio_desde_genei', 'anadir_envio_id')
    fecha_inicio = fields.Date('Fecha inicio', required=True, default=fields.Date.context_today)
    fecha_fin = fields.Date('Fecha fin', required=True, default=fields.Date.context_today)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id)

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

    def buscar_envios(self):
        params = {
            'fecha_inicio': self.fecha_inicio.strftime('%Y-%m-%d'),
            'fecha_fin': (self.fecha_fin + timedelta(days=1)).strftime('%Y-%m-%d'),
        }

        result = Genei.send("obtener_lista_envios_fecha", self.company_id, params)
        self.envio_ids.unlink()
        for envio in result:
            self.env['induus.envio_desde_genei'].create({
                'anadir_envio_id': self.id,
                'codigo_envio': envio['codigo_envio'],
                'direccion_llegada': unidecode.unidecode(envio['direccion_llegada']),
                'fecha_hora_creacion': envio['fecha_hora_creacion'],
                'id_usuario': envio['id_usuario'],
                'direccion_salida': unidecode.unidecode(envio['direccion_salida']),
                'id_agencia': envio['id_agencia'],
                'importe_total': envio['importe_total']
            })
        return self.open_wizard()

    def anadir_envio_existente(self):
        self.ensure_one()
        if self.envio_ids:
            envio_ids = self.envio_ids.ids
            if self.picking_id.gene_envio_ids:
                envio_ids += self.picking_id.gene_envio_ids.ids

            self.picking_id.write({'gene_envio_ids': [(6, 0, envio_ids)]})

    def anadir_envio_desde_genei(self):
        self.ensure_one()
        EnvioGenei = self.env['induus.genei_envio']
        for envio in self.envio_genei_ids.filtered(lambda x: x.para_importar):
            envio_genei = EnvioGenei.search([('name', '=', envio.codigo_envio)], limit=1)
            if not envio_genei:
                envio_genei = EnvioGenei.create({
                    'resultado_text': "Envío creado con código %s" % envio.codigo_envio,
                    'id_agencia': envio.id_agencia,
                    'sincronizado': True
                })

            if envio_genei:
                self.picking_id.write({'gene_envio_ids': [(4, envio_genei.id)]})


class EnvioDesdeGenei(models.TransientModel):
    _name = 'induus.envio_desde_genei'
    _description = 'Envío Genei'

    anadir_envio_id = fields.Many2one('induus.anadir_envio', string="Envíos de genei", ondelete="cascade")
    codigo_envio = fields.Char("Código")
    direccion_llegada = fields.Html('Dirección de llegada')
    fecha_hora_creacion = fields.Char('Fecha creación')
    id_usuario = fields.Char('ID usuario')
    direccion_salida = fields.Html('Dirección salida')
    id_agencia = fields.Char('ID agencia')
    importe_total = fields.Monetary('Importe')
    currency_id = fields.Many2one('res.currency', 'Currency',
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    para_importar = fields.Boolean('Seleccionar')

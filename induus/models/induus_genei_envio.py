# -*- coding: utf-8 -*-
# © 2019 Ingetive - <info@ingetive.com>

import logging

from odoo import api, fields, models, _
from odoo.addons.induus.models.induus_genei import Genei
from datetime import date
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class GeneiEnvio(models.Model):
    _name = "induus.genei_envio"
    _description = "Envíos"

    name = fields.Char('Código Genei', compute="_compute_name", store=True)
    valor_mercancia = fields.Boolean('Valor mercancía')
    contenido_envio = fields.Boolean('Contenido envío')
    contrareembolso = fields.Boolean('Contrareembolso')
    seguro = fields.Boolean('Seguro')
    importe_seguro = fields.Boolean('Importe seguro')
    dropshipping = fields.Boolean('Dropshipping')
    codigos_origen = fields.Char('Códigos origen')
    poblacion_salida = fields.Char('Población salida')
    iso_pais_salida = fields.Char('ISO País salida')
    direccion_salida = fields.Char('Dirección salida')
    email_salida = fields.Char('Email salida')
    nombre_salida = fields.Char('Nombre salida')
    telefono_salida = fields.Char('Teléfono salida')
    dni_salida = fields.Char('DNI salida')
    codigos_destino = fields.Char('Códigos destino')
    poblacion_llegada = fields.Char('Población llegada')
    iso_pais_llegada = fields.Char('ISO País llegada')
    direccion_llegada = fields.Char('Dirección llegada')
    telefono_llegada = fields.Char('Teléfono llegada')
    email_llegada = fields.Char('Email llegada')
    nombre_llegada = fields.Char('Nombre llegada')
    dni_llegada = fields.Char('DNI llegada')
    observaciones_salida = fields.Text('Observaciones salida')
    contacto_salida = fields.Char('Contacto salida')
    observaciones_llegada = fields.Text('Observaciones llegaa')
    contacto_llegada = fields.Char('Contacto llegada')
    codigo_mercancia = fields.Char('Código mercancia')
    recoger_tienda = fields.Boolean('Recoger tienda')
    cod_promo = fields.Char('Código promocional')
    select_oficinas_destino = fields.Char('Oficinas destino')
    fecha_recogida = fields.Char('Fecha recogida')
    hora_recogida_desde = fields.Char('Hora recogida desde')
    hora_recogida_hasta = fields.Char('Hora recogida hasta')
    unidad_correo = fields.Char('Unidad de correo')
    codigo_envio_servicio = fields.Char('Código envío servicio')
    id_agencia = fields.Char('ID agencia')
    name_agencia = fields.Char('Nombre agencia')
    imagen_agencia = fields.Char('Imagen agencia')
    codigo_seguimiento = fields.Char('Código seguimiento')
    bulto_ids = fields.One2many('induus.genei_bulto', 'envio_id', ondelete="cascade")
    picking_ids = fields.Many2many('stock.picking', string="Albaranes")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id)
    sincronizado = fields.Boolean("Sincronizado")
    resultado_text = fields.Char('Resultado sincronización')
    referencia_cliente = fields.Char('Referencia cliente')
    codigo_etiqueta = fields.Char("Código etiqueta")
    url_etiqueta = fields.Char("Etiqueta", compute="_compute_url_etiqueta")

    _sql_constraints = [
        ('codigo_envio_servicio_uniq', 'unique (codigo_envio_servicio)', "El código de servicio ya existe."),
    ]

    @api.depends('resultado_text')
    def _compute_name(self):
        texto = "Envío creado con código"
        for r in self:
            name = None
            if r.resultado_text and r.resultado_text.find(texto) >= 0:
                name = r.resultado_text.replace(texto, '').replace(" ", "")
            r.update({'name': name})

    @api.depends("codigo_etiqueta")
    def _compute_url_etiqueta(self):
        for r in self:
            if r.codigo_etiqueta:
                r.url_etiqueta = "https://www.genei.es/recursos/etiquetas/%s" % r.codigo_etiqueta
            else:
                r.url_etiqueta = None
            
    def generar(self):
        for r in self:
            fecha_recogida, horarios = r.horarios_agencia()

            hora_recogida_desde = None
            for k, v in list(reversed(list(sorted(horarios['inicial'].items()))))[0:2]:
                hora_recogida_desde = v

            hora_recogida_hasta = None
            for k, v in list(reversed(list(sorted(horarios['final'].items()))))[0:2]:
                hora_recogida_hasta = v
            
            observaciones_llegada = ""
            if r.dni_llegada:
                observaciones_llegada = "CIF  %s" % r.dni_llegada

            if r.observaciones_llegada:
                observaciones_llegada = " %s" % r.observaciones_llegada

            observaciones_salida = ""
            if r.dni_salida:
                observaciones_salida = "CIF %s" % r.dni_salida

            if r.observaciones_salida:
                observaciones_salida = " %s" % r.observaciones_salida

            params = {
                "codigo_envio_servicio": r.codigo_envio_servicio,
                "valor_mercancia": 0,
                "contenido_envio": ", ",
                "contrareembolso": 0,
                "cantidad_reembolso": 0,
                "seguro": 0,
                "importe_seguro": 0,
                "dropshipping": 0,
                "codigos_origen": r.codigos_origen,
                "poblacion_salida": r.poblacion_salida,
                "iso_pais_salida": r.iso_pais_salida,
                "direccion_salida": r.direccion_salida,
                "email_salida": r.email_salida,
                "nombre_salida": r.nombre_salida,
                "telefono_salida": r.telefono_salida,
                "codigos_destino": r.codigos_destino,
                "poblacion_llegada": r.poblacion_llegada,
                "iso_pais_llegada": r.iso_pais_llegada,
                "direccion_llegada": r.direccion_llegada,
                "telefono_llegada": r.telefono_llegada,
                "email_llegada": r.email_llegada,
                "nombre_llegada": r.nombre_llegada,
                "contacto_llegada": r.contacto_llegada,
                "dni_llegada": r.dni_llegada,
                "observaciones_llegada": observaciones_llegada,
                "observaciones_salida": observaciones_salida,
                "id_agencia": r.id_agencia,
                "fecha_recogida": fecha_recogida.strftime("%d/%m/%Y"),
                "hora_recogida_desde": hora_recogida_desde,
                "hora_recogida_hasta": hora_recogida_hasta,
                'array_bultos': [[],],
                "dia_laborable_automatico": 1
            }

            if r.referencia_cliente:
                params.update({"referencia_cliente": r.referencia_cliente})

            if r.contacto_salida:
                params.update({"contacto_salida": r.contacto_salida})

            if r.contacto_llegada:
                params.update({"contacto_llegada": r.contacto_llegada})

            for bulto in r.bulto_ids:
                params['array_bultos'].append({
                    "peso": bulto.peso,
                    "largo": bulto.largo,
                    "ancho": bulto.ancho,
                    "alto": bulto.alto,
                    "contenido": "",
                    "taric": "",
                    "dni_contenido": "",
                    "valor": ""
                })

            _logger.warning(params)
            result = Genei.send("crear_envio", r.company_id, params)

            if result and 'resultado' in result:
                if result['resultado'] == "1" or result['resultado'] == "6":
                    self.sincronizado = True
                    self.obtener_codigo_envio()
                else:
                    self.sincronizado = False
                self.resultado_text = result['resultado_text']

    def horarios_agencia(self, fecha_recogida=None):
        if not fecha_recogida:
            fecha_recogida = date.today()

        params = {
            "id_agencia": self.id_agencia,
            "cp_salida": self.codigos_origen,
            "iso_pais_salida": self.iso_pais_salida,
            "fecha_recogida": fecha_recogida.strftime("%d/%m/%Y")
        }

        result = Genei.send("obtener_lista_horarios_disponibles_agencia", self.company_id, params)

        if not result:
            fecha_recogida_sig = fecha_recogida + relativedelta(days=1)
            return self.horarios_agencia(fecha_recogida_sig)
        return fecha_recogida, result
    
    def obtener_codigo_envio(self):
        self.ensure_one()
        if not self.name:
            return
        params = {"codigo_envio_plataforma": self.name}
        result = Genei.send("obtener_codigo_envio", self.company_id, params)
        if result['nombre_agencia']:
            self.write({
                'name_agencia': result['nombre_agencia'],
                'codigo_seguimiento': result['seguimiento'],
            })

    def action_etiqueta(self):
        self.ensure_one()
        if not self.name:
            return None
        params = {"codigo_envio": self.name}
        result = Genei.send("obtener_etiquetas_envio", self.company_id, params)
        codigo = None
        if result and result['url_etiqueta']:
            codigo = result['url_etiqueta']
        self.write({'codigo_etiqueta': codigo})

        
class GeneiBultos(models.Model):
    _name = "induus.genei_bulto"
    _description = "Bultos"

    peso = fields.Integer('Peso')
    largo = fields.Integer('Largo')
    ancho = fields.Integer('Ancho')
    alto = fields.Integer('Alto')
    contenido = fields.Integer('Contenido')
    taric = fields.Integer('Taric')
    dni_contenido = fields.Integer('DNI contenido')
    valor = fields.Integer('Valor')
    envio_id = fields.Many2one('induus.genei_envio', string="Envío", required=True, ondelete="cascade")


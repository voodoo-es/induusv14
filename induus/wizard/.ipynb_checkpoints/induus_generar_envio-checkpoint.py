# -*- coding: utf-8 -*-
# Copyright 2019 Adrián del Río <a.delrio@ingetive.com>

import logging

from odoo import api, fields, models
from odoo.addons.induus.models.induus_genei import Genei
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class GeneiBultoWizard(models.TransientModel):
    _name = 'induus.genei_bulto_wizard'
    _description = 'Bultos Genei'

    generar_envio_id = fields.Many2one('induus.generar_envio', string="Bulto")
    peso = fields.Integer('Peso (kg)')
    largo = fields.Integer('Largo (cm)')
    ancho = fields.Integer('Ancho (cm)')
    alto = fields.Integer('Alto (cm)')
    suma_dimensiones = fields.Integer('Suma dimensiones')
    volumen = fields.Float('Volumen')


class InduusBultoWizard(models.TransientModel):
    _name = 'induus.induus_bulto_wizard'
    _description = 'Bultos Induus'

    generar_envio_id = fields.Many2one('induus.generar_envio', string="Bulto")
    peso = fields.Integer('Peso (kg)', default=1)
    largo = fields.Integer('Largo (cm)', default=30)
    ancho = fields.Integer('Ancho (cm)', default=15)
    alto = fields.Integer('Alto (cm)', default=10)
    suma_dimensiones = fields.Integer('Suma dimensiones')
    volumen = fields.Float('Volumen')


class GenerarEnvio(models.TransientModel):
    _name = 'induus.generar_envio'
    _description = 'Generar Envío'

    picking_ids = fields.Many2many('stock.picking', string="Albarán", required=True)
    agencia_ids = fields.One2many('induus.generar_envio_agencia', 'generar_envio_id')
    nombre_pais_origen = fields.Char('País origen')
    nombre_pais_destino = fields.Char('País destino')
    nombre_provincia_origen = fields.Char('Provincia origen')
    nombre_provincia_destino = fields.Char('Provincia destino')
    poblacion_salida = fields.Char('Población origen')
    poblacion_entrega = fields.Char('Población destino')
    num_paquetes = fields.Integer('Número de paquetes')
    bulto_ids = fields.One2many('induus.generar_envio_bulto', 'generar_envio_id')
    induus_bulto_ids = fields.One2many('induus.induus_bulto_wizard', 'generar_envio_id')
    genei_bulto_ids = fields.One2many('induus.genei_bulto_wizard', 'generar_envio_id')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id)
    recogida_proveedor = fields.Boolean('Recogida en proveedor')
    codigos_origen = fields.Char("Códigos origen", compute="_compute_direcciones")
    provincia_salida = fields.Char("Provincia salida", compute="_compute_direcciones")
    iso_pais_salida = fields.Char("ISO País salida", compute="_compute_direcciones")
    direccion_salida = fields.Char("Dirección salida", compute="_compute_direcciones")
    nombre_salida = fields.Char("Nombre salida", compute="_compute_direcciones")
    contacto_salida = fields.Char("Contact salida", compute="_compute_direcciones")
    telefono_salida = fields.Char("Teléfono salida", compute="_compute_direcciones")
    email_salida = fields.Char("Email salida", compute="_compute_direcciones")
    dni_salida = fields.Char("DNI salida", compute="_compute_direcciones")
    codigos_destino = fields.Char("Códigos destino", compute="_compute_direcciones")
    poblacion_llegada = fields.Char("Población llegada", compute="_compute_direcciones")
    provincia_llegada = fields.Char("Provincia llegada", compute="_compute_direcciones")
    iso_pais_llegada = fields.Char("ISO País llegada", compute="_compute_direcciones")
    direccion_llegada = fields.Char("Dirección llegada", compute="_compute_direcciones")
    nombre_llegada = fields.Char("Nombre llegada", compute="_compute_direcciones")
    contacto_llegada = fields.Char("Contacto llegada", compute="_compute_direcciones")
    telefono_llegada = fields.Char("Teléfono llegada", compute="_compute_direcciones")
    email_llegada = fields.Char("Email llegada", compute="_compute_direcciones")
    dni_llegada = fields.Char("DNI llegada", compute="_compute_direcciones")

    @api.constrains('picking_ids')
    def _check_picking_ids(self):
        for r in self:
            partner_id = None
            for picking in r.picking_ids:
                if not partner_id:
                    partner_id = picking.partner_id.id

                if partner_id != picking.partner_id.id:
                    raise ValidationError('Todos los albaranes tiene que tener el mismo Cliente/Proveedor.')

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

    @api.depends('recogida_proveedor', 'picking_ids')
    def _compute_direcciones(self):
        for r in self:
            if not r.picking_ids:
                continue

            company = r.company_id
            picking_id = r.picking_ids[0]
            if r.recogida_proveedor:
                codigos_salida = picking_id.genei_codigos_origen_proveedor
                poblacion_salida = picking_id.genei_poblacion_proveedor
                provincia_salida = picking_id.genei_provincia_proveedor
                iso_pais_salida = picking_id.genei_iso_pais_proveedor
                direccion_salida = picking_id.genei_direccion_proveedor
                email_salida = picking_id.genei_email_proveedor
                nombre_salida = picking_id.genei_nombre_proveedor
                contacto_salida = picking_id.genei_contacto_proveedor
                telefono_salida = picking_id.genei_telefono_proveedor
                dni_salida = picking_id.genei_dni_proveedor
                codigos_destino = company.genei_codigos_origen
                poblacion_llegada = company.genei_poblacion
                provincia_llegada = company.genei_provincia
                iso_pais_llegada = company.genei_iso_pais
                direccion_llegada = company.genei_direccion
                telefono_llegada = company.genei_telefono
                email_llegada = company.genei_email
                nombre_llegada = company.genei_nombre
                contacto_llegada = company.genei_contacto
                dni_llegada = company.vat
            else:
                codigos_salida = company.genei_codigos_origen
                poblacion_salida = company.genei_poblacion
                provincia_salida = company.genei_provincia
                iso_pais_salida = company.genei_iso_pais
                direccion_salida = company.genei_direccion
                email_salida = company.genei_email
                nombre_salida = company.genei_nombre
                contacto_salida = company.genei_contacto
                telefono_salida = company.genei_telefono
                dni_salida = company.vat
                codigos_destino = picking_id.genei_codigos_origen_cliente
                poblacion_llegada = picking_id.genei_poblacion_cliente
                provincia_llegada = picking_id.genei_provincia_cliente
                iso_pais_llegada = picking_id.genei_iso_pais_cliente
                direccion_llegada = picking_id.genei_direccion_cliente
                telefono_llegada = picking_id.genei_telefono_cliente
                email_llegada = picking_id.genei_email_cliente
                nombre_llegada = picking_id.genei_nombre_cliente
                contacto_llegada = picking_id.genei_contacto_cliente
                dni_llegada = picking_id.genei_dni_cliente

            r.update({
                'codigos_origen': codigos_salida,
                'poblacion_salida': poblacion_salida,
                'provincia_salida': provincia_salida,
                'iso_pais_salida': iso_pais_salida,
                'codigos_destino': codigos_destino,
                'poblacion_llegada': poblacion_llegada,
                'provincia_llegada': provincia_llegada,
                'iso_pais_llegada': iso_pais_llegada,
                'direccion_salida': direccion_salida,
                'email_salida': email_salida,
                'nombre_salida': nombre_salida,
                'contacto_salida': contacto_salida,
                'telefono_salida': telefono_salida,
                'direccion_llegada': direccion_llegada,
                'telefono_llegada': telefono_llegada,
                'email_llegada': email_llegada,
                'nombre_llegada': nombre_llegada,
                'contacto_llegada': contacto_llegada,
                'dni_llegada': dni_llegada,
                'dni_salida': dni_salida,
            })

    def datos_iniciales(self):
        for picking in self.picking_ids:
            self.env['induus.induus_bulto_wizard'].create({
                'generar_envio_id': self.id,
                'peso': picking.peso,
                'largo': picking.largo,
                'ancho': picking.ancho,
                'alto': picking.alto,
            })

    def buscar_precios(self):
        self.ensure_one()
        if not self.direccion_llegada or not self.codigos_origen or  not self.poblacion_llegada or \
            not self.provincia_llegada or not self.iso_pais_llegada:
            raise ValidationError("El código postal, ciudad, provincia y país de la dirección de envío son obligatorios.")

        bultos = [[]]
        for bulto in self.induus_bulto_ids:
            bultos.append({
                "peso": bulto.peso,
                "largo": bulto.largo,
                "ancho": bulto.ancho,
                "alto": bulto.alto
            })

        params = {
            "array_bultos": bultos,
            "codigos_origen": self.codigos_origen,
            "poblacion_salida": self.poblacion_salida,
            "iso_pais_salida": self.iso_pais_salida,
            "codigos_destino": self.codigos_destino,
            "poblacion_llegada": self.poblacion_llegada,
            "iso_pais_llegada": self.iso_pais_llegada,
            "cod_promo": "",
        }

        result = Genei.send("obtener_listado_agencias_precios", self.company_id, params)
        if result:
            datos_vista = result['datos_vista']

            self.update({
                'nombre_pais_origen': datos_vista['nombre_pais_origen'],
                'nombre_pais_destino': datos_vista['nombre_pais_destino'],
                'nombre_provincia_origen': datos_vista['nombre_provincia_origen'],
                'nombre_provincia_destino': datos_vista['nombre_provincia_entrega'],
                'poblacion_salida': datos_vista['poblacion_salida'],
                'poblacion_entrega': datos_vista['poblacion_entrega'],
                'num_paquetes': datos_vista['num_paquetes'],
            })

            self.genei_bulto_ids.unlink()
            if datos_vista['bultos']:
                for key, bulto in datos_vista['bultos'].items():
                    self.env['induus.genei_bulto_wizard'].create({
                        'generar_envio_id': self.id,
                        'peso': bulto['peso_%s' % key],
                        'largo': bulto['largo_%s' % key],
                        'ancho': bulto['ancho_%s' % key],
                        'alto': bulto['alto_%s' % key],
                        'suma_dimensiones': bulto['suma_dimensiones'],
                        'volumen': bulto['volumen'],
                    })

            self.agencia_ids.unlink()
            if result['datos_agencia2']:
                for key, agencia in result['datos_agencia2'].items():
                    seleccionado = False
                    if agencia['id_agencia'] == str(self.picking_ids[0].partner_id.agencia_genei_id):
                        seleccionado = True
                        
                    self.env['induus.generar_envio_agencia'].create({
                        'generar_envio_id': self.id,
                        'id_agencia': agencia['id_agencia'],
                        'importe': agencia['importe'],
                        'iva': agencia['iva'],
                        'iva_exento': False if agencia['iva_exento'] == "0" else True,
                        'nombre_agencia': agencia['nombre_agencia'],
                        'imagen_agencia': "https://www.genei.es/%s" % agencia['imagen_agencia'],
                        'num_bultos': agencia['num_bultos'],
                        'envio_seleccionado': seleccionado
                    })

        return self.open_wizard()

    def crear_envio(self):
        self.ensure_one()
        agencia = None
        for a in self.agencia_ids:
            if a.envio_seleccionado and agencia:
                raise UserError("Solo se puede seleccionar una agencia de envío.")
            
            if a.envio_seleccionado:
                agencia = a
        
        codigo_envio_servicio = ",".join([p.name for p in self.picking_ids])

        if self.picking_ids:
            genei_envio_count = self.env['induus.genei_envio'].search_count([
                ('picking_ids', 'in', self.picking_ids.ids)
            ])

            if genei_envio_count > 0:
                codigo_envio_servicio += " - %s" % genei_envio_count

        refs_cliente = []
        for p in self.picking_ids.filtered(lambda pi: pi.ref_cliente_sale_order):
            refs_cliente.append(p.ref_cliente_sale_order)
        referencia_cliente = ", ".join(refs_cliente)

        observaciones_salida = ''
        for picking in self.picking_ids:
            if picking.sale_id and picking.sale_id.name:
                if observaciones_salida:
                    observaciones_salida += "\n"
                observaciones_salida += picking.sale_id.name

        envio = self.env['induus.genei_envio'].create({
            'picking_ids': [(4, p.id) for p in self.picking_ids],
            'codigo_envio_servicio': codigo_envio_servicio,
            "valor_mercancia": 0,
            "contenido_envio": ", ",
            "contrareembolso": 0,
            "cantidad_reembolso": 0,
            "seguro": 0,
            "importe_seguro": 0,
            "dropshipping": 0,
            "codigos_origen": self.codigos_origen,
            "poblacion_salida": self.poblacion_salida,
            "iso_pais_salida": self.iso_pais_salida,
            "direccion_salida": self.direccion_salida,
            "email_salida": self.email_salida,
            "nombre_salida": self.nombre_salida,
            "contacto_salida": self.contacto_salida,
            "telefono_salida": self.telefono_salida,
            "dni_salida": self.dni_salida,
            "observaciones_salida": observaciones_salida,
            "codigos_destino": self.codigos_destino,
            "poblacion_llegada": self.poblacion_llegada,
            "iso_pais_llegada": self.iso_pais_llegada,
            "direccion_llegada": self.direccion_llegada,
            "telefono_llegada": self.telefono_llegada,
            "email_llegada": self.email_llegada,
            "nombre_llegada": self.nombre_llegada,
            "contacto_llegada": self.contacto_llegada,
            "dni_llegada": self.dni_llegada,
            "id_agencia": agencia.id_agencia,
            'imagen_agencia': agencia.imagen_agencia,
            'referencia_cliente': referencia_cliente
        })

        for bulto in self.genei_bulto_ids:
            self.env['induus.genei_bulto'].create({
                'envio_id': envio.id,
                "peso": bulto.peso,
                "largo": bulto.largo,
                "ancho": bulto.ancho,
                "alto": bulto.alto,
            })

        envio.generar()


class GenerarEnvioBulto(models.TransientModel):
    _name = 'induus.generar_envio_bulto'
    _description = 'Bultos'

    generar_envio_id = fields.Many2one('induus.generar_envio', string="Bulto", required=True)


class GenerarEnvioAgencia(models.TransientModel):
    _name = 'induus.generar_envio_agencia'
    _description = 'Agencias'
    _rec_name = "nombre_agencia"
    order = "importe, id"

    generar_envio_id = fields.Many2one('induus.generar_envio', string="Bulto", required=True)
    id_agencia = fields.Integer('ID Agencia')
    importe = fields.Monetary('Importe')
    importe_sin_iva = fields.Monetary('Importe (Sin IVA)', compute="_compute_importe_sin_iva")
    nombre_agencia = fields.Char('Agencia')
    imagen_agencia = fields.Char('Imagen agencia')
    num_bultos = fields.Integer('Número de bultos')
    company_id = fields.Many2one(related="generar_envio_id.company_id")
    currency_id = fields.Many2one('res.currency', 'Currency', default=lambda self: self.env.user.company_id.currency_id.id, required=True)
    envio_seleccionado = fields.Boolean('Selecciona')
    iva_exento = fields.Boolean("IVA Exento")
    iva = fields.Float('IVA')

    @api.depends('importe', 'iva', 'iva_exento')
    def _compute_importe_sin_iva(self):
        for r in self:
            if r.iva_exento:
                r.importe_sin_iva = r.importe
            else:
                r.importe_sin_iva = r.importe / ((r.iva/100) + 1)

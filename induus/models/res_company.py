# -*- coding: utf-8 -*-
# © 2019 Ingetive - <info@ingetive.com>

from odoo import api, fields, models, tools, _


class Company(models.Model):
    _inherit = "res.company"

    genei_usuario = fields.Char('Usuario')
    genei_pass = fields.Char('Contraseña')
    genei_nombre = fields.Char('Nombre')
    genei_contacto = fields.Char('Contacto')
    genei_telefono = fields.Char('Teléfono')
    genei_direccion = fields.Char('Dirección')
    genei_email = fields.Char('Email ')
    genei_codigos_origen = fields.Char('C.P.')
    genei_poblacion = fields.Char('Población')
    genei_provincia = fields.Char('Provincia')
    genei_iso_pais = fields.Char('ISO Páis')
    secuencia_productos = fields.Integer("Secuencia productos")

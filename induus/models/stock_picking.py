# -*- coding: utf-8 -*-
# © 2019 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = 'stock.picking'

    gene_envio_ids = fields.Many2many('induus.genei_envio')
    peso = fields.Integer('Peso (kg)', default=1)
    largo = fields.Integer('Largo (cm)', default=30)
    ancho = fields.Integer('Ancho (cm)', default=15)
    alto = fields.Integer('Alto (cm)', default=10)

    genei_nombre_company = fields.Char(related="company_id.genei_nombre")
    genei_contacto_company = fields.Char(related="company_id.genei_contacto")
    genei_telefono_company = fields.Char(related="company_id.genei_telefono")
    genei_direccion_company = fields.Char(related="company_id.genei_direccion")
    genei_email_company = fields.Char(related="company_id.genei_email")
    genei_codigos_origen_company = fields.Char(related="company_id.genei_codigos_origen")
    genei_poblacion_company = fields.Char(related="company_id.genei_poblacion")
    genei_provincia_company = fields.Char(related="company_id.genei_provincia")
    genei_iso_pais_company = fields.Char(related="company_id.genei_iso_pais")
    genei_dni_company = fields.Char(related="company_id.vat")

    genei_nombre_cliente = fields.Char("Nombre  ", compute="_compute_genei")
    genei_contacto_cliente = fields.Char("Contacto  ", compute="_compute_genei")
    genei_telefono_cliente = fields.Char("Teléfono  ", compute="_compute_genei")
    genei_direccion_cliente = fields.Char("Dirección  ", compute="_compute_genei")
    genei_email_cliente = fields.Char("Email  ", compute="_compute_genei")
    genei_codigos_origen_cliente = fields.Char("C.P.  ", compute="_compute_genei")
    genei_poblacion_cliente = fields.Char("Población  ", compute="_compute_genei")
    genei_provincia_cliente = fields.Char("Provincia  ", compute="_compute_genei")
    genei_iso_pais_cliente = fields.Char("ISO País  ", compute="_compute_genei")
    genei_dni_cliente = fields.Char('DNI ', compute="_compute_genei")

    genei_nombre_proveedor = fields.Char("Nombre ", compute="_compute_genei")
    genei_contacto_proveedor = fields.Char("Contacto ", compute="_compute_genei")
    genei_telefono_proveedor = fields.Char("Teléfono ", compute="_compute_genei")
    genei_direccion_proveedor = fields.Char("Dirección ", compute="_compute_genei")
    genei_email_proveedor = fields.Char("Email  ", compute="_compute_genei")
    genei_codigos_origen_proveedor = fields.Char("C.P. ", compute="_compute_genei")
    genei_poblacion_proveedor = fields.Char("Población ", compute="_compute_genei")
    genei_provincia_proveedor = fields.Char("Provincia ", compute="_compute_genei")
    genei_iso_pais_proveedor = fields.Char("ISO País ", compute="_compute_genei")
    genei_dni_proveedor = fields.Char('DNI', compute="_compute_genei")

    no_facturar_auto = fields.Boolean('No facturar automáticamente')
    sale_order_origin = fields.Char("adf")
    ref_cliente_sale_order = fields.Char('Referencia cliente', compute="_compute_ref_cliente_sale_order")
    proyecto_id = fields.Many2one('sale.order', string="Proyecto")

    @api.depends('sale_id', 'purchase_id')
    def _compute_ref_cliente_sale_order(self):
        for r in self:
            if r.sale_id:
                r.ref_cliente_sale_order = r.sale_id.client_order_ref
            elif r.purchase_id:
                orders = r.purchase_id.sale_order_ids.filtered(lambda o: o.client_order_ref)
                r.ref_cliente_sale_order = ", ".join([order.client_order_ref for order in orders])

    @api.depends('sale_id', 'partner_id')
    def _compute_genei(self):
        for r in self:
            partner = r.partner_id

            if partner.parent_id:
                nombre = partner.parent_id.name
                contacto = partner.name
            else:
                nombre = partner.name
                contacto = ''

            values = {
                'genei_nombre_proveedor': nombre,
                'genei_contacto_proveedor': contacto,
                'genei_telefono_proveedor': partner.phone,
                'genei_direccion_proveedor': partner.street,
                'genei_email_proveedor': partner.email,
                'genei_codigos_origen_proveedor': partner.zip,
                'genei_poblacion_proveedor': partner.city,
                'genei_provincia_proveedor': partner.state_id.name if partner.state_id else None,
                'genei_iso_pais_proveedor': partner.country_id.code if partner.country_id else None,
                'genei_dni_proveedor': partner.vat,
                'genei_nombre_cliente': nombre,
                'genei_contacto_cliente': contacto,
                'genei_telefono_cliente': partner.phone,
                'genei_direccion_cliente': partner.street,
                'genei_email_cliente': partner.email,
                'genei_codigos_origen_cliente': partner.zip,
                'genei_poblacion_cliente': partner.city,
                'genei_provincia_cliente': partner.state_id.name if partner.state_id else None,
                'genei_iso_pais_cliente': partner.country_id.code if partner.country_id else None,
                'genei_dni_cliente': partner.vat,
            }

            r.update(values)

#     @api.multi
    def crear_recogida_desde_induus(self):
        return self.open_wizard_precio_envio(False)

#     @api.multi
    def crear_recogida_desde_cliente(self):
        return self.open_wizard_precio_envio(True)

#     @api.multi
    def open_wizard_precio_envio(self, recogida_proveedor):
        wizard = self.env['induus.generar_envio'].create({
            'picking_ids': [(6, 0, self.ids)],
            'recogida_proveedor': recogida_proveedor
        })
        wizard.datos_iniciales()
        wizard.buscar_precios()
        return wizard.open_wizard()

    def anadir_envio(self):
        self.ensure_one()
        wizard = self.env['induus.anadir_envio'].create({'picking_id': self.id})
        return wizard.open_wizard()

    def action_picking_group_id_tree(self):
        action = self.env.ref('stock.action_picking_tree_all').read()[0]
        action['domain'] = [('group_id', '=', self.group_id.id)]
        return action

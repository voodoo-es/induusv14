# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class PlantillaProyecto(models.Model):
    _name = "induus.plantilla_proyecto"
    _description = "Plantillas proyectos"

    name = fields.Char('Nombre plantilla', required=True)
    proyecto_detalle_ids = fields.One2many('induus.plantilla_proyecto_detalle', 'plantilla_proyecto_id')
    sale_order_ids = fields.One2many('sale.order', 'plantilla_proyecto_detalle_id')


class PProyectoDetalle(models.Model):
    _name = "induus.plantilla_proyecto_detalle"
    _description = "Plantillas detalles proyectos"
    _order = "sequence,id"

    sequence = fields.Integer('Secuencia')
    name = fields.Char('Nombre')
    unidades = fields.Float('Unidades', default=1)
    plantilla_proyecto_id = fields.Many2one('induus.plantilla_proyecto', string="Plantilla", required=True,
                                            ondelete="cascade")
    linea_ids = fields.One2many('induus.plantilla_proyecto_detalle_linea', 'proyecto_detalle_id')

    def mostrar_lineas(self):
        self.ensure_one()
        view_form_id = self.env.ref('induus.induus_plantilla_proyecto_detalle_short_lineas_form').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'views': [[view_form_id, 'form']],
            'target': 'new',
        }


class PProyectoDetalleLinea(models.Model):
    _name = "induus.plantilla_proyecto_detalle_linea"
    _description = "Plantillas detalles proyectos linea"

    proyecto_detalle_id = fields.Many2one('induus.plantilla_proyecto_detalle', string="Proyecto detalle",
                                          required=True, ondelete="cascade")
    product_id = fields.Many2one('product.product', string="Producto")
    product_ref = fields.Char('Ref. Producto')
    partner_id = fields.Many2one("res.partner", domain=[('supplier', '=', True)], string="Proveedor")
    descripcion = fields.Char('Descripción de elementos')
    unidades = fields.Float('Unidades', default=1)
    pvp = fields.Monetary('PVP')
    coste = fields.Monetary('Coste unitario')
    subtotal = fields.Monetary('Coste total', compute="_compute_subtotal", store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True,
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    cantidad_producto = fields.Float(string='Cantidad disponible', related='product_id.qty_available', readonly=True)
    cantidad_prevista = fields.Float(string='Cantidad prevista', related='product_id.virtual_available', readonly=True)
    beneficio = fields.Monetary('Margen')
    beneficio_porcentaje = fields.Float('Margen(%)')

    @api.onchange('pvp', 'coste')
    def _onchange_pvp_coste(self):
        for r in self:
            beneficio = r.pvp - r.coste
            if r.pvp and not r.coste:
                beneficio_porcentaje = 100
            elif r.pvp and r.coste:
                beneficio_porcentaje = (beneficio * 100) / r.coste
            else:
                beneficio_porcentaje = 0

            r.update({
                'beneficio': beneficio,
                'beneficio_porcentaje': beneficio_porcentaje
            })

    @api.onchange('beneficio_porcentaje')
    def _onchange_beneficio_porcentaje(self):
        for r in self:
            beneficio = (r.coste * r.beneficio_porcentaje) / 100
            r.update({'pvp': r.coste + beneficio})

    @api.onchange('beneficio')
    def _onchange_beneficio(self):
        for r in self:
            pvp = r.coste + r.beneficio
            r.update({'pvp': pvp})

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for r in self:
            if r.product_id:
                values = {
                    'product_ref': r.product_id.default_code,
                    'pvp': r.product_id.list_price,
                    'descripcion': r.product_id.name
                }

                if not r.unidades:
                    values.update({'unidades': 1})

                if r.product_id.seller_ids:
                    values.update({
                        'partner_id': r.product_id.seller_ids[0].name,
                        'coste': r.product_id.seller_ids[0].price,
                    })
                else:
                    values.update({
                        'coste': r.product_id.standard_price
                    })

                r.update(values)

    @api.depends('unidades', 'coste')
    def _compute_subtotal(self):
        for r in self:
            r.subtotal = r.unidades * r.coste

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for r in self:
            if r.partner_id and r.product_id:
                seller = self.env['product.supplierinfo'].search([
                    ('product_tmpl_id', '=', r.product_id.product_tmpl_id.id),
                    ('name', '=', r.partner_id.id),
                ], limit=1)

                if seller:
                    r.update({'coste': seller.price})



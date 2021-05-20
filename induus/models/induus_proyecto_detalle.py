# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ProyectoDetalle(models.Model):
    _name = "induus.proyecto_detalle"
    _description = "Detalles proyecto"
    _order = "sequence,id"

    sequence = fields.Integer('Secuencia')
    name = fields.Char('Nombre')
    sale_order_id = fields.Many2one('sale.order', string="Pedido de venta")
    coste = fields.Monetary('Coste unitario', compute="_compute_totales", store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True,
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    unidades = fields.Float('Unidades')
    total = fields.Monetary('Coste total', compute="_compute_totales", store=True)
    precio_unitario = fields.Monetary('Venta unitario', compute="_compute_totales", store=True)
    precio_venta = fields.Monetary('Venta total', compute="_compute_totales", store=True)
    linea_ids = fields.One2many('induus.proyecto_detalle_linea', 'proyecto_detalle_id', ondelete="cascade")
    margen = fields.Monetary('Margen', compute="_compute_totales")
    margen_porcentaje = fields.Float('Margen (%)', compute="_compute_totales")
    coste_real = fields.Monetary('Coste Real')

    @api.depends('unidades', 'linea_ids.subtotal')
    def _compute_totales(self):
        for r in self:
            coste = 0
            venta = 0
            for linea in r.linea_ids:
                coste += linea.subtotal
                venta += linea.venta_total

            coste_total = coste * r.unidades
            venta_total = venta * r.unidades
            beneficio = venta - coste
            beneficio_porcentaje = (beneficio * 100) / coste if coste else 100
            r.update({
                'coste': coste,
                'total': coste_total,
                'precio_unitario': venta,
                'precio_venta': venta_total,
                'margen': beneficio,
                'margen_porcentaje': beneficio_porcentaje,
            })

    def mostrar_lineas(self):
        self.ensure_one()
        view_form_id = self.env.ref('induus.induus_proyecto_detalle_short_lineas_form').id
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_type': 'form',
            'view_mode': 'form',
            'views': [[view_form_id, 'form']],
            'target': 'new',
        }

    @api.model
    def create(self, vals):
        res = super(ProyectoDetalle, self).create(vals)
        if self.env.context.get('desde_plantilla'):
            _logger.warning(vals)
        return res

#     @api.multi
    def unlink(self):
        for r in self:
            r.linea_ids.unlink()
        return super(ProyectoDetalle, self).unlink()


class ProyectoDetalleLinea(models.Model):
    _name = "induus.proyecto_detalle_linea"
    _description = "Detalles proyecto linea"
    _rec_name = "descripcion"

    proyecto_detalle_id = fields.Many2one('induus.proyecto_detalle', string="Proyecto detalle", required=True,
                                          ondelete="cascade")
    proyecto_detalle_coste = fields.Monetary('Coste unitario ', compute="_compute_proyecto_detalle", store=True)
    proyecto_detalle_unidades = fields.Float('Unidades ', compute="_compute_proyecto_detalle", store=True)
    proyecto_detalle_total = fields.Monetary('Total', compute="_compute_proyecto_detalle", store=True)
    proyecto_detalle_precio_venta = fields.Monetary('Precio venta', compute="_compute_proyecto_detalle", store=True)
    product_id = fields.Many2one('product.product', string="Producto")
    cantidad_producto = fields.Float(string='Cantidad disponible', related='product_id.qty_available', readonly=True)
    cantidad_prevista = fields.Float(string='Cantidad prevista', related='product_id.virtual_available', readonly=True)
    product_ref = fields.Char('Ref. Producto')
    partner_id = fields.Many2one("res.partner", domain=[('supplier', '=', True)], string="Proveedor")
    descripcion = fields.Char('Descripción de elementos')
    unidades = fields.Float('Unidades', default=1)
    pvp = fields.Monetary('Venta unitaria')
    venta_total = fields.Monetary('Venta total', compute="_compute_venta_total")
    coste = fields.Monetary('Coste unitario')
    subtotal = fields.Monetary('Coste total', compute="_compute_subtotal", store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, readonly=True,
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    beneficio = fields.Monetary('Margen')
    beneficio_porcentaje = fields.Float('Margen(%)')
#     account_analytic_line_ids = fields.One2many('account.analytic.line', 'proyecto_detalle_linea_id', string="Línea cuenta analítica")

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

    @api.depends('proyecto_detalle_id.coste', 'proyecto_detalle_id.unidades', 'proyecto_detalle_id.total',
                 'proyecto_detalle_id.precio_venta')
    def _compute_proyecto_detalle(self):
        for r in self:
            r.update({
                'proyecto_detalle_coste': r.proyecto_detalle_id.coste,
                'proyecto_detalle_unidades': r.proyecto_detalle_id.unidades,
                'proyecto_detalle_total': r.proyecto_detalle_id.total,
                'proyecto_detalle_precio_venta': r.proyecto_detalle_id.precio_venta,
            })

    @api.depends('unidades', 'coste')
    def _compute_subtotal(self):
        for r in self:
            r.subtotal = r.unidades * r.coste

    @api.depends('unidades', 'pvp')
    def _compute_venta_total(self):
        for r in self:
            r.venta_total = r.unidades * r.pvp

#     @api.multi
    def write(self, vals):
        res = super(ProyectoDetalleLinea, self).write(vals)
        if 'descripcion' in vals or 'unidades' in vals or 'pvp' in vals:
            self.actualizar_apuntes_analiticos()
        return res

#     @api.multi
    def unlink(self):
        for r in self:
            r.account_analytic_line_ids.unlink()
        return super(ProyectoDetalleLinea, self).unlink()

#     @api.multi
    def _prepare_procurement_values(self, group_id=False):
        self.ensure_one()
        order = self.proyecto_detalle_id.sale_order_id

        values = {
            'company_id': order.company_id,
            'group_id': group_id,
            'date_planned': order.confirmation_date,
            'route_ids': self.product_id.warehouse_id and \
                                 [(6, 0, [x.id for x in self.product_id.warehouse_id.route_ids])] or [],
            'warehouse_id': order.warehouse_id or False,
            'partner_id': order.partner_shipping_id.id,
        }
        return values

#     @api.multi
    def crear_stock_picking_proyecto(self):
        errors = []
        movimientos_creado = False
        for r in self:
            order = r.proyecto_detalle_id.sale_order_id
            if order.state != 'sale' or not r.product_id.type in ('consu', 'product'):
                continue

            group_id = order.procurement_group_id
            if not group_id:
                group_id = self.env['procurement.group'].create({
                    'name': order.name,
                    'move_type': order.picking_policy,
                    'sale_id': order.id,
                    'partner_id': order.partner_shipping_id.id,
                })
                order.procurement_group_id = group_id
            else:
                updated_vals = {}
                if group_id.partner_id != order.partner_shipping_id:
                    updated_vals.update({'partner_id': order.partner_shipping_id.id})
                if group_id.move_type != order.picking_policy:
                    updated_vals.update({'move_type': order.picking_policy})
                if updated_vals:
                    group_id.write(updated_vals)

            values = r._prepare_procurement_values(group_id=group_id)
            product_qty = r.unidades

            quant_uom = r.product_id.uom_id
            get_param = self.env['ir.config_parameter'].sudo().get_param
            if  get_param('stock.propagate_uom') != '1':
                product_qty = r.product_id.uom_id._compute_quantity(product_qty, quant_uom, rounding_method='HALF-UP')

            try:
                self.env['procurement.group'].run(r.product_id, product_qty, quant_uom,
                                                  order.partner_shipping_id.property_stock_customer,
                                                  r.descripcion,
                                                  order.name,
                                                  values)
                movimientos_creado = True
            except UserError as error:
                errors.append(error.name)

        if errors:
            raise UserError('\n'.join(errors))

        return movimientos_creado

#     @api.multi
    def actualizar_apuntes_analiticos(self):
        for r in self:
            if not r.account_analytic_line_ids:
                continue

            r.account_analytic_line_ids.write({
                'name': r.descripcion,
                'amount': r.venta_total,
                'unit_amount': r.unidades
            })

#     @api.multi
    def crear_apuntes_analiticos(self):
        for r in self:
            order = r.proyecto_detalle_id.sale_order_id

            if r.product_id and not order.analytic_account_id:
                continue

            self.env['account.analytic.line'].create({
                'account_id': order.analytic_account_id.id,
                'name': r.descripcion,
                'partner_id': order.partner_id.id,
                'amount': r.venta_total,
                'unit_amount': r.unidades,
                'proyecto_detalle_linea_id': r.id
            })

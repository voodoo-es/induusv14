# -*- coding: utf-8 -*-
# © 2018 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = 'stock.move'

    cantidad_pedido_venta = fields.Float(string='Cantidad pedido venta', related='sale_line_id.product_uom_qty', readonly=True)
    unidad_pedido_venta = fields.Char(string='Unidad pedido venta', related='sale_line_id.product_uom.name', readonly=True)
    ref_proveedor = fields.Char('Referencia Proveedor', compute="_compute_ref_proveedor")
    propagate = fields.Boolean( default=False)
    imprimir_etiqueta = fields.Boolean("Imprimir etiqueta")
    ref_cliente = fields.Char('Referencia Cliente', compute="_compute_ref_cliente")

    @api.depends('picking_id.partner_id', 'product_id')
    def _compute_ref_proveedor(self):
        for r in self:
            if r.picking_id and r.picking_id.picking_type_code == 'incoming':
                proveedor = self.env['product.supplierinfo'].search([
                    ('name', '=', r.picking_id.partner_id.id),
                    ('product_tmpl_id', '=', r.product_id.product_tmpl_id.id)
                ], limit=1)

                r.ref_proveedor = proveedor.product_code if proveedor else r.product_id.default_code
            else:
                r.ref_proveedor = None

    @api.depends('picking_id.partner_id', 'product_id')
    def _compute_ref_cliente(self):
        for r in self:
            if r.picking_id and r.picking_id.picking_type_code == 'outgoing':
                cliente = self.env['induus.referencia_cliente'].search([
                    ('partner_id', '=', r.picking_id.partner_id.id),
                    ('product_tmpl_id', '=', r.product_id.product_tmpl_id.id)
                ], limit=1)

                r.ref_cliente = cliente.name if cliente else r.product_id.default_code
            else:
                r.ref_cliente = None

    @api.model
    def create(self, vals):
        res = super(StockMove, self).create(vals)
        res.anular_stock()
        if res.product_id.type == 'product' and res.product_id.categ_id.imprimir_etiqueta:
            res.write({'imprimir_etiqueta': True})
        return res

#     @api.multi
    def write(self, vals):
        res = super(StockMove, self).write(vals)
        if vals.get('state') == 'done':
            self.anular_stock()

        if vals.get('date_expected'):
            for r in self:
                r.move_dest_ids.write({'date_expected': r.date_expected +  relativedelta(days=2)})
        return res

    def anular_stock(self):
        for r in self:
            if r.picking_id and r.product_id.type == 'product' and r.picking_id.purchase_id and \
                r.picking_id.state == 'done' and r.picking_id.purchase_id.anular_stock:
                inventory = self.env['stock.inventory'].create({
                    'name': "%s - %s" % (r.product_id.name, fields.Date.today()),
                    'filter': 'product',
                    'product_id': r.product_id.id,
                    'location_id': r.location_dest_id.id
                })

                product = r.product_id.with_context(location=r.location_dest_id.id)

                self.env['stock.inventory.line'].create({
                    'inventory_id': inventory.id,
                    'product_id': product.id,
                    'product_uom_id': product.uom_id.id,
                    'location_id': r.location_dest_id.id,
                    'theoretical_qty': product.qty_available,
                    'product_qty': product.qty_available - r.quantity_done
                })

                inventory._action_done()

#     @api.multi
    def action_toggle_imprimir_etiqueta(self):
        for r in self:
            r.imprimir_etiqueta = True if not r.imprimir_etiqueta else False

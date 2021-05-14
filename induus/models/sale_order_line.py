# -*- coding: utf-8 -*-
# © 2018 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api
from odoo.tools import float_compare
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    cantidad_producto = fields.Float(string='En stock', related='product_id.qty_available', readonly=True)
    cantidad_prevista = fields.Float(string='Prevista', related='product_id.virtual_available', readonly=True)
    referencia_cliente = fields.Char('R. Cliente', compute="_compute_referencia_cliente", store=True)
    margen = fields.Float('Margen', compute="_compute_margen", digits=(16, 2), store=True)
    beneficio = fields.Monetary('Beneficio', compute='_compute_beneficio', store=True)
    beneficio_porcentaje = fields.Float('Margen (%)', compute='_compute_beneficio', digits=(16, 2), store=True)
    equipo_id = fields.Many2one(related="order_id.equipo_id", store=True)
    equipo_serie = fields.Char(related="equipo_id.serie", store=True)
    equipo_referencia = fields.Char(related="equipo_id.referencia", store=True)
    equipo_serial = fields.Char(related="equipo_id.serial", store=True)
    equipo_eme = fields.Char(related="equipo_id.eme", store=True)
    order_effective_date = fields.Date(related="order_id.effective_date", store=True)
    fecha_prevista = fields.Date('Fecha Prevista', compute="_fecha_prevista")

    @api.onchange('product_uom_qty', 'product_uom', 'route_id')
    def _onchange_product_id_check_availability(self):
        res = super(SaleOrderLine, self)._onchange_product_id_check_availability()
        res.pop('warning', None)
        return res

    @api.depends('product_id', 'order_id.partner_id')
    def _compute_referencia_cliente(self):
        for r in self:
            partner = r.order_id.partner_id
            if partner:
                partner_ids = [partner.id]
                if partner.parent_id:
                    partner_ids.append(partner.parent_id.id)

                referencias = self.env['induus.referencia_cliente'].search([
                    ('product_tmpl_id', '=', r.product_id.product_tmpl_id.id),
                    ('partner_id', 'in', partner_ids)
                ])
                if referencias:
                    r.update({
                        'referencia_cliente': ', '.join(referencias.mapped('name')),
                    })
                    continue

            r.referencia_cliente = r.product_id.default_code

    @api.depends('price_reduce', 'price_subtotal')
    def _compute_margen(self):
        for r in self:
            if r.margin and r.price_subtotal:
                r.percent = (r.margin / r.price_subtotal) * 100
            else:
                r.percent = 0

    @api.depends('purchase_price', 'price_subtotal', 'product_uom_qty')
    def _compute_beneficio(self):
        for r in self:
            coste = r.purchase_price * r.product_uom_qty
            beneficio = r.price_subtotal - coste
            beneficio_porcentaje = (beneficio * 100) / coste if coste else 100
            r.update({
                'beneficio': beneficio,
                'beneficio_porcentaje': beneficio_porcentaje
            })

    @api.onchange('product_id', 'product_uom_qty')
    def _onchange_product_id_set_customer_lead(self):
        self.customer_lead = self.product_id.delay_website(self.product_uom_qty, "days")
        
    @api.depends('order_id.date_order', 'customer_lead')
    def _fecha_prevista(self):
        for r in self:
            if r.customer_lead > 0:
                fecha_prevista = fields.Date.from_string(r.order_id.date_order) + relativedelta(days=r.customer_lead)
            else:
                fecha_prevista = r.order_id.date_order
            r.fecha_prevista = fecha_prevista.strftime("%Y-%m-%d")

#     @api.multi
    def _action_launch_stock_rule(self):
        """
        Launch procurement group run method with required/custom fields genrated by a
        sale order line. procurement group will launch '_run_pull', '_run_buy' or '_run_manufacture'
        depending on the sale order line product rule.
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        errors = []
        for line in self:
            if line.state != 'sale' or not line.product_id.type in ('consu', 'product'):
                continue
            qty = line._get_qty_procurement()
            if float_compare(qty, line.product_uom_qty, precision_digits=precision) >= 0:
                continue

            group_id = line.order_id.procurement_group_id
            if not group_id:
                group_id = self.env['procurement.group'].create({
                    'name': line.order_id.name, 'move_type': line.order_id.picking_policy,
                    'sale_id': line.order_id.id,
                    'partner_id': line.order_id.partner_shipping_id.id,
                })
                line.order_id.procurement_group_id = group_id
            else:
                # In case the procurement group is already created and the order was
                # cancelled, we need to update certain values of the group.
                updated_vals = {}
                if group_id.partner_id != line.order_id.partner_shipping_id:
                    updated_vals.update({'partner_id': line.order_id.partner_shipping_id.id})
                if group_id.move_type != line.order_id.picking_policy:
                    updated_vals.update({'move_type': line.order_id.picking_policy})
                if updated_vals:
                    group_id.write(updated_vals)

            values = line._prepare_procurement_values(group_id=group_id)
            product_qty = line.product_uom_qty - qty

            procurement_uom = line.product_uom
            quant_uom = line.product_id.uom_id
            get_param = self.env['ir.config_parameter'].sudo().get_param
            if procurement_uom.id != quant_uom.id and get_param('stock.propagate_uom') != '1':
                product_qty = line.product_uom._compute_quantity(product_qty, quant_uom, rounding_method='HALF-UP')
                procurement_uom = quant_uom

            try:
                self.env['procurement.group'].run(line.product_id, product_qty, procurement_uom,
                                                  line.order_id.partner_shipping_id.property_stock_customer, line.name,
                                                  line.order_id.name, values)
            except UserError as error:
                errors.append(error.name)

        if errors:
            raise UserError('\n'.join(errors))
        return True

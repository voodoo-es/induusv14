# -*- coding: utf-8 -*-
# © 2018 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api
from odoo.addons.induus.models.induus_genei import Genei
from datetime import datetime
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    partner_origin_ids = fields.Many2many('res.partner', string="Clientes Origen", compute="_compute_partner_origin_ids")
    parent_partner_id = fields.Many2one(related="partner_id.parent_id")
    sale_order_ids = fields.Many2many('sale.order', compute="_compute_partner_origin_ids", string="Pedidos de Venta")
    sale_order_count = fields.Integer("Numero Pedidos de venta", compute="_compute_partner_origin_ids")
    sale_account_analytic_id = fields.Many2one('account.analytic.account', compute="_compute_partner_origin_ids")
    equipo_id = fields.Many2one('induus.equipo', compute="_compute_partner_origin_ids", string="Equipo")
    prueba = fields.Boolean('Prueba')
    anular_stock = fields.Boolean('Anular Stock')
    carrier_id = fields.Many2one('delivery.carrier', string="Método entrega")
    descripcion_linea = fields.Text(related='order_line.name', string="Descripción línea", store=True)
    effective_date = fields.Date('Fecha efectiva', compute='_compute_effective_date', store=True)
    pedido_completo = fields.Boolean('Completo', compute="_compute_pedido_completo", store=True)

    @api.depends('origin')
    def _compute_partner_origin_ids(self):
        for r in self:
            if r.origin:
                sale_account_analytic_id = None
                partner_ids = []
                order_ids = []
                equipo_id = None
                for o in r.origin.replace(" ", "").split(","):
                    order = self.env['sale.order'].search([('name', '=', o)], limit=1)
                    if order:
                        order_ids.append(order.id)

                    if order and order.partner_id.id not in partner_ids:
                        partner_ids.append(order.partner_id.id)

                    if order and order.analytic_account_id and not sale_account_analytic_id:
                        sale_account_analytic_id = order.analytic_account_id.id

                    if order and order.equipo_id and not equipo_id:
                        equipo_id = order.equipo_id.id

                r.update({
                    'partner_origin_ids': [(6, 0, partner_ids)],
                    'sale_order_ids': [(6, 0, order_ids)],
                    'sale_order_count': len(order_ids),
                    'sale_account_analytic_id': sale_account_analytic_id,
                    'equipo_id': equipo_id
                })
            else:
                r.update({
                    'partner_origin_ids': None,
                    'sale_order_ids': None,
                    'sale_order_count': 0,
                    'sale_account_analytic_id': None,
                    'equipo_id': None
                })

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        for r in self:
            carrier_id = None
            if r.partner_id:
                partner = r.partner_id.parent_id if r.partner_id.parent_id else r.partner_id
                carrier_id = partner.supplier_property_delivery_carrier_id.filtered('active')
            r.update({'carrier_id': carrier_id})

    @api.depends('picking_ids.date_done')
    def _compute_effective_date(self):
        for r in self:
            pickings = r.picking_ids.filtered(lambda x: x.state == 'done')
            dates_list = [date for date in pickings.mapped('date_done') if date]
            r.effective_date = dates_list and max(dates_list).date()

    @api.depends('order_line', 'order_line.qty_received', 'order_line.qty_invoiced')
    def _compute_pedido_completo(self):
        for r in self:
            completo = True
            for line in r.order_line:
                if line.qty_invoiced < line.qty_received:
                    completo = False
                    break
            r.pedido_completo = completo

#     @api.multi
    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        if res:
            return self.with_context(send_rfq=False).action_rfq_send()
        return res

#     @api.multi
    def button_cancel(self):
        super(PurchaseOrder, self).button_cancel()

    @api.model
    def create(self, vals):
        res = super(PurchaseOrder, self).create(vals)
        res.sync_prueba(vals)
        res._onchange_partner_id()
        return res

#     @api.multi
    def write(self, vals):
        res = super(PurchaseOrder, self).write(vals)
        self.sync_prueba(vals)
        return res

#     @api.multi
    def sync_prueba(self, vals):
        if 'prueba' in vals and not self.env.context.get('no_retorno'):
            for r in self:
                r.sale_order_ids.with_context(no_retorno=True).write({'prueba': vals.get('prueba')})

    @api.model
    def _prepare_picking(self):
        res = super(PurchaseOrder, self)._prepare_picking()
        res.update({'carrier_id': self.carrier_id.id if self.carrier_id else None})
        return res

    def action_view_sale_order_origin(self):
        return {
            'name': 'Pedidos de Venta',
            'domain': [('id', 'in', self.sale_order_ids.ids)],
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
        }

    @api.model
    def realizar_seguimiento(self):
        fecha_tope = fields.Datetime.to_string((datetime.now() - relativedelta(days=1)).replace(hour=23, minute=59))
        order_lines = self.env['purchase.order.line'].search(['|',
            ('order_id.partner_id.seguimiento', '=', True),
            ('order_id.partner_id.parent_id.seguimiento', '=', True),
            ('order_id.state', 'in', ['purchase']),
            ('product_id.type', '=', 'product'),
            ('date_planned', '<=', fecha_tope)
        ])

        order_ids = []
        lines_ids = {}
        for ord in order_lines.filtered(lambda o: o.qty_received < o.product_qty):
            key_order = str(ord.order_id.id)
            if key_order not in lines_ids:
                lines_ids.update({key_order: []})
            lines_ids[key_order].append(ord.id)
            order_ids.append(ord.order_id.id)

        orders = self.env['purchase.order'].search([
            ('id', 'in', order_ids),
            ('user_id', '!=', False),
        ])

        template_purchase_order = self.env.ref('induus.email_template_seguimiento_purchase_order_line')
        for r in orders:
            email = self.env['mail.template'].browse(template_purchase_order.id)\
                .with_context(lineas=lines_ids[str(r.id)])
            email.send_mail(r.id)

            template = template_purchase_order.get_email_template(r.id)
            body_html = self.env['mail.template'].with_context(lineas=lines_ids[str(r.id)]) \
                ._render_template(template.body_html, 'purchase.order', r.id)

            for picking in r.picking_ids:
                picking.with_context(mail_create_nosubscribe=True).message_post(
                    body=body_html,
                    message_type='comment',
                    subtype='mail.mt_note'
                )

            user = r.user_id if r.user_id else self.env.user
            self.env['mail.activity'].create({
                'activity_type_id': 2,
                'summary': "Verificar reclamacion a proveedor",
                'date_deadline': datetime.today(),
                'user_id': user.id,
                'res_model': 'purchase.order',
                'res_model_id': self.env.ref('purchase.model_purchase_order').id,
                'res_id': r.id,
                'res_name': r.name,
            })


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    cantidades_facturadas_mayor_que_recibida = fields.Boolean("Cantidades facturadas > recibidas", store=True,
                                                              compute="_compute_cantidades_facturadas_mayor_que_recibida")
    invoice_sale_id = fields.Many2one('account.move', string="Factura cliente")

    @api.depends('qty_invoiced', 'qty_received')
    def _compute_cantidades_facturadas_mayor_que_recibida(self):
        for r in self:
            r.cantidades_facturadas_mayor_que_recibida = True if r.qty_invoiced > r.qty_received else False

#     @api.multi
    def _prepare_stock_moves(self, picking):
        res = super(PurchaseOrderLine, self)._prepare_stock_moves(picking)
        if self.order_id.anular_stock:
            for r in res:
                r.update({
                    'analytic_account_id': None,
                    'tag_ids': None,
                })
        return res

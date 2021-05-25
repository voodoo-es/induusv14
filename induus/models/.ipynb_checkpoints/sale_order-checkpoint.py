# -*- coding: utf-8 -*-
# © 2018 Ingetive - <info@ingetive.com>

import logging
import babel

from odoo import models, fields, api, _, tools
from datetime import timedelta

_logger = logging.getLogger(__name__)

LINEAS_NEGOCIO = [
    ('distribucion', 'Distribución'),
    ('reparacion', 'Reparación'),
    ('proyecto', 'Proyecto')
]


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    prueba = fields.Boolean('Prueba')
    purchase_order_count = fields.Integer("Pedidos de Compra", compute="_compute_purchase_order_count")
    lost_reason = fields.Many2one('sale.order.lost.reason', string='Motivo de cancelación', index=True, track_visibility='onchange')
    active = fields.Boolean('Active', default=True, track_visibility=True)
    numero_dias_cobro = fields.Integer("Número días cobro", group_operator='avg', compute="_compute_numero_dias_cobro")
    numero_dias_pago = fields.Integer("Número días pago", group_operator='avg', compute="_compute_numero_dias_pago")
    numero_dias_diferencia_cobro_pago = fields.Integer("Número días diferencia cobro - pago", group_operator='avg', 
                                                       compute="_compute_numero_dias_cobro_pago")
    equipo_id = fields.Many2one('induus.equipo', string="Equipo")
    equipo_serial = fields.Char('Serial equipo',related='equipo_id.serial')
    equipo_eme = fields.Char('EME equipo',related='equipo_id.eme')
    website_description = fields.Html(translate=False)
    no_facturar_auto = fields.Boolean('No facturar automáticamente')
    amount_delivery_taxincl = fields.Monetary("Precio envío iva incl.", compute="_compute_amount_delivery_taxincl")
    effective_date_action = fields.Boolean('Fecha efectiva + 2 días menor que la fecha actual',
                                           compute="_effective_date_action")
    anadir_suscripcion = fields.Boolean('Añadir cliente a newsletter')
    purchase_invoice_ids = fields.Many2many("account.move", string='Facturas Proveedores', compute="_compute_purchase_invoice",
                                            readonly=True, copy=False)
    purchase_invoice_count = fields.Integer('Número Facturas Proveedores', compute="_compute_purchase_invoice",
                                            copy=False)
    account_analytic_url = fields.Char('Coste/Beneficio', compute="_compute_analytic_account_id", store=True)
    margen_analitico = fields.Monetary('Beneficio analítico', compute="_compute_analytic_account_id", store=True)
    margen_analitico_porcentaje = fields.Float('Margen analítico (%)', compute="_compute_analytic_account_id", store=True)
    coste = fields.Monetary('Coste', compute="_compute_coste", store=True)
    proyecto_detalle_ids = fields.One2many('induus.proyecto_detalle', 'sale_order_id')
    coste_total_proyecto_detalle = fields.Monetary('Coste total', compute="_compute_proyeto_detalle", store=True)
    precio_venta_proyecto_detalle = fields.Monetary('Precio venta total', compute="_compute_proyeto_detalle", store=True)
    beneficio_proyecto_detalle = fields.Monetary('Beneficio ', compute="_compute_proyeto_detalle", store=True)
    margen_proyecto_detalle = fields.Float('Margen (%)', compute="_compute_proyeto_detalle", store=True)
    coste_real_proyecto_detalle = fields.Monetary('Coste Real')
    beneficio_real_proyecto_detalle = fields.Monetary('Beneficio Real')
    margen_real_proyecto_detalle = fields.Float('Margen Real')
    plantilla_proyecto_detalle_id = fields.Many2one('induus.plantilla_proyecto', string="Plantilla proyecto")
    margin = fields.Monetary(string="Beneficio")
    margin_porcentaje = fields.Float('Margen (%) ', compute='_compute_coste', digits=(16, 2))
    es_proyecto = fields.Boolean('Proyecto')
    proyecto_titulo = fields.Char('Título proyecto')
    linea_negocio = fields.Selection(LINEAS_NEGOCIO, string='Línea negocio', compute="_compute_linea_negocio",
                                     store=True, default="distribucion")
    editor_proyecto = fields.Html('Editor')
    plantilla_proyecto_editor_id = fields.Many2one('induus.plantilla_proyecto_editor', string="Plantilla Editor")
    no_mostrar_ref = fields.Boolean("No mostrar referencia")
    mostrar_ref_cliente = fields.Boolean("Mostrar ref. cliente")
    mostrar_ref_induus = fields.Boolean("Mostrar ref. Induus")

    @api.depends('es_proyecto', 'order_line.product_id')
    def _compute_linea_negocio(self):
        for r in self:
            if r.es_proyecto:
                r.linea_negocio = "proyecto"
                continue

            reparacion = False
            for line in r.order_line:
                if line.product_id.code in ["IND18875", "IND17036"]:
                    reparacion = True

            r.linea_negocio = "reparacion" if reparacion else "distribucion"

    @api.depends('margin', 'order_line.purchase_price', 'order_line.product_uom_qty', 'order_line.state')
    def _compute_coste(self):
        for r in self:
            coste = 0
            for line in r.order_line.filtered(lambda x: x.state != 'cancel'):
                coste += line.product_uom_qty * line.purchase_price

            margin_porcentaje = (r.margin * 100) / coste if coste else 100
            r.update({
                'coste': coste,
                'margin_porcentaje': margin_porcentaje
            })

#     @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super(SaleOrder, self).onchange_partner_id()
        no_facturar_auto = None
        if self.partner_id and \
            (self.partner_id.no_facturar_auto or (self.partner_id.parent_id and self.partner_id.parent_id.no_facturar_auto)):
            no_facturar_auto = True
            
        team_id = None
        if self.partner_id:
            team_id = self.partner_id.sale_order_team_id.id
            if self.partner_id.parent_id and self.partner_id.parent_id.sale_order_team_id:
                team_id = self.partner_id.parent_id.sale_order_team_id.id
            
            self.update({
                'no_mostrar_ref': self.partner_id.no_mostrar_ref,
                'mostrar_ref_cliente': self.partner_id.mostrar_ref_cliente,
                'mostrar_ref_induus': self.partner_id.mostrar_ref_induus
            })
                
        if team_id:
            self.update({'team_id': team_id})

        self.update({'no_facturar_auto': no_facturar_auto})

    @api.onchange('partner_id')
    def onchange_partner_id_carrier_id(self):
        carrier_id = None
        if self.partner_id:
            partner = self.partner_id.parent_id if self.partner_id.parent_id else self.partner_id
            carrier_id = partner.property_delivery_carrier_id.filtered('active')
        self.carrier_id = carrier_id

    @api.onchange('es_proyecto')
    def _onchange_es_proyecto(self):
        for r in self:
            if r.es_proyecto:
                r.user_id = 21 # Es el usuario Armando Perales Garcia

    def _compute_purchase_invoice(self):
        for r in self:
            orders = self.env['purchase.order'].search([('origin', 'like', r.name)])
            invoice_ids = []
            for order in orders:
                invoice_ids += order.invoice_ids.ids
            r.update({
                'purchase_invoice_count': len(invoice_ids),
                'purchase_invoice_ids': [(6, 0, invoice_ids)]
            })

    @api.depends('analytic_account_id', 'coste', 'analytic_account_id.line_ids', 'analytic_account_id.line_ids.amount')
    def _compute_analytic_account_id(self):
        for r in self:
            account_analytic_url = None
            margen_analitico = 0
            if r.analytic_account_id:
                account_analytic_url = "/web?#action=%s&active_id=%s&model=account.analytic.line&view_type=list&menu_id=%s" % (
                    self.env.ref("analytic.account_analytic_line_action").id,
                    r.analytic_account_id.id,
                    self.env.ref("induus.account_analytic_account_hojas_margenes_tree").id
                )
                for line in r.analytic_account_id.line_ids:
                    margen_analitico += line.amount

            r.update({
                'account_analytic_url': account_analytic_url,
                'margen_analitico': margen_analitico,
                'margen_analitico_porcentaje': (margen_analitico * 100) / r.coste if r.coste else 0
            })

    @api.depends('proyecto_detalle_ids.total', 'proyecto_detalle_ids.coste')
    def _compute_proyeto_detalle(self):
        for r in self:
            coste_total = 0
            precio_venta_total = 0
            for proyecto in r.proyecto_detalle_ids:
                coste_total += proyecto.total
                precio_venta_total += proyecto.precio_venta

            beneficio = precio_venta_total - coste_total
            margen = (beneficio * 100) / coste_total if coste_total else 100
            r.update({
                'coste_total_proyecto_detalle': coste_total,
                'precio_venta_proyecto_detalle': precio_venta_total,
                'beneficio_proyecto_detalle': beneficio,
                'margen_proyecto_detalle': margen
            })

    def cargar_plantilla_proyecto_detalle(self):
        for r in self:
            if r.plantilla_proyecto_detalle_id:
                for ppd in r.plantilla_proyecto_detalle_id.proyecto_detalle_ids:
                    proyecto = self.env['induus.proyecto_detalle'].create({
                        'sale_order_id': r.id,
                        'name': ppd.name,
                        'unidades': ppd.unidades,
                    })

                    for linea in ppd.linea_ids:
                        self.env['induus.proyecto_detalle_linea'].create({
                            'proyecto_detalle_id': proyecto.id,
                            'product_id': linea.product_id.id if linea.product_id else None,
                            'product_ref': linea.product_ref,
                            'partner_id': linea.partner_id.id if linea.partner_id else None,
                            'descripcion': linea.descripcion,
                            'unidades': linea.unidades,
                            'pvp': linea.pvp,
                            'coste': linea.coste,
                        })

    def cargar_plantilla_proyecto_editor(self):
        for r in self:
            if r.plantilla_proyecto_editor_id:
                r.update({
                    'proyecto_titulo': r.plantilla_proyecto_editor_id.name,
                    'editor_proyecto': r.plantilla_proyecto_editor_id.editor,
                })

#     @api.multi
    def _effective_date_action(self):
        for r in self:
            effective_date = False
            if r.effective_date and (r.effective_date + timedelta(days=2)) < fields.Date.today():
                effective_date = True
            r.effective_date_action = effective_date

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        self.env['account.analytic.line'].actualizar_cuentas_analiticas(res.name)
        res.sync_prueba(vals)
        res.crear_seguimiento_oferta_cliente()
        return res

    def crear_seguimiento_oferta_cliente(self):
        for r in self:
            dias_seguimiento = r.partner_id.seguimiento_cliente
            if r.partner_id.parent_id:
                dias_seguimiento = r.partner_id.parent_id.seguimiento_cliente
            self.env['mail.activity'].create({
                'activity_type_id': self.env.ref("induus.mail_act_oferta_cliente").id,
                'summary': "Seguimiento oferta cliente",
                'date_deadline': fields.Date.today() + timedelta(days=dias_seguimiento),
                'user_id': r.user_id.id if r.user_id else 2,
                'res_model': 'sale.order',
                'res_model_id': self.env.ref('sale.model_sale_order').id,
                'res_id': r.id,
                'res_name': r.name,
            })

#     @api.multi
    def write(self, vals):
        if 'state' in vals:
            states = {}
            for r in self.filtered(lambda o: o.anadir_suscripcion and o.partner_id.email):
                states.update({str(r.id): r.state})

        res = super(SaleOrder, self).write(vals)
        for r in self:
            self.env['account.analytic.line'].actualizar_cuentas_analiticas(r.name)
        self.sync_prueba(vals)

        if vals.get('partner_id'):
            for r in self.filtered(lambda so: so.analytic_account_id):
                r.analytic_account_id.write({'partner_id' : r.partner_id.id})

#         if not self.env.context.get('no_get_delivery_price'):
#             self.filtered(lambda o: o.carrier_id and o.state in ['draft', 'sent']).get_delivery_price()

        if 'state' in vals:
            for r in self.filtered(lambda o: o.anadir_suscripcion and o.partner_id.email):
                if r.state in ['sent', 'sale', 'done'] and states[str(r.id)] == 'draft':
                    mailing = self.env['mail.mass_mailing'].sudo().browse(1)
                    if not mailing:
                        continue

                    MailingContact = self.env['mail.mass_mailing.contact'].sudo()
                    contact = MailingContact.search([
                        ('email', '!=', r.partner_id.email),
                        ('list_ids', 'in', [1])
                    ])
                    if not contact:
                        MailingContact.create({
                            'name': r.partner_id.name,
                            'email': r.partner_id.email,
                            'list_ids': [(4, 1)]
                        })

        return res

#     @api.multi
    def get_delivery_price(self):
        self = self.with_context(no_get_delivery_price=True)
        super(SaleOrder, self).get_delivery_price()
        self.filtered(lambda r: r.delivery_price > 0).set_delivery_line()

#     @api.multi
    def action_cancel(self):
        result = super(SaleOrder, self).action_cancel()
        purchase_order_ids = []
        for r in self:
            purchase_order = self.env['purchase.order'].search([('origin', 'like', r.name)])
            for po in purchase_order:
                purchase_order_ids.append(po.id)

        purchase_order = self.env['purchase.order'].search([('id', 'in', purchase_order_ids)])
        purchase_order.button_cancel()
        return result

#     @api.multi
    def sync_prueba(self, vals):
        if 'prueba' in vals and not self.env.context.get('no_retorno'):
            for r in self:
                purchase_orders = self.env['purchase.order'].search([('origin', 'like', r.name)])
                purchase_orders.with_context(no_retorno=True).write({'prueba': vals.get('prueba')})

#     @api.multi
    def unlink(self):
        names = [r.name for r in self]
        res = super(SaleOrder, self).unlink()
        for n in names:
            self.env['account.analytic.line'].actualizar_cuentas_analiticas(n)
        return res

#     @api.multi
    def action_confirm(self):
        if self.es_proyecto:
            crear = False
            for proyecto_detalle in self.proyecto_detalle_ids:
                if proyecto_detalle.linea_ids:
                    crear = True
                    break

            if crear:
                self.write({
                    'state': 'sale',
                    'confirmation_date': fields.Datetime.now()
                })

            for proyecto_detalle in self.proyecto_detalle_ids:
                proyecto_detalle.linea_ids.crear_stock_picking_proyecto()
                proyecto_detalle.linea_ids.crear_apuntes_analiticos()

            categoria = self.env['product.category'].search([('name', '=ilike', 'proyectos')], limit=1)

            product_tmpl = self.env['product.template'].create({
                'name': self.proyecto_titulo,
                'type': 'service',
                'categ_id': categoria.id if categoria else None,
                'default_code': self.name,
                'list_price': self.precio_venta_proyecto_detalle,
                'invoice_policy': 'delivery'
            })

            self.env['sale.order.line'].create({
                'order_id': self.id,
                'product_id': product_tmpl.product_variant_id.id
            })

        else:
            return super(SaleOrder, self).action_confirm()

#     @api.multi
    def _action_confirm(self):
        result = super(SaleOrder, self)._action_confirm()
        for order in self:
            order.partner_id.campos_obligatorios(False)
            order.partner_id.write({'validar_campos': True})
            if order.user_id:
                purchases = self.env['purchase.order'].search([('origin', 'like', order.name)])
                if purchases:
                    purchases.write({'user_id': order.user_id.id})
            order.activity_ids.action_done()
        return result

    def _compute_purchase_order_count(self):
        for r in self:
            r.purchase_order_count = self.env['purchase.order'].search_count([('origin', 'like', r.name)])

    def _compute_numero_dias_cobro(self):
        for r in self:
            ultimo_efecto = self.env['account.move.line'].search([('invoice_origin', 'like', r.name),('account_id.internal_type','=','receivable')],order="date_maturity desc",limit=1)
            if ultimo_efecto:
                r.numero_dias_cobro = (ultimo_efecto.date_maturity-ultimo_efecto.invoice_date).days
            else:
                r.numero_dias_cobro = 0

    def _compute_numero_dias_pago(self):
        for r in self:
            pedidoscomprarelacionados = self.env['purchase.order'].search([('origin', 'like', r.name)])
            pedidoscomprarelacionados_ids = []

            for pedidocompra in pedidoscomprarelacionados:
                pedidoscomprarelacionados_ids.append(pedidocompra.name)

            ultimo_efecto = self.env['account.move.line'].search([('invoice_origin', 'in', pedidoscomprarelacionados_ids),('account_id.internal_type','=','payable')],order="date_maturity desc",limit=1)

            if ultimo_efecto:
                r.numero_dias_pago = (ultimo_efecto.date_maturity-ultimo_efecto.invoice_date).days
            else:
                r.numero_dias_pago = 0

    @api.depends('numero_dias_cobro','numero_dias_pago')
    def _compute_numero_dias_cobro_pago(self):
        for r in self:
            r.numero_dias_diferencia_cobro_pago = r.numero_dias_cobro - r.numero_dias_pago

    def action_view_purchase_order(self):
        self.ensure_one()
        return {
            'name': 'Pedidos de Compra',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'tree, form',
            'views': [
                (self.env.ref('purchase.purchase_order_tree').id, 'tree'),
                (self.env.ref('purchase.purchase_order_form').id, 'form')
            ],
            'view_id': False,
            'target': 'current',
            'domain': [('origin', 'like', self.name)]
        }

    def action_view_purchase_invoice(self):
        self.ensure_one()
        return {
            'name': 'Facturas Proveedor',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree, form',
            'views': [
                (self.env.ref('account.move_supplier_tree').id, 'tree'),
                (self.env.ref('account.move_supplier_form').id, 'form')
            ],
            'view_id': False,
            'target': 'current',
            'domain': [('id', 'in', self.purchase_invoice_ids.ids if self.purchase_invoice_ids else [])]
        }

    def action_view_efectos_cobro(self):
        self.ensure_one()
        return {
            'name': 'Efectos',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'view_mode': 'tree, form',
            'views': [
                (self.env.ref('account_due_list.view_payments_tree').id, 'tree'),
                (self.env.ref('account.view_move_line_form').id, 'form')
            ],
            'view_id': False,
            'target': 'current',
            'domain': [('invoice_origin', 'like', self.name),('account_id.internal_type','=','receivable')]
        }

    def action_view_efectos_pago(self):
        self.ensure_one()
        pedidoscomprarelacionados = self.env['purchase.order'].search([('origin', 'like', self.name)])
        pedidoscomprarelacionados_ids = []
        for pedidocompra in pedidoscomprarelacionados:
            pedidoscomprarelacionados_ids.append(pedidocompra.name)

        return {
            'name': 'Efectos',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'view_mode': 'tree, form',
            'views': [
                (self.env.ref('account_due_list.view_payments_tree').id, 'tree'),
                (self.env.ref('account.view_move_line_form').id, 'form')
            ],
            'view_id': False,
            'target': 'current',
            'domain': [('invoice_origin', 'in', pedidoscomprarelacionados_ids),('account_id.internal_type','=','payable')]
        }

#     @api.multi
    def action_set_lost(self):
        return self.write({'active': False})

    def _create_delivery_line(self, carrier, price_unit):
        if carrier.no_anadir_order or not price_unit:
            return None
        return super(SaleOrder, self)._create_delivery_line(carrier, price_unit)

    def order_invoice_no_auto(self):
        orders_init = self.search([
            ('prueba', '=', False),
            ('order_line', '!=', False),
            ('invoice_status','=','to invoice'),
            ('no_facturar_auto', '=', False),
        ])

        orders = []
        for order in orders_init:
            picking_no_facturar_auto = False
            for picking in order.picking_ids:
                if picking.no_facturar_auto:
                    picking_no_facturar_auto = True
                    break

            if picking_no_facturar_auto:
                continue

            lineas_producto_stock = order.order_line.filtered(lambda l: l.product_id.type == 'product')
            lineas_hechas = lineas_producto_stock.filtered(lambda l: l.product_uom_qty == l.qty_delivered)
            if len(lineas_producto_stock) == len(lineas_hechas):
                orders.append(order)

        return orders

    def action_order_invoice_no_auto(self):
        orders = self.order_invoice_no_auto()
        return {
            'name': 'Pedidos a facturar (Induus)',
            'domain': [('id', 'in', [o.id for o in orders])],
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
        }

    def order_invoice_auto(self):
        orders_ini = self.search([
            ('prueba', '=', False),
            ('order_line', '!=', False),
            ('invoice_status','=','to invoice'),
        ])

        orders = []
        for order in orders_ini:
            picking_no_facturar_auto = False

            if order.partner_id.no_facturar_auto or order.no_facturar_auto:
                picking_no_facturar_auto = True

            if not picking_no_facturar_auto:
                for picking in order.picking_ids:
                    if picking.no_facturar_auto:
                        picking_no_facturar_auto = True
                        break

            if not picking_no_facturar_auto:
                continue

            lineas_producto_stock = order.order_line.filtered(lambda l: l.product_id.type == 'product')
            lineas_hechas = lineas_producto_stock.filtered(lambda l: l.product_uom_qty == l.qty_delivered)
            if len(lineas_producto_stock) == len(lineas_hechas):
                orders.append(order)
        return orders

    def action_order_invoice_auto(self):
        orders = self.order_invoice_auto()
        return {
            'name': 'Pedidos a facturar no automáticos (Induus)',
            'domain': [('id', 'in', [o.id for o in orders])],
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'views': [(self.env.ref('induus.sale_order_no_automaticos_tree').id, 'tree'),
                      (self.env.ref('sale.view_order_form').id, 'form')],
            'view_mode': 'tree,form',
            'view_type': 'form',
            'search_view_id': None,
        }

    def action_desfase(self):
        orders = self.search([('numero_dias_pago', '!=', 0)])
        order_ids = [o.id for o in orders if o.numero_dias_pago != 0 and o.numero_dias_pago < o.numero_dias_cobro]
        return {
            'name': 'Desfase (Induus)',
            'domain': [('id', 'in', order_ids)],
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'search_view_id': None,
        }

    def delay_website(self, delivery_id=None, format="string"):
        self.ensure_one()
        self = self.sudo()
        locale = self.env.context.get('lang') or 'en_US'
        fecha_entrega = None

        if delivery_id == 3: # 3 es la recogida en Induus
            country_code = 'ES'
        else:
            country_code = self.partner_shipping_id.country_id.code if self.partner_shipping_id.country_id else 'ES'

        for line in self.order_line.filtered(lambda l: not l.is_delivery):
            fe = line.product_id.delay_website(line.product_uom_qty, "date", country_code)
            if not fe:
                continue

            if not fecha_entrega:
                fecha_entrega = fe
                continue

            if fe > fecha_entrega:
                fecha_entrega = fe

        if not fecha_entrega:
            if format == 'string':
                return _("Fecha prevista de entrega no disponible.")
            else:
                return None

        if format == 'string':
            return _("Fecha prevista de entrega: ") + tools.ustr(babel.dates.format_date(date=fecha_entrega, format='full', locale=locale))
        else:
            return fecha_entrega

    def _compute_amount_delivery_taxincl(self):
        for r in self:
            envio = 0
            for line in r.order_line:
                if line.is_delivery:
                    envio += line.price_total / line.product_uom_qty if line.product_uom_qty else 0.0
            r.amount_delivery_taxincl = envio

    def action_account_analytic(self):
        self.ensure_one()
        return {
            'name': 'Coste/Beneficio',
            'type': 'ir.actions.act_url',
            'url': self.account_analytic_url,
            'target': 'new',
        }

    def action_sale_crm_lead_view(self):
        self.ensure_one()
        return {
            'name': 'Oportunidad',
            'res_id': self.opportunity_id.id,
            'res_model': 'crm.lead',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
        }

#     @api.multi
    def action_quotation_send(self):
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        proforma = self.env.context.get('proforma', False)

        template_id = None
        template_name = None
        if proforma:
            template_name = 'Factura Pro-Forma (Induus)'
        elif self.state == 'draft':
            template_name = 'Presupuesto (Induus)'
        elif self.state == 'sale':
            template_name = 'Confirmación Pedido (Induus)'

        if template_name:
            template = self.env['mail.template'].search([
                ('name', '=ilike', template_name),
                ('model_id', '=', 288) # 288 es el ID modelo de sale.order
            ], limit=1)
            if template:
                template_id = template.id

        if not template_id:
            try:
                template_id = ir_model_data.get_object_reference('sale', 'email_template_edi_sale')[1]
            except ValueError:
                template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        lang = self.env.context.get('lang')
        template = template_id and self.env['mail.template'].browse(template_id)
        if template and template.lang:
            lang = template._render_template(template.lang, 'sale.order', self.ids[0])
        ctx = {
            'default_model': 'sale.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'model_description': self.with_context(lang=lang).type_name,
            'custom_layout': "mail.mail_notification_paynow",
            'proforma': proforma,
            'force_email': True
        }
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

#     @api.multi
    def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
        values = super(SaleOrder, self)._cart_update(product_id, line_id, add_qty, set_qty, **kwargs)
        if values['quantity'] > 0:
            line = self.env['sale.order.line'].sudo().browse(values['line_id'])
            if line:
                line._onchange_product_id_set_customer_lead()
        return values


class SaleOrderLostReason(models.Model):
    _name = "sale.order.lost.reason"
    _description = 'Motivo de cancelación Presupuesto/Pedido'

    name = fields.Char('Name', required=True, translate=True)
    active = fields.Boolean('Active', default=True)


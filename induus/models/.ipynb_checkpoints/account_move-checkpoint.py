# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api
from odoo.tools import float_is_zero
from collections import OrderedDict
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    margen_analitico = fields.Monetary("Beneficio analítico", compute="_compute_origin_account_analytic_id")
    margen_analitico_porcentaje = fields.Float("Margen analítico (%)", compute="_compute_origin_account_analytic_id")
    purchase_origin = fields.Char(string='D.O. venta', compute="_compute_invoice_line_ids")
    equipo_id = fields.Many2one('induus.equipo', string="Equipo", compute="_compute_invoice_line_ids")
    origin_account_analytic_id = fields.Many2one('account.analytic.account', string="Cuenta Analítica Origen",
                                                 compute="_compute_origin_account_analytic_id")
    origin_account_analytic_url = fields.Char('Coste/Beneficio',  compute="_compute_origin_account_analytic_id")
    sale_order_count = fields.Integer('Nº Pedidos de venta', compute="_compute_origin_account_analytic_id")
    sale_order_ids = fields.Many2many('sale.order', compute="_compute_origin_account_analytic_id")
    purchase_order_count = fields.Integer('Nº Pedidos de compra', compute="_compute_origin_account_analytic_id")
    purchase_order_ids = fields.Many2many('purchase.order', compute="_compute_origin_account_analytic_id")
    stock_picking_count = fields.Integer('Nº Albaranes', compute="_compute_origin_account_analytic_id")
    stock_picking_ids = fields.Many2many('stock.picking', compute="_compute_origin_account_analytic_id")
    parent_id = fields.Many2one(related="partner_id.parent_id")
    partner_valids_ids = fields.Many2many('res.partner', compute="_compute_partner_valids_ids")
    amount_untaxed_invoice_signed = fields.Monetary(store=True)
    amount_tax_signed = fields.Monetary(store=True)
    enviada_auto = fields.Boolean('Enviada automáticamente')
    margin_porcentaje = fields.Float('Margen (%)', compute='_compute_margin', store=True, readonly=True)
    coste = fields.Float('Margen (%)', compute='_compute_margin', store=True, readonly=True)
    invoice_attachment_ids = fields.One2many('ir.attachment', 'invoice_id')
    date_payment = fields.Date('Fecha de pago', compute="_compute_date_payment", store=True)
    num_dias_cobro = fields.Integer("Días cobro", compute="_compute_date_payment", store=True)

    # rellnear los campos 
    @api.depends('invoice_line_ids.amount_residual')
    def _compute_date_payment(self):
        for r in self:
            date = None
            payment_vals = r._get_payments_vals()
            for values in payment_vals:
                if not date:
                    date = values['date']
                elif date < values['date']:
                    date = values['date']
                    
            if date:
                r.date_payment = date
            else:
                r.date_payment = None
                
            if date and r.date_due:
                r.num_dias_cobro = (date - r.date_due).days
            else:
                r.num_dias_cobro = 0

#     @api.multi
#     @api.depends(
#         'invoice_line_ids.quantity',
#         'invoice_line_ids.margin',
#         'invoice_line_ids.margin_signed',
#         'invoice_line_ids.purchase_price',
#         'invoice_line_ids.price_subtotal',
#     )
#     def _compute_margin(self):
#         super(AccountInvoice, self)._compute_margin()
#         for r in self:
#             coste = 0
#             for line in r.invoice_line_ids:
#                 coste += line.quantity * line.purchase_price

#             margin_porcentaje = (r.margin * 100) / coste if coste else 100
#             r.update({
#                 'coste': coste,
#                 'margin_porcentaje': margin_porcentaje
#             })

    @api.depends('partner_id')
    def _compute_partner_valids_ids(self):
        for r in self:
            partner_ids = []
            team_id = None
            if r.partner_id:
                partner_ids.append(r.partner_id.id)
                team_id = r.partner_id.sale_order_team_id.id
            if r.partner_id.parent_id:
                partner_ids.append(r.partner_id.parent_id.id)
                if r.partner_id.parent_id.sale_order_team_id:
                    team_id = r.partner_id.parent_id.sale_order_team_id.id
                
            r.partner_valids_ids = partner_ids
            
            if team_id:
                r.team_id = team_id

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        res = super(AccountInvoice, self)._onchange_partner_id()
        self._cambiar_intrastat()
        return res

    @api.onchange('vendor_bill_purchase_id')
    def _onchange_bill_purchase_order(self):
        res = super(AccountInvoice, self)._onchange_bill_purchase_order()
        self._cambiar_intrastat()
        return res

    @api.onchange('state', 'partner_id', 'invoice_line_ids')
    def _onchange_allowed_purchase_ids(self):
        '''
        The purpose of the method is to define a domain for the available
        purchase orders.
        '''
        result = {}

        # A PO can be selected only if at least one PO line is not already in the invoice
        purchase_line_ids = self.invoice_line_ids.mapped('purchase_line_id')
        purchase_ids = self.invoice_line_ids.mapped('purchase_id').filtered(lambda r: r.order_line <= purchase_line_ids)

        domain = [('invoice_status', 'in', ['to invoice', 'no'])]
        if self.partner_id:
            domain += [('partner_id', 'child_of', self.partner_valids_ids.ids)]
        if purchase_ids:
            domain += [('id', 'not in', purchase_ids.ids)]
        result['domain'] = {'purchase_id': domain}
        return result

    @api.depends('invoice_line_ids')
    def _compute_invoice_line_ids(self):
        for r in self:
            purchase_ids = r.invoice_line_ids.mapped('purchase_id')
            origins = []
            for purchase_id in purchase_ids:
                if purchase_id.origin:
                    origins.append(purchase_id.origin)

            if origins:
                r.purchase_origin = ', '.join(origins)

            equipo_id = None
            for line in r.invoice_line_ids:
                for sale_line in line.sale_line_ids:
                    if sale_line.order_id.equipo_id:
                        equipo_id = sale_line.order_id.equipo_id.id
                        break
                if equipo_id:
                    break

            r.equipo_id = equipo_id

    @api.depends('invoice_origin')
    def _compute_origin_account_analytic_id(self):
        for r in self:
            origin_account_analytic_id = None
            origin_account_analytic_url = None
            sale_order_ids = []
            purchase_order_ids = []
            stock_picking_ids = []
            margen_analitico = 0

            if r.origin:
                origins = r.origin.split(',')

                for o in origins:
                    sale_order = self.env['sale.order'].search([('name', '=', o.replace(" ", ""))], limit=1)
                    if sale_order:
                        sale_order_ids.append(sale_order.id)
                        stock_picking_ids += [p.id for p in sale_order.picking_ids]

                for o in origins:
                    purchase_order = self.env['purchase.order'].search([('name', '=', o.replace(" ", ""))], limit=1)
                    if purchase_order:
                        purchase_order_ids.append(purchase_order.id)
                        stock_picking_ids += [p.id for p in purchase_order.picking_ids]

                sale_order_name = origins[0].replace(" ", "")

                order = self.env['purchase.order'].search([
                    ('name', '=', sale_order_name),
                    ('origin', '!=', False),
                ], limit=1)
                if order:
                    origins = order.origin.strip().split(',')
                    sale_order_name = origins[0].replace(" ", "")

                order = self.env['sale.order'].search([
                    ('name', '=', sale_order_name),
                    ('analytic_account_id', '!=', False)
                ], limit=1)

                if order:
                    origin_account_analytic_id = order.analytic_account_id.id
                    origin_account_analytic_url = "/web?#action=%s&active_id=%s&model=account.analytic.line&view_type=list&menu_id=%s" % (
                        self.env.ref("analytic.account_analytic_line_action").id,
                        order.analytic_account_id.id,
                        self.env.ref("induus.account_analytic_account_hojas_margenes_tree").id
                    )

                    for line in order.analytic_account_id.line_ids:
                        margen_analitico += line.amount

            r.update({
                'origin_account_analytic_id': origin_account_analytic_id,
                'origin_account_analytic_url': origin_account_analytic_url,
                'sale_order_ids': [(6, 0, sale_order_ids)],
                'sale_order_count': len(sale_order_ids),
                'purchase_order_ids': [(6, 0, purchase_order_ids)],
                'purchase_order_count': len(purchase_order_ids),
                'stock_picking_ids': [(6, 0, stock_picking_ids)],
                'stock_picking_count': len(stock_picking_ids),
                'margen_analitico': margen_analitico,
                'margen_analitico_porcentaje': (margen_analitico * 100) / r.coste if r.coste else 0
            })

    @api.depends('type', 'amount_untaxed', 'amount_tax')
    def _compute_sign_taxes(self):
        super(AccountInvoice, self)._compute_sign_taxes()

    @api.model
    def create(self, vals):
        onchanges = {'_onchange_partner_id': ['partner_id']}
        for onchange_method, changed_fields in list(onchanges.items()):
            if any(f not in vals for f in changed_fields):
                invoice = self.new(vals)
                getattr(invoice, onchange_method)()
                for field in changed_fields:
                    if field not in vals and invoice[field]:
                        vals[field] = invoice._fields[field].convert_to_write(invoice[field], invoice,)

        res = super(AccountInvoice, self.with_context(mail_auto_subscribe_no_notify=True, mail_create_nosubscribe=True)).create(vals)
        self.env['account.analytic.line'].actualizar_cuentas_analiticas(res.origin)
        return res

#     @api.multi
    def write(self, vals):
        res = super(AccountInvoice, self).write(vals)
        for r in self:
            self.env['account.analytic.line'].actualizar_cuentas_analiticas(r.origin)

        if vals.get('invoice_date') or "type" in vals:
            self.env['ir.attachment'].actualizar_etiquetas_facturas(self.ids)

        return res

#     @api.multi
    def unlink(self):
        origins = [r.origin for r in self]
        res = super(AccountInvoice, self).unlink()
        for o in origins:
            self.env['account.analytic.line'].actualizar_cuentas_analiticas(o)
        return res

    def _cambiar_intrastat(self):
        for r in self:
            incoterm_id = None
            intrastat_country_id = None
            intrastat_transport_mode_id = None
            if r.partner_id:
                if r.partner_id.parent_id:
                    partner = r.partner_id.parent_id
                else:
                    partner = r.partner_id

                incoterm_id = partner.incoterm_id.id if partner.incoterm_id else None
                intrastat_country_id = partner.intrastat_country_id.id if partner.intrastat_country_id else None
                intrastat_transport_mode_id = partner.intrastat_transport_mode_id.id if partner.intrastat_transport_mode_id else None

            r.update({
                'incoterm_id': incoterm_id,
                'intrastat_country_id': intrastat_country_id,
                'intrastat_transport_mode_id': intrastat_transport_mode_id
            })

    @api.model
    def _sort_grouped_lines(self, lines_dic):
        return sorted(lines_dic, key=lambda x: (x['picking'].date, x['picking'].date_done))

    def lines_grouped_by_picking(self):
        """This prepares a data structure for printing the invoice report
        grouped by pickings."""
        self.ensure_one()
        picking_dict = OrderedDict()
        lines_dict = OrderedDict()
        sign = -1.0 if self.type == 'out_refund' else 1.0
        for line in self.invoice_line_ids:
            remaining_qty = line.quantity
            for move in line.move_line_ids:
                key = (move.picking_id, line)
                picking_dict.setdefault(key, 0)
                qty = 0
                if move.location_id.usage == 'customer':
                    qty = -move.quantity_done * sign
                elif move.location_dest_id.usage == 'customer':
                    qty = move.quantity_done * sign
                picking_dict[key] += qty
                remaining_qty -= qty
            if (not float_is_zero(remaining_qty, precision_rounding=line.product_id.uom_id.rounding)):
                lines_dict[line] = remaining_qty

        no_picking = [
            {'picking': False, 'line': key, 'quantity': value}
            for key, value in lines_dict.items()
        ]
        with_picking = [
            {'picking': key[0], 'line': key[1], 'quantity': value}
            for key, value in picking_dict.items()
        ]

        return no_picking + self._sort_grouped_lines(with_picking)

    def action_view_sale_order_from_invoice(self):
        self.ensure_one()
        return {
            'name': 'Pedidos a Venta',
            'domain': [('id', 'in', [o.id for o in self.sale_order_ids])],
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
        }

    def action_view_purchase_order_from_invoice(self):
        self.ensure_one()
        return {
            'name': 'Pedidos a Compra',
            'domain': [('id', 'in', [o.id for o in self.purchase_order_ids])],
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
        }

    def action_stock_picking_from_invoice(self):
        self.ensure_one()
        return {
            'name': 'Albaranes',
            'domain': [('id', 'in', [o.id for o in self.stock_picking_ids])],
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
        }

#     @api.multi
    def action_invoice_open(self):
        to_open_invoices = self.filtered(lambda inv: inv.state != 'open' and inv.type == 'out_invoice')
        for invoice in to_open_invoices:
            for line in invoice.invoice_line_ids:
                if not line.account_analytic_id:
                    raise UserError("Hay lineas sin cuenta analítca.")

        res = super(AccountInvoice, self).action_invoice_open()

        for r in self.filtered(lambda x: x.type in ['in_invoice', 'in_refund']):
            i = 0
            for attachment in r.invoice_attachment_ids:
                num = ' (%s)' % i if i > 0 else ''
                if attachment.mimetype == 'application/pdf' and r.number:
                    attachment.write({
                        'importada': True,
                        'ref': "origen_%s%s.pdf" % (r.number, num)
                    })
                i = i + 1

        for r in self.filtered(lambda o: o.type == 'out_invoice'):
            return r.action_invoice_sent()

        return res

#     @api.multi
    def set_field_with_text(self, field, text):
        res = super(AccountInvoice, self).set_field_with_text(field, text)
        self.invoice_line_ids = None
        return res

#     @api.multi
    def _set_invoice_lines(self, invoice_lines, subtotal_ocr):
        pass

    def action_importar_envios_genei(self):
        self.ensure_one()
        importar_envios = self.env['induus.importar_envio'].create({'invoice_id': self.id})
        return importar_envios.open_wizard()

    def action_account_analytic(self):
        self.ensure_one()
        return {
            'name': 'Coste/Beneficio',
            'type': 'ir.actions.act_url',
            'url': self.origin_account_analytic_url,
            'target': 'new',
        }
    
    def get_invoice_date_from_out_out_refund(self):
        self.ensure_one()
        if self.type == 'out_refund' and self.origin:
            for o in self.origin.split(','):
                _logger.warning(o)
                invoice = self.env['account.move'].search([
                    ('number', '=', o.replace(" ", "")),
                    ('invoice_date', '!=', False),
                    ('type', '=', 'out_invoice')
                ], limit=1)
                if invoice:
                    return invoice.invoice_date.strftime("%d/%m/%Y")
        return ''

# -*- coding: utf-8 -*-
# © 2018 Ingetive - <info@ingetive.com>

import logging

from odoo.addons.induus.models.induus_db import InduusDB
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class AccountAnalytic(models.Model):
    _inherit = 'account.analytic.account'

    invoice_id = fields.Many2one('account.move', string="Factura", compute="_compute_invoice", store=True)
    invoice_date_invoice = fields.Date('Fecha factura', compute="_compute_invoice", store=True)
    invoice_number = fields.Char('Número', compute="_compute_invoice", store=True)
    invoice_name = fields.Char('Referencia/Descripción', compute="_compute_invoice", store=True)
    invoice_date_due = fields.Date('Fecha vencimiento', compute="_compute_invoice", store=True)
    invoice_state = fields.Selection([
        ('draft', 'Borrador'),
        ('open', 'Abierto'),
        ('in_payment', 'In Payment'),
        ('paid', 'Pagado'),
        ('cancel', 'Cancelado'),
    ], string='Estado', compute="_compute_invoice", store=True)
    invoice_payment_mode_id = fields.Many2one('account.payment.mode', compute="_compute_invoice" ,
                                              string="Modo de pago", store=True)
    invoice_amount_untaxed = fields.Monetary('Base imponible', compute="_compute_invoice", store=True)
    invoice_amount_tax = fields.Monetary('Impuesto', compute="_compute_invoice", store=True)
    invoice_amount_total_signed = fields.Monetary('Total en la divisa de la factura', compute="_compute_invoice",
                                                  store=True)
    coste_margenes = fields.Monetary("Coste ", compute="_compute_invoice", store=True)
    coste_margenes_sin_portes = fields.Monetary("Coste sin portes", compute="_compute_invoice", store=True)
    coste_margenes_portes = fields.Monetary("Coste portes", compute="_compute_invoice", store=True)
    venta_margenes = fields.Monetary("Venta ", compute="_compute_invoice", store=True)
    beneficio = fields.Monetary("Beneficio", compute="_compute_invoice", store=True)
    margen = fields.Float("Margen", compute="_compute_invoice", store=True, group_operator="avg")
    account_analytic_url = fields.Char('Coste/Beneficio', compute="_compute_invoice")
    account_invoice_url = fields.Char('Factura', compute="_compute_invoice")

    @api.depends('code')
    def _compute_invoice(self):
        for r in self:
            values = {
                'invoice_id': False,
                'invoice_date_invoice': False,
                'invoice_number': False,
                'invoice_date_due': False,
                'invoice_state': False,
                'invoice_payment_mode_id': False,
                'invoice_amount_untaxed': 0,
                'invoice_amount_tax': 0,
                'invoice_amount_total_signed': 0,
                'coste_margenes': 0,
                'coste_margenes_sin_portes': 0,
                'coste_margenes_portes': 0,
                'beneficio': 0,
                'margen': 0,
                'account_analytic_url': False,
                'account_invoice_url': False,
                'invoice_name': False
            }

            if r.code:
                invoice_lines = self.env['account.move.line'].search([
                    ('account_analytic_id', '=', r.id),
                    ('invoice_id.type', 'in', ['out_invoice', 'out_refund'])
                ])

                invoice_amount_untaxed = 0
                invoice_amount_tax = 0
                invoice_amount_total_signed = 0
                for line in invoice_lines:
                    invoice_amount_untaxed += line.price_subtotal
                    invoice_amount_tax += line.price_tax
                    invoice_amount_total_signed += line.price_subtotal_signed

                lines = self.env['account.analytic.line'].search([('account_id', '=', r.id)])

                venta = 0
                coste = 0
                coste_portes = 0
                costes_sin_portes = 0
                for l in lines:
                    if l.amount < 0:
                        if l.product_id.id in [105168, 105159, 109395, 109396]:
                            coste_portes += abs(l.amount)
                        else:
                            costes_sin_portes += abs(l.amount)
                        coste += abs(l.amount)
                    else:
                        venta += l.amount

                beneficio = venta - coste
                if coste == 0:
                    margen = 100
                else:
                    margen = (beneficio * 100) / coste if coste else 0

                values.update({
                    'invoice_amount_untaxed': invoice_amount_untaxed,
                    'invoice_amount_tax': invoice_amount_tax,
                    'invoice_amount_total_signed': invoice_amount_total_signed,
                    'venta_margenes': venta,
                    'coste_margenes': coste,
                    'coste_margenes_portes': coste_portes,
                    'coste_margenes_sin_portes': costes_sin_portes,
                    'beneficio': beneficio,
                    'margen': margen,
                })

                if invoice_lines:
                    invoice = invoice_lines[0].invoice_id

                    account_analytic_url = "/web?#action=%s&active_id=%s&model=account.analytic.line&view_type=list&menu_id=%s" % (
                        self.env.ref("analytic.account_analytic_line_action").id,
                        r.id,
                        self.env.ref("induus.menu_account_analytic_account_hojas_margenes_tree").id
                    )

                    account_invoice_url = "/web?#action=%s&id=%s&model=account.move&view_type=form&menu_id=%s" % (
                        self.env.ref("account.action_invoice_tree1").id,
                        invoice.id,
                        self.env.ref("account.menu_action_invoice_tree1").id
                    )

                    values.update({
                        'invoice_id': invoice.id,
                        'invoice_date_invoice': invoice.invoice_date,
                        'invoice_number': invoice.number,
                        'invoice_date_due': invoice.date_due,
                        'invoice_state': invoice.state,
                        'invoice_payment_mode_id': invoice.payment_mode_id.id if invoice.payment_mode_id else False,
                        'account_invoice_url': account_invoice_url,
                        'account_analytic_url': account_analytic_url,
                        'invoice_name': invoice.name
                    })

            r.update(values)


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    order_id = fields.Many2one('sale.order', string="Pedido", compute="_compute_order", store=True)
    order_confirmation_date = fields.Datetime('Fecha Pedido', compute="_compute_order", store=True)
    order_partner_id = fields.Many2one('res.partner', string="Cliente Pedido", compute="_compute_order", store=True)
    order_client_order_ref = fields.Char('Referencia Pedido', compute="_compute_order", store=True)
    invoice_id = fields.Many2one('account.move', string="Factura", compute="_compute_order", store=True)
    invoice_date_invoice = fields.Date('Fecha Factura', compute="_compute_order", store=True)
    invoice_number = fields.Char('Número Factura', compute="_compute_order", store=True)
    invoice_amount_total = fields.Monetary('Total Factura', compute="_compute_order", store=True)
    proyecto_detalle_linea_id = fields.Many2one('proyecto_detalle_linea', string="Línea proyecto detalle")

    @api.depends('account_id.code')
    def _compute_order(self):
        for r in self:
            values_order = {
                'order_id': False,
                'order_confirmation_date': False,
                'order_partner_id': False,
                'order_client_order_ref': False,
                'invoice_id': False,
                'invoice_date_invoice': False,
                'invoice_number': False,
                'invoice_amount_total': False
            }
            if r.account_id and r.account_id.code:
                order = self.env['sale.order'].search([('name', '=', r.account_id.code)], limit=1)
                if order:
                    values_order.update({
                        'order_id': order.id,
                        'order_confirmation_date': order.confirmation_date,
                        'order_partner_id': order.partner_id.id if order.partner_id else False,
                        'order_client_order_ref': order.client_order_ref,
                    })

                invoice = self.env['account.move'].search([('origin', '=', r.account_id.code)], limit=1)
                if invoice:
                    values_order.update({
                        'invoice_id': invoice.id,
                        'invoice_date_invoice': invoice.invoice_date,
                        'invoice_number': invoice.number,
                        'invoice_amount_total': invoice.amount_total,
                    })

            r.update(values_order)

    @api.depends('amount')
    def _compute_coste_margenes(self):
        for r in self:
            coste = 0
            lines = self.env['account.analytic.line'].search([
                ('account_id', '=', r.id),
                ('amount', '<', 0.0),
            ])

            for l in lines:
                coste += abs(l.amount)

            coste_margenes = abs(coste)
            beneficio = r.invoice_id.amount_untaxed - coste_margenes
            if coste_margenes == 0:
                margen = 100
            else:
                margen = beneficio * 100 / coste_margenes if coste_margenes else 0
            r.update({
                'coste_margenes': coste_margenes,
                'beneficio': beneficio,
                'margen': margen
            })

    def actualizar_cuentas_analiticas(self, code):
        account_analytic_line = self.env['account.analytic.line'].search([
            ('account_id.code', '=', code)
        ])
        if account_analytic_line:
            account_analytic_line._compute_order()

    @api.model
    def create(self, vals):
        res = super(AccountAnalyticLine, self).create(vals)
        if 'amount' in vals:
            res.account_id._compute_invoice()
        return res

#     @api.multi
    def write(self, vals):
        res = super(AccountAnalyticLine, self).write(vals)
        if 'amount' in vals:
            self.mapped('account_id')._compute_invoice()
        return res

#     @api.multi
    def unlink(self):
        accounts = self.mapped('account_id')
        res = super(AccountAnalyticLine, self).unlink()
        if accounts:
            accounts._compute_invoice()
        return res

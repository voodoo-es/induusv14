# -*- coding: utf-8 -*-
# © 2018 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    referencia_cliente = fields.Char('R. Cliente', compute="_compute_referencia_cliente", store=True)
    margin_porcentaje = fields.Float('Margen (%)', compute='_compute_margin', store=True, readonly=True)
    
    @api.depends('quantity', 'purchase_price')
    def _compute_margin(self):
        super(AccountInvoiceLine, self)._compute_margin()
        for r in self:
            coste = r.quantity * r.purchase_price
            r.margin_porcentaje = (r.margin * 100) / coste if coste else 100
    
    def lineas_para_actualizar_margen(self):
        analytic_account_ids = []
        for r in self:
            if r.analytic_account_id and r.invoice_type in ['in_invoice', 'in_refund'] and \
                r.invoice_id.state not in ['draft', 'cancel']:
                analytic_account_ids.append(r.analytic_account_id.id)
        return analytic_account_ids

    @api.depends('product_id', 'invoice_id.partner_id')
    def _compute_referencia_cliente(self):
        for r in self:
            if r.invoice_id.partner_id:
                partner = r.invoice_id.partner_id
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

    @api.multi
    def write(self, vals):
        res = super(AccountInvoiceLine, self).write(vals)
        if 'price_unit' in vals or 'quantity' in vals or 'discount' in vals or 'discount1' in vals or \
            'discount2' in vals:
            for r in self:
                if not r.purchase_line_id:
                    continue

                for sale_order in r.purchase_line_id.order_id.sale_order_ids:
                    if sale_order.analytic_account_id:
                        analytic_line = self.env['account.analytic.line'].search([
                            ('account_id', '=', sale_order.analytic_account_id.id),
                            ('product_id', '=', r.product_id.id),
                            ('amount', '<=', 0)
                        ], limit=1)
                        if analytic_line:
                            importe = (r.price_subtotal / r.quantity) * analytic_line.unit_amount
                            analytic_line.write({'amount': importe * -1})
        return res

# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api
from odoo.addons.induus.models import date_utils

_logger = logging.getLogger(__name__)


class Attachment(models.Model):
    _inherit = 'ir.attachment'

    invoice_id = fields.Many2one('account.move', string="Factura", compute="_compute_invoice", store=True)
    date_invoice = fields.Date(related="invoice_id.invoice_date", string="Fecha factura")
    invoice_reference = fields.Char(related="invoice_id.ref", string="Referencia")
    expense_id = fields.Many2one('hr.expense', string="Gasto", compute="_compute_invoice", store=True)
#     date_expense = fields.Date(related="expense_id.date", string="Fecha gasto")
    importada = fields.Boolean('Importada')

    @api.depends('res_model', 'res_id')
    def _compute_invoice(self):
        for r in self:
            if r.res_model == 'account.move' and r.res_id:
                invoice = self.env['account.move'].search([('id', '=', r.res_id)], limit=1)
                r.invoice_id = invoice.id if invoice else None
            elif r.res_model == 'hr.expense' and r.res_id:
                expense = self.env['hr.expense'].search([('id', '=', r.res_id)], limit=1)
                r.expense_id = expense.id if expense else None

    @api.model
    def create(self, vals):
        res = super(Attachment, self).create(vals)
#         if res.res_model == 'account.invoice' and res.res_id:
#             res.actualizar_etiquetas_facturas([res.res_id])

        if res.res_model == 'account.move' and res.res_id:
            res.actualizar_etiquetas_account_move([res.res_id])
            
        if res.res_model == 'hr.expense' and res.res_id:
            res.actualizar_etiquetas_gastos([res.res_id])
        return res

#     @api.multi
    def write(self, vals):
        res = super(Attachment, self).write(vals)
        if 'res_model' in vals or 'res_id' in vals:
#             facturas_adjuntos_ids = [f.res_id for f in self.filtered(lambda x: x.res_model == 'account.invoice' and x.res_id)]
#             if facturas_adjuntos_ids:
#                 self.actualizar_etiquetas_facturas(facturas_adjuntos_ids)

            move_adjuntos_ids = [f.res_id for f in self.filtered(lambda x: x.res_model == 'account.move' and x.res_id)]
            if move_adjuntos_ids:
                self.actualizar_etiquetas_account_move(move_adjuntos_ids)
                
            expense_adjuntos_ids = [f.res_id for f in self.filtered(lambda x: x.res_model == 'hr.expense' and x.res_id)]
            if expense_adjuntos_ids:
                self.actualizar_etiquetas_gastos(expense_adjuntos_ids)
        return res

    def actualizar_etiquetas_facturas(self, invoice_ids):
        fiscal_year_folder = self.env.ref("documents.documents_finance_Fiscal_year_folder")
        trimestre_facet = self.env.ref("induus.documents_facet_trimestre")
        mes_facet = self.env.ref("induus.documents_facet_mes")
        documentos_facet = self.env.ref("induus.documents_facet_documentos")

        for id in invoice_ids:
            values = {}
            attachments = self.search([
                ('res_model', '=', 'account.move'),
                ('res_id', '=', id),
            ])
            if not attachments:
                continue

            invoice = self.env['account.move'].browse(id)

            if invoice:
                tag_ids = []
                values.update({'folder_id': self.env.ref("documents.documents_finance_folder").id})

                if invoice.type == 'out_invoice':
                    tag_ids.append((4, self.env.ref("induus.documents_tag_factura_cliente").id))
                elif invoice.type == 'in_invoice':
                    tag_ids.append((4, self.env.ref("induus.documents_tag_factura_proveedor").id))
                elif invoice.type == 'out_refund':
                    tag_ids.append((4, self.env.ref("induus.documents_tag_nota_credito_cliente").id))
                elif invoice.type == 'in_refund':
                    tag_ids.append((4, self.env.ref("induus.documents_tag_nota_credito_proveedor").id))
                else:
                    tag_ids.append((4, self.env.ref("induus.documents_tag_otros").id))

                if invoice.invoice_date:
                    DocumentTag = self.env['documents.tag'].sudo()

                    ano = str(invoice.invoice_date.year)
                    tag = DocumentTag.search([('name', '=', ano)], limit=1)
                    if not tag:
                        tag = DocumentTag.create({
                            'facet_id': fiscal_year_folder.id,
                            'name': ano
                        })

                    tag_ids.append((4, tag.id))

                    mes = date_utils.nombre_mes(invoice.invoice_date)
                    tag = DocumentTag.search([('name', '=', mes)], limit=1)
                    if tag:
                        tag_ids.append((4, tag.id))

                    trimestre = None
                    if invoice.invoice_date.month >= 1 and invoice.invoice_date.month <= 3:
                        trimestre = self.env.ref("induus.documents_tag_1trimestre")
                    elif invoice.invoice_date.month >= 4 and invoice.invoice_date.month <= 6:
                        trimestre = self.env.ref("induus.documents_tag_2trimestre")
                    elif invoice.invoice_date.month >= 7 and invoice.invoice_date.month <= 9:
                        trimestre = self.env.ref("induus.documents_tag_3trimestre")
                    elif invoice.invoice_date.month >= 10 and invoice.invoice_date.month <= 12:
                        trimestre = self.env.ref("induus.documents_tag_4trimestre")

                    if trimestre:
                        tag = DocumentTag.search([('id', '=', trimestre.id)], limit=1)
                        if tag:
                            tag_ids.append((4, tag.id))

                    unlink_tag_ids = []
                    for attachment in attachments:
                        for t in attachment.tag_ids:
                            if t.facet_id.id == fiscal_year_folder.id or t.facet_id.id == trimestre_facet.id or \
                                t.facet_id.id == mes_facet.id or t.facet_id.id == documentos_facet.id:
                                unlink_tag_ids.append((3, t.id))

                        if unlink_tag_ids:
                            attachment.write({'tag_ids': unlink_tag_ids})

                    values.update({'tag_ids': tag_ids})

            if values:
                attachments.write(values)

    def actualizar_etiquetas_account_move(self, account_move_ids):
        documentos_facet = self.env.ref("induus.documents_facet_documentos")

        for id in account_move_ids:
            values = {}
            attachments = self.search([
                ('res_model', '=', 'account.move'),
                ('res_id', '=', id),
            ], limit=1)
            if not attachments:
                continue

            move = self.env['account.move'].browse(id)
            if move:
                values.update({'folder_id': self.env.ref("documents.documents_finance_folder").id})

                unlink_tag_ids = []
                for attachment in attachments:
                    for t in attachment.tag_ids:
                        if t.facet_id.id == documentos_facet.id:
                            unlink_tag_ids.append((3, t.id))

                    if unlink_tag_ids:
                        attachment.write({'tag_ids': unlink_tag_ids})

                values.update({'tag_ids': [(4, self.env.ref("induus.documents_tag_asientos").id)]})
                attachments.write(values)
                
    def actualizar_etiquetas_gastos(self, gasto_ids):
        mes_facet = self.env.ref('induus.documents_facet_gasto_mes')
        fiscal_year_folder = self.env.ref("induus.documents_gasto_Fiscal_year_folder")
        trimestre_facet = self.env.ref("induus.documents_facet_gasto_trimestre")
        gastos_folder = self.env.ref("induus.documents_folder_gastos")
        
        for id in gasto_ids:
            values = {}
            attachments = self.search([
                ('res_model', '=', 'hr.expense'),
                ('res_id', '=', id),
            ])
            if not attachments:
                continue

            expense = self.env['hr.expense'].browse(id)
            values.update({'folder_id': gastos_folder.id})
            tag_ids = []
            if expense and expense.date:
                DocumentTag = self.env['documents.tag'].sudo()

                ano = str(expense.date.year)
                tag = DocumentTag.search([
                    ('name', '=', ano),
                    ('facet_id', '=', fiscal_year_folder.id)
                ], limit=1)
                if not tag:
                    tag = DocumentTag.create({
                        'facet_id': fiscal_year_folder.id,
                        'name': ano
                    })
                tag_ids.append((4, tag.id))
                
                mes = date_utils.nombre_mes(expense.date)
                tag = DocumentTag.search([
                    ('name', '=', mes),
                    ('facet_id', '=', mes_facet.id)
                ], limit=1)
                
                if tag:
                    tag_ids.append((4, tag.id))
                    
                trimestre = None
                if expense.date.month >= 1 and expense.date.month <= 3:
                    trimestre = self.env.ref("induus.documents_tag_gasto_1trimestre")
                elif expense.date.month >= 4 and expense.date.month <= 6:
                    trimestre = self.env.ref("induus.documents_tag_gasto_2trimestre")
                elif expense.date.month >= 7 and expense.date.month <= 9:
                    trimestre = self.env.ref("induus.documents_tag_gasto_3trimestre")
                elif expense.date.month >= 10 and expense.date.month <= 12:
                    trimestre = self.env.ref("induus.documents_tag_gasto_4trimestre")

                if trimestre:
                    tag = DocumentTag.search([('id', '=', trimestre.id)], limit=1)
                    if tag:
                        tag_ids.append((4, tag.id)) 
                        
                unlink_tag_ids = []
                for attachment in attachments:
                    for t in attachment.tag_ids:
                        if t.facet_id.id == fiscal_year_folder.id or t.facet_id.id == trimestre_facet.id or \
                            t.facet_id.id == mes_facet.id or t.facet_id.id == documentos_facet.id:
                            unlink_tag_ids.append((3, t.id))

                    if unlink_tag_ids:
                        attachment.write({'tag_ids': unlink_tag_ids})
                
                values.update({'tag_ids': tag_ids})
            
            if values:
                attachments.write(values)
                

        
# -*- coding: utf-8 -*-
# © 2018 Ingetive - <info@ingetive.com>

import logging
import babel
import dateutil.parser

from odoo import models, fields, api, tools, _
from datetime import timedelta
from odoo.addons.induus.models import date_utils

_logger = logging.getLogger(__name__)


class Product(models.Model):
    _inherit = 'product.product'

    stock_previsto = fields.Float('Stock previsto', compute="_compute_stock_previsto")
    total_previsto = fields.Monetary('Total previsto', compute="_compute_stock_previsto")
    expense_policy = fields.Selection([('no', 'No'), ('cost', 'At cost'), ('sales_price', 'Sales price')], default='no')

    # @api.multi
    # def name_get(self):
    #     result = super(Product, self).name_get()
    #     if self._context.get('ref_cliente'):
    #         partner = self.env['res.partner'].browse(self._context.get('ref_cliente'))
    #         if partner:
    #             partner_ids = [partner.id]
    #             if partner.parent_id:
    #                 partner_ids.append(partner.parent_id.id)
    #
    #             if partner.child_ids:
    #                 partner_ids += partner.child_ids.ids
    #
    #             cliente_ids = self.env['induus.referencia_cliente'].search([
    #                 ('name', '=', name),
    #                 ('partner_id', 'in', partner_ids)
    #             ])
    #             product_ids = [c.product_tmpl_id.product_variant_id.id for c in cliente_ids]
    #     return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        res = super(Product, self)._name_search(name, args, operator, limit, name_get_uid)
        if res:
            return res

        product_ids = []
        if name:
            if self._context.get('ref_cliente'):
                partner = self.env['res.partner'].browse(self._context.get('ref_cliente'))
                if partner:
                    partner_ids = [partner.id]
                    if partner.parent_id:
                        partner_ids.append(partner.parent_id.id)

                    if partner.child_ids:
                        partner_ids += partner.child_ids.ids

                    cliente_ids = self.env['induus.referencia_cliente'].search([
                        ('name', operator, name),
                        ('partner_id', 'in', partner_ids)
                    ])
                    product_ids = [c.product_tmpl_id.product_variant_id.id for c in cliente_ids]

            if not product_ids and (self._context.get('partner_id') or self._context.get('parent_partner_id')):
                domain = []
                if self._context.get('partner_id') and self._context.get('parent_partner_id'):
                    domain = ['|',
                              ('name', '=', self._context.get('partner_id')),
                              ('name', '=', self._context.get('parent_partner_id'))
                              ]
                elif self._context.get('partner_id'):
                    domain = [('name', '=', self._context.get('partner_id'))]
                elif self._context.get('parent_partner_id'):
                    domain = [('name', '=', self._context.get('parent_partner_id'))]

                domain += ['|',
                    ('product_code', operator, name),
                    ('product_name', operator, name)
                ]

                suppliers_ids = self.env['product.supplierinfo']._search(domain, access_rights_uid=name_get_uid)
                if suppliers_ids:
                    product_ids = self._search([('product_tmpl_id.seller_ids', 'in', suppliers_ids)], limit=limit,
                                               access_rights_uid=name_get_uid)

        return self.browse(product_ids).name_get()

    @api.depends('standard_price')
    def _compute_stock_previsto(self):
        for r in self:
            moves = self.env['stock.move'].search([
                ('product_id', '=', r.id),
                ('reserved_availability', '>', 0)
            ])
            pendiente_entrega = 0
            for m in moves:
                pendiente_entrega += m.reserved_availability

            stock_previsto = r.qty_available - pendiente_entrega
            total_previsto = stock_previsto * r.standard_price
            r.update({
                'stock_previsto': stock_previsto,
                'total_previsto': total_previsto
            })

    def valoracion_inventario_prevista(self):
        products = self.search([])
        product_ids = [p.id for p in products if p.stock_previsto > 0]

        return {
            'name': 'Valoración inventario previsto',
            'domain': [('id', 'in', product_ids)],
            'res_model': 'product.product',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'views': [(self.env.ref('induus.product_inventario_previsto_tree').id, 'tree'),
                      (self.env.ref('product.product_normal_form_view').id, 'form')],
            'view_mode': 'tree,form',
            'view_type': 'form',
        }

    @api.model
    def create(self, vals):
        res = super(Product, self).create(vals)
        if not vals.get('default_code'):
            default_code, secuencia = res.get_secuencia_product()
            res.write({'default_code': default_code})
            company = self.env['res.company'].search([('id', '=', 1)], limit=1)
            company.write({'secuencia_productos': secuencia})
        return res
    
    def get_secuencia_product(self, sumar=0):
        self.ensure_one()
        company = self.env['res.company'].search([('id', '=', 1)], limit=1)
        secuencia = company.secuencia_productos + sumar
        default_code = 'IND'
        num_len = len(str(secuencia))
        if num_len <= 5:
            for i in range(5 - num_len):
                default_code += '0'

        default_code += '%s' % secuencia
        product = self.env['product.product'].search([('default_code', '=', default_code)], limit=1)
        if product:
            return self.get_secuencia_product(sumar+1)
        return default_code, secuencia

    def delay_website(self, cantidad=1, format="string", code_pais="ES"):
        self = self.sudo()
        if not code_pais:
            code_pais = "ES"
        FechaFestivo = self.env['induus.fecha_festivo']
        locale = self.env.context.get('lang') or 'en_US'

        def return_fecha(fecha, format, code_pais):
            if code_pais != 'ES':  # para envios fuera de españa sumamos 3 días
                fecha += timedelta(days=3)

            dias_festivos = FechaFestivo.dias_festivos_y_findes(fields.Datetime.now(), fecha)
            if dias_festivos:
                fecha += timedelta(days=dias_festivos)

            if format == 'string':
                return _("Fecha prevista de entrega: ") + tools.ustr(
                    babel.dates.format_date(date=fecha, format='full', locale=locale))
            elif format == 'days':
                return (dateutil.parser.parse(fields.Datetime.to_string(fecha)).date() - fields.Date.today()).days
            else:
                return fecha

        hay_stock = True
        if cantidad <= 0 or self.qty_available < cantidad:
            hay_stock = False
            componente_con_stock = True
            for bom in self.bom_ids.filtered(lambda p: p.product_id and p.product_id.id == self.id):
                if bom.product_qty <= 0:
                    hay_stock = False
                    break

                if bom.bom_line_ids:
                    hay_stock = True

                for bom_line in bom.bom_line_ids:
                    cantidad_pedida = (bom.product_qty * cantidad) * bom_line.product_qty
                    if cantidad_pedida > bom_line.product_id.qty_available:
                        componente_con_stock = False
                        break

                if not componente_con_stock:
                    hay_stock = False
                    break

        if not hay_stock:
            dias = int(self.sale_delay)
            if dias <= 0:
                return None
            fecha = fields.Datetime.now() + timedelta(days=dias)
            return return_fecha(fecha, format, code_pais)

        if int(date_utils.display_date(fields.Datetime.now(), '%H', self)) < 12:
            fecha = fields.Datetime.now() + timedelta(days=1)
            return return_fecha(fecha, format, code_pais)

        fecha = fields.Datetime.now() + timedelta(days=self.sale_delay_with_stock)
        return return_fecha(fecha, format, code_pais)

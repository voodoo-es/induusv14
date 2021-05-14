# -*- coding: utf-8 -*-
# © 2019 Ingetive - <info@ingetive.com>

import logging
import math

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class StockRule(models.Model):
    _inherit = 'stock.rule'

#     @api.multi
    def _prepare_purchase_order_line(self, product_id, product_qty, product_uom, values, po, partner):
        data = super(StockRule, self)._prepare_purchase_order_line(product_id, product_qty, product_uom, values, po, partner)

        if product_id.seller_ids:
            seller = product_id.seller_ids[0]
            if seller.min_qty > data['product_qty']:
                data['product_qty'] = seller.min_qty

            if data['product_qty'] > 0 and seller.multiplo:
                data['product_qty'] = math.ceil(data['product_qty'] / seller.multiplo) * seller.multiplo

        seller = product_id.with_context(force_company=values['company_id'].id)._select_seller(
            partner_id=partner,
            quantity=data['product_qty'],
            date=po.date_order and po.date_order.date(),
            uom_id=product_id.uom_po_id)

        taxes = product_id.supplier_taxes_id
        fpos = po.fiscal_position_id
        taxes_id = fpos.map_tax(taxes, product_id, seller.name) if fpos else taxes
        if taxes_id:
            taxes_id = taxes_id.filtered(lambda x: x.company_id.id == values['company_id'].id)

        price_unit = self.env['account.tax']._fix_tax_included_price_company(seller.price, product_id.supplier_taxes_id,
                                                                             taxes_id,
                                                                             values['company_id']) if seller else 0.0
        if price_unit and seller and po.currency_id and seller.currency_id != po.currency_id:
            price_unit = seller.currency_id._convert( price_unit, po.currency_id, po.company_id, po.date_order or fields.Date.today())

        data['price_unit'] = price_unit

        return data

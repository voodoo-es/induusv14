# -*- coding: utf-8 -*-
# © 2018 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    no_anadir_order = fields.Boolean('No añadir al pedido de venta al procesar')
    supplier_partner_ids = fields.One2many('res.partner', 'supplier_property_delivery_carrier_id')
    purchase_order_ids = fields.One2many('purchase.order', 'carrier_id')

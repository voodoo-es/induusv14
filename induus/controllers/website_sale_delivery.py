# -*- coding: utf-8 -*-
# © 2019 Ingetive - <info@ingetive.com>

import logging

from odoo.addons.website_sale_delivery.controllers.main import WebsiteSaleDelivery

_logger = logging.getLogger(__name__)


class WebsiteSaleDeliveryInduus(WebsiteSaleDelivery):
    def _update_website_sale_delivery_return(self, order, **post):
        result = super(WebsiteSaleDeliveryInduus, self)._update_website_sale_delivery_return(order, **post)
        currency = order.currency_id
        if order:
            result.update({'new_amount_delivery': self._format_amount(order.amount_delivery_taxincl, currency)})
        return result

# -*- coding: utf-8 -*-
# © 2018 Ingetive - <info@ingetive.com>

import logging

from odoo import models, fields, api
from odoo.addons.http_routing.models.ir_http import slug

_logger = logging.getLogger(__name__)


class ProductCategory(models.Model):
    _inherit = 'product.category'

    imprimir_etiqueta = fields.Boolean("Imprimir etiqueta", default=True,
                                       help="Imprime las etiquetas para los productos stocables")


# class ProductPublicCategory(models.Model):
#     _inherit = 'product.public.category'

#     description_top = fields.Html('Descripción Sitio web (Parte de arriba)')

#     def website_url(self):
#         self.ensure_one()
#         return slug(self)

# -*- coding: utf-8 -*-
# © 2020 Ingetive - <info@ingetive.com>

import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class PlantillaProyectoEditor(models.Model):
    _name = "induus.plantilla_proyecto_editor"
    _description = "Plantillas proyectos editor"

    name = fields.Char('Nombre')
    editor = fields.Html('Editor')
    sale_order_ids = fields.One2many('sale.order', 'plantilla_proyecto_editor_id')

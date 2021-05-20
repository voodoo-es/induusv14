# -*- coding: utf-8 -*-
# Copyright 2020 Adrián del Río <a.delrio@ingetive.com>

import logging
import unidecode

from datetime import timedelta
from odoo import api, fields, models
from odoo.addons.induus.models.induus_genei import Genei
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ImportarDetalleProyecto(models.TransientModel):
    _name = 'induus.importar_detalle_pro'
    _description = 'Importar envios'

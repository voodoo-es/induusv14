# -*- coding: utf-8 -*-
# Copyright 2019 Adrián del Río <a.delrio@ingetive.com>

import logging

from odoo import api, fields, models
from odoo.addons.induus.models.induus_genei import Genei
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ImportInvoiceImportWizard(models.TransientModel):
    _inherit = 'account.move.import.wizard'

#     @api.multi
    def _create_invoice_from_file(self, attachment):
        invoice = super(ImportInvoiceImportWizard, self)._create_invoice_from_file(attachment)
        attachment.write({'importada': True})
        _logger.warning(attachment.importada)
        invoice.write({'invoice_line_ids': None})
        invoice._onchange_partner_id()
        return invoice

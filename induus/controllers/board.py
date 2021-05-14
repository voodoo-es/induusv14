# -*- coding: utf-8 -*-
# © 2018 Ingetive - <info@ingetive.com>

import logging

from lxml import etree as ElementTree
from odoo.http import Controller, route, request
from odoo.addons.board.controllers.main import Board

_logger = logging.getLogger(__name__)


class BoardInduus(Board):

    @route('/board/add_to_dashboard', type='json', auth='user')
    def add_to_dashboard(self, action_id, context_to_save, domain, view_mode, name=''):
        model_from = None
        if context_to_save.get('params') and context_to_save['params'].get('model'):
            model_from = context_to_save['params'].get('model')

        if model_from == 'sale.order':
            action = request.env.ref('induus.open_board_sale_order_action')
        elif model_from == 'purchase.order':
            action = request.env.ref('induus.open_board_purchase_order_action')
        elif model_from == 'account.invoice':
            action = request.env.ref('induus.open_board_invoice_action')
        elif model_from == 'crm.lead':
            action = request.env.ref('induus.open_board_crm_action')
        else:
            action = request.env.ref('board.open_board_my_dash_action')

        if action and action['res_model'] == 'board.board' and action['views'][0][1] == 'form' and action_id:
            # Maybe should check the content instead of model board.board ?
            view_id = action['views'][0][0]
            board = request.env['board.board'].fields_view_get(view_id, 'form')
            if board and 'arch' in board:
                xml = ElementTree.fromstring(board['arch'])
                column = xml.find('./board/column')
                if column is not None:
                    new_action = ElementTree.Element('action', {
                        'name': str(action_id),
                        'string': name,
                        'view_mode': view_mode,
                        'context': str(context_to_save),
                        'domain': str(domain)
                    })
                    column.insert(0, new_action)
                    arch = ElementTree.tostring(xml, encoding='unicode')
                    request.env['ir.ui.view.custom'].create({
                        'user_id': request.session.uid,
                        'ref_id': view_id,
                        'arch': arch
                    })
                    return True

        return False

# -*- coding: utf-8 -*-
# from odoo import http


# class Induus(http.Controller):
#     @http.route('/induus/induus/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/induus/induus/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('induus.listing', {
#             'root': '/induus/induus',
#             'objects': http.request.env['induus.induus'].search([]),
#         })

#     @http.route('/induus/induus/objects/<model("induus.induus"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('induus.object', {
#             'object': obj
#         })

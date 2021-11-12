# -*- coding: utf-8 -*-
from odoo import http

# class FongipJuridiqueContrat(http.Controller):
#     @http.route('/fongip_juridique_contrat/fongip_juridique_contrat/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/fongip_garantie/fongip_garantie/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('fongip_garantie.listing', {
#             'root': '/fongip_garantie/fongip_garantie',
#             'objects': http.request.env['fongip_garantie.fongip_garantie'].search([]),
#         })

#     @http.route('/fongip_garantie/fongip_garantie/objects/<model("fongip_garantie.fongip_garantie"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('fongip_garantie.object', {
#             'object': obj
#         })

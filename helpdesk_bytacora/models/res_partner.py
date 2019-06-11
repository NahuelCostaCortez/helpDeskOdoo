# -*- coding: utf-8 -*-
from odoo import api, fields, models

class byta_res_partner(models.Model):

    _inherit = "res.partner"

    support_ticket_ids = fields.One2many('byta.support.ticket', 'partner_id', string='Tickets')



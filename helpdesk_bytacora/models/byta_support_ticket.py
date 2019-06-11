# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo import tools
import datetime

AVAILABLE_RATINGS = [
    ('0', 'Unratted'),
    ('1', 'Very low'),
    ('2', 'Low'),
    ('3', 'High'),
    ('4', 'Very High'),
]

class byta_support_ticket(models.Model):

    _name = "byta.support.ticket"
    _rec_name = "subject"
    _description = "Bytacora Support Ticket"
    _inherit = ['mail.thread']

    def _default_category(self):
        return self.env['ir.model.data'].get_object('helpdesk_bytacora', 'byta_ticket_tech_support')

    def user_in_session(self):
        return self.env.user.partner_id

    aplicacion = fields.Many2many('byta.support.ticket.app', string="Aplicaciones")
    attachment_ids = fields.One2many('ir.attachment', 'res_id', string="Archivos adjuntos")
    category = fields.Many2one('byta.support.ticket.categories', required=True, default= _default_category, string="Categoría")
    close_time = fields.Datetime(string="Fecha de cierre")
    color = fields.Integer('Color')
    company = fields.Char(related='partner_id.commercial_company_name', string="Empresa")
    department_id = fields.Many2one('hr.department', string='Departmento')
    description = fields.Text(required=True, string="Descripción")
    email = fields.Char(related='partner_id.email', string="Correo")
    location = fields.Char(related='partner_id.city', string="Localización") # Se obtiene a partir de partner_id
    origin_zammad = fields.Boolean("origin_zammad", default=False)
    partner_id = fields.Many2one('res.partner', string="Remitente")
    person_name = fields.Char(related='partner_id.name', string="Nombre del remitente") # Se obtiene a partir de partner_id
    priority = fields.Many2one('byta.support.ticket.priority', string="Prioridad")  # Crear valores por defecto en su modelo
    phone = fields.Char(related='partner_id.phone', string="Teléfono") # Se obtiene a partir de partner_id
    project_id = fields.Many2one('project.project', string="Proyecto") #Lo especifica el usuario, el admin o el responsable???
    rating = fields.Selection(AVAILABLE_RATINGS, string='Valorar atención recibida', index=True, default=AVAILABLE_RATINGS[0][0])
    #Con este campo accedemos al usuario responsable de la categoria del ticket
    responsible_user = fields.Many2one('res.users', string="Responsable/técnico asignado", related='category.technician')
    #responsible_user_name = fields.Char(related='responsible_user.name', string="Responsable/técnico asignado")
    ticket_number = fields.Char(string='Número de ticket')
    servidor = fields.Many2many('byta.support.ticket.server', string="Servidores")
    solution = fields.Text(string="Solución")
    subject = fields.Char(required=True, string="Asunto")
    state = fields.Selection([
            ('sin_mirar','Sin mirar'),
            ('abierto', 'Abierto'),
            ('esperando_respuesta', 'Esperando Respuesta'),
            ('cerrado', 'Cerrado'),
        ], string='Estado', index=True, readonly=True, default='sin_mirar',
        track_visibility='onchange', copy=False)
    zammad_id = fields.Integer('Zammad_id')

    @api.model
    def create(self, vals):
        new_record = super(byta_support_ticket, self).create(vals)
        new_record.ticket_number = self.env['ir.sequence'].next_by_code('byta.support.ticket')
        new_record.created_on = new_record.create_date
        if new_record.zammad_id != False:
            if new_record.partner_id == False:
                new_record.partner_id = self.env['ir.model.data'].get_object('helpdesk_bytacora', 'byta_ticket_users_unassigned')
        else:
            #Si no viene de Zammad, puede venir por correo, asi que comprobamos si tiene asignado o no partner_id
            if new_record.partner_id == False:
                new_record.partner_id = self.env.user.partner_id
        return new_record

    @api.multi
    def close_ticket(self):
        for ticket in self:
            if ticket.solution == False:
                raise ValidationError("No se puede cerrar la incidencia, no hay solución")
            ticket.state = 'cerrado'
            ticket.close_time = datetime.datetime.now()

    @api.multi
    def open_ticket(self):
        for ticket in self:
            ticket.state = 'abierto'
            ticket.close_time = False
            ticket.solution = False
			
    @api.multi
    def reassign_ticket(self):
        return {
            'name': "Reasignación de ticket",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'byta.support.ticket.clients',
            'context': {'default_associated_ticket': self.id},
            'target': 'new'
        }

    @api.multi
    def solve_ticket(self):

        return {
            'name': "Solución a la incidencia",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'byta.support.ticket.close',
            'context': {'default_ticket_id': self.id},
            'target': 'new'
        }

    @api.multi
    def open_zammad(self):

        url = "http://192.168.1.48/#ticket/zoom/"+str(self.zammad_id)

        return {
            'name': 'Go to website',
            'res_model': 'ir.actions.act_url',
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': url
        }

    @api.model
    def message_new(self, msg, custom_values=None):
        """ Overrides mail_thread message_new that is called by the mailgateway
            through message_process.
            This override creates a new ticket according to the email received.
        """
        # remove default author when going through the mail gateway. Indeed we
        # do not want to explicitly set user_id to False; however we do not
        # want the gateway user to be responsible if no other responsible is
        # found.
        self = self.with_context(default_user_id=False)

        if custom_values is None:
            custom_values = {}

        defaults = {'subject':  msg.get('subject'),'description':tools.html_sanitize(msg.get('body'))}
        #Extract the name from the from email if you can
        if "<" in msg.get('from') and ">" in msg.get('from'):
            start = msg.get('from').rindex( "<" ) + 1
            end = msg.get('from').rindex( ">", start )
            from_email = msg.get('from')[start:end]
            person_name = msg.get('from').split("<")[0]
            defaults['person_name'] = person_name
        else:
            from_email = msg.get('from')

        defaults['email'] = from_email
        #Try to find the partner using the from email. Solo pasará si from_email cogio el valor al entrar en el if anterior
        search_partner = self.env['res.partner'].sudo().search([('email','=', from_email)])
        if len(search_partner) > 0:
            defaults['partner_id'] = search_partner[0].id
        else:
            defaults['partner_id'] = self.env['ir.model.data'].get_object('helpdesk_bytacora', 'byta_ticket_users_unassigned')

        return super(byta_support_ticket, self).message_new(msg, custom_values=defaults) 

class byta_support_ticket_solution(models.TransientModel):
    _name = "byta.support.ticket.close"

    ticket_id = fields.Many2one('byta.support.ticket', string="Ticket ID")
    solution = fields.Text(string="Solución")

    def close_ticket(self):
        self.ticket_id.solution = self.solution

class byta_res_partner_clientes(models.TransientModel):
    _name = "byta.support.ticket.clients"

    associated_ticket = fields.Many2one('byta.support.ticket', string="Ticket ID")
    clients = fields.Many2one('res.partner', string="Cliente asociado al ticket")

    def reassign(self):
        self.associated_ticket.partner_id = self.clients

class byta_support_ticket_users(models.Model):
    _inherit = "res.users"

    ticket_ids = fields.One2many('byta.support.ticket', 'responsible_user', string="Tickets del usuario")
    ticket_categories = fields.One2many('byta.support.ticket.categories', 'technician', string='Categorías asignadas al técnico')

class byta_support_ticket_projects(models.Model):
    _inherit = "project.project"

    ticket_ids = fields.One2many('byta.support.ticket', 'project_id', string='Tickets')


class byta_support_ticket_categories(models.Model):
    _name = "byta.support.ticket.categories"

    name = fields.Char(required=True, translate=True, string='Category Name')
    #Cuando se crea una nueva categoría se especifica el técnico responsable
    technician = fields.Many2one('res.users', string="Tecnico Responsable")
    ticket_ids = fields.One2many('byta.support.ticket', 'category', 'Categorias')


class Department(models.Model):
    _inherit = "hr.department"

    ticket_ids = fields.One2many('byta.support.ticket', 'department_id', string='Departamentos')

class byta_support_ticket_priority(models.Model):
    _name = "byta.support.ticket.priority"

    name = fields.Char(required=True, translate=True, string='Priority Name')
    ticket_ids = fields.One2many('byta.support.ticket', 'priority', 'Prioridades')

class byta_support_ticket_server(models.Model):
    _name = "byta.support.ticket.server"

    name = fields.Char(string="Nombre")
    rol = fields.Char(string="Rol")
    funcionalidad = fields.Char(string="Funcionalidad")
    so = fields.Char(string="Sistema Operativo")
    ram = fields.Char(string="RAM")
    disco = fields.Char(string="Disco Duro")
    ticket_ids = fields.Many2many('byta.support.ticket', string="Tickets")

class byta_support_ticket_app(models.Model):
    _name = "byta.support.ticket.app"

    name = fields.Char(string='Nombre de la Aplicacion')
    ticket_ids = fields.Many2many('byta.support.ticket', string="Tickets")
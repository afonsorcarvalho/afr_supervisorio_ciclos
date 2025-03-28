# -*- encoding: utf-8 -*-
# © 2024 Afonso Carvalho


from odoo import api, fields, models
import logging
_logger = logging.getLogger(__name__)
from odoo.exceptions import UserError, ValidationError
import csv
from datetime import datetime, timezone, timedelta
import pytz
class EngcEquipment(models.Model):
    _inherit = 'engc.equipment'

    cycle_model = fields.Many2one(string='Modelo de ciclo', comodel_name='steril_supervisorio.cycle_model', ondelete='restrict')
    cycle_type_id = fields.Many2one(string='Tipo de ciclo', comodel_name='afr.cycle.type', ondelete='restrict')
    chamber_size = fields.Float(string="Volume Câmara (L)")
    





    

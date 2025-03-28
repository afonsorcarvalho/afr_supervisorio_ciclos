from odoo import models, fields, api
import logging
from datetime import datetime

_logger = logging.getLogger(__name__)

class CycleType(models.Model):
    _name = 'afr.cycle.type'
    _description = 'Tipos de Ciclo'
    _order = 'sequence,name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Campos básicos
    name = fields.Char(string='Nome', required=True, tracking=True)
    code = fields.Char(string='Código', required=True, tracking=True)
    description = fields.Text(string='Descrição', tracking=True)
    
    # Campos de controle
    sequence = fields.Integer(string='Sequência', default=10)
    active = fields.Boolean(string='Ativo', default=True, tracking=True)
    color = fields.Integer(string='Cor')
    reader_class_dataobject = fields.Char(
        string='Classe do Leitor de fita', 
        tracking=True,
        help='Nome da classe que implementa a interface de leitura de fita digital para este tipo de ciclo'
    )
    python_code = fields.Text(
        string='Código Python',
        help='Código Python a ser executado para processamento específico deste tipo de ciclo',
        tracking=True
    )
    method_name_create_cycle = fields.Char(
        string='Nome do método para criar dados do ciclo', 
        tracking=True,
        help='Nome do método que será chamado dinamicamente para criar os dados específicos do ciclo a partir da leitura da fita digital'
    )
    # Campos de interface
    form_view_id = fields.Many2one(
        'ir.ui.view', 
        string='Formulário Específico',
        domain="[('model', '=', 'afr.supervisorio.ciclos'), ('type', '=', 'form')]",
        help='Formulário específico a ser aberto para este tipo de ciclo',
        tracking=True
    )

    # Campos computados
    cycle_count = fields.Integer(
        string='Total de Ciclos',
        compute='_compute_cycle_count',
        store=True
    )

    @api.depends('cycle_type_ids')
    def _compute_cycle_count(self):
        for record in self:
            record.cycle_count = len(record.cycle_type_ids)

    # Campos relacionais
    cycle_type_ids = fields.One2many(
        'afr.supervisorio.ciclos',
        'cycle_type_id',
        string='Ciclos'
    )

    _sql_constraints = [
        ('unique_code', 'unique(code)', 'O código do tipo de ciclo deve ser único!')
    ]

    def action_view_cycles(self):
        self.ensure_one()
        action = self.env.ref('afr_supervisorio_ciclos.action_afr_supervisorio_ciclos_ciclos').read()[0]
        action.update({
            'domain': [('cycle_type_id', '=', self.id)],
            'context': {'default_cycle_type_id': self.id}
        })
        return action

    def execute_python_code(self, context=None):
        """
        Executa o código Python definido no campo python_code de forma segura.
        
        Args:
            context (dict): Contexto adicional para execução do código
            
        Returns:
            dict: Resultado da execução do código
        """
        self.ensure_one()
        if not self.python_code:
            return {'success': False, 'message': 'Nenhum código Python definido'}
            
        try:
            # Cria um ambiente isolado para execução
            local_dict = {
                'self': self,
                'env': self.env,
                'context': context or {},
                'datetime': datetime,
                'logging': logging,
                '_logger': _logger
            }
            
            # Executa o código
            exec(self.python_code, {'__builtins__': {}}, local_dict)
            
            return {
                'success': True,
                'message': 'Código executado com sucesso',
                'result': local_dict.get('result', None)
            }
        except Exception as e:
            _logger.error(f"Erro ao executar código Python: {str(e)}")
            return {
                'success': False,
                'message': f'Erro ao executar código: {str(e)}'
            } 
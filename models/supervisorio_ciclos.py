from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import logging
from ..fita_digital.data_object.dataobject_fita_digital import DataObjectFitaDigital

from ..fita_digital.reader_fita_digital.reader_fita_digital_afr13 import ReaderFitaDigitalAfr13
import re
import os
_logger = logging.getLogger(__name__)
import sys
import base64

class SupervisorioCiclos(models.Model):
    _name = 'afr.supervisorio.ciclos'
    _description = 'Supervisório de Ciclos de Esterilização, Lavagem e Desinfecção'
    _order = 'start_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _check_company_auto = True

    directory_path = "/var/lib/odoo/filestore/odoo-steriliza/ciclos/"
        
    do = DataObjectFitaDigital(directory_path=directory_path)
   
    # Campos básicos
    name = fields.Char(string='Ciclo', required=True, tracking=True)
    equipment_id = fields.Many2one('engc.equipment', string='Equipamento', required=True, tracking=True)
    equipment_nickname = fields.Char(related='equipment_id.apelido', string='Apelido do Equipamento', store=True)
    equipment_category_id = fields.Many2one(related='equipment_id.category_id', string='Categoria do Equipamento', store=True)
    cycle_type_id = fields.Many2one('afr.cycle.type', string='Tipo de Ciclo', required=True,
        domain="[('active', '=', True)]", tracking=True)
        
   
    # Campos de data/hora
    start_date = fields.Datetime(string='Data Início', default=fields.Datetime.now, tracking=True)
    end_date = fields.Datetime(string='Data Fim', tracking=True)
    duration = fields.Float(string='Duração (h)', compute='_compute_duration', store=True)
    
    # Status do ciclo
    state = fields.Selection([
        ('em_andamento', 'Em Andamento'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
        ('erro', 'Erro'),
        ('abortado', 'Abortado'),
        ('aguardando', 'Aguardando'),
        ('pausado', 'Pausado'),
    ], string='Status', default='aguardando', tracking=True)


    # Campos adicionais
    notes = fields.Text(string='Observações', tracking=True)
    operator_id = fields.Many2one('res.users', string='Operador', 
        default=lambda self: self.env.user, tracking=True,check_company=True)
    
    # Campos de arquivo
    file_path = fields.Char(
        string='Caminho do Arquivo',
        tracking=True,
        help='Caminho completo do arquivo de ciclo'
    )
    cycle_txt = fields.Text(
        string='Conteúdo do Arquivo',
        compute='_compute_cycle_txt',
        store=False,
        help='Conteúdo do arquivo de ciclo'
    )
    cycle_txt_filename = fields.Char(
        string='Nome do Arquivo TXT'
    )
    cycle_pdf = fields.Binary(
        string='PDF do Ciclo',
        attachment=True,
        tracking=True
    )
    cycle_pdf_filename = fields.Char(
        string='Nome do Arquivo PDF'
    )
    cycle_graph = fields.Binary(
        string='Gráfico do Ciclo',
        compute='compute_cycle_graph',
        store=False,
        help='Gráfico gerado a partir dos dados do ciclo'
    )
    cycle_graph_filename = fields.Char(
        string='Nome do Arquivo do Gráfico',
        default='cycle_graph.png'
    )
   
    batch_number = fields.Char(string='Número do Lote', tracking=True)
    company_id = fields.Many2one('res.company', string='Empresa', 
        default=lambda self: self.env.company)

    # Campos computados
    state_color = fields.Integer(string='Cor do Status', compute='_compute_state_color')
    is_overdue = fields.Boolean(string='Atrasado', compute='_compute_is_overdue', store=True)
    duration_planned = fields.Float(string='Duração Prevista (min)', compute='_compute_duration_planned')

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        for record in self:
            if record.start_date and record.end_date:
                duration = (record.end_date - record.start_date).total_seconds() / 3600  # Convertendo para horas
                record.duration = round(duration, 2)
            else:
                record.duration = 0.0

    @api.depends('state')
    def _compute_state_color(self):
        colors = {
            'aguardando': 4,    # azul
            'em_andamento': 3,  # verde
            'concluido': 7,     # cinza
            'cancelado': 1,     # vermelho
            'erro': 2,          # laranja
            'abortado': 1,      # vermelho
            'pausado': 4,       # azul
        }
        for record in self:
            record.state_color = colors.get(record.state, 0)

    @api.depends('start_date', 'duration')
    def _compute_is_overdue(self):
        now = fields.Datetime.now()
        for record in self:
            if record.start_date and record.duration:
                expected_end = record.start_date + timedelta(minutes=record.duration)
                record.is_overdue = now > expected_end and record.state in ['em_andamento', 'aguardando']
            else:
                record.is_overdue = False

    @api.depends('cycle_type_id')
    def _compute_duration_planned(self):
        for record in self:
            # Aqui você pode definir uma duração padrão baseada no tipo de ciclo
            record.duration_planned = 60.0  # valor padrão de 60 minutos

    @api.onchange('equipment_id')
    def _onchange_equipment(self):
        if self.equipment_id:
            self.cycle_type_id = False

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise ValidationError('A data de início não pode ser posterior à data de fim.')

    def action_start(self):
        self.ensure_one()
        if self.state != 'aguardando':
            raise UserError('Apenas ciclos em aguardo podem ser iniciados.')
        self.write({
            'state': 'em_andamento',
            'start_date': fields.Datetime.now()
        })

    def action_conclude(self):
        self.ensure_one()
        if self.state != 'em_andamento':
            raise UserError('Apenas ciclos em andamento podem ser concluídos.')
        self.write({
            'state': 'concluido',
            'end_date': fields.Datetime.now()
        })

    def action_cancel(self):
        self.ensure_one()
        if self.state in ['concluido', 'cancelado']:
            raise UserError('Este ciclo não pode ser cancelado.')
        self.write({
            'state': 'cancelado',
            'end_date': fields.Datetime.now()
        })

    def action_pause(self):
        self.ensure_one()
        if self.state != 'em_andamento':
            raise UserError('Apenas ciclos em andamento podem ser pausados.')
        self.write({'state': 'pausado'})

    def action_resume(self):
        self.ensure_one()
        if self.state != 'pausado':
            raise UserError('Apenas ciclos pausados podem ser retomados.')
        self.write({'state': 'em_andamento'})
    
    def action_ler_diretorio_ciclos(self,equipment_alias=None,data_inicial=None,data_final=None):
        #self.ensure_one()
        equipment_alias = equipment_alias or self.equipment_id.apelido
        data_inicial = data_inicial or datetime.now() - timedelta(days=365)
        data_final = data_final or datetime.now()

        lista_arquivos = self.ler_diretorio_ciclos(equipment_alias,data_inicial,data_final)
        _logger.debug(f"lista_arquivos: {lista_arquivos}")

        self.update_ciclos(lista_arquivos,equipment_alias)
    


    def update_ciclos(self,lista_arquivos,equipment_alias):

        equipment_alias = equipment_alias or self.equipment_id.apelido
        equipment_id = self.env['engc.equipment'].search([('apelido', '=', equipment_alias)], limit=1)
        if not equipment_id:
            raise UserError(f"Equipamento {equipment_alias} não encontrado")
 
        for arquivo in lista_arquivos:
            #verifica se o ciclo já existe
            _logger.debug(f"arquivo: {arquivo}")
            ciclo_name = arquivo['name'].replace('.txt','')
            ciclo = self.env['afr.supervisorio.ciclos'].search([('name', '=', ciclo_name)])
            if ciclo:
                _logger.debug(f"Ciclo {ciclo_name} já existe. Update dados do ciclo")
                continue
               
            _logger.debug(f"Ciclo {ciclo_name} sendo criado")
            self.create_new_cycle(arquivo,equipment_id)


    
        
    def _carregar_classe_leitor(self, equipment_id):
            """
            Carrega dinamicamente a classe do leitor de fita baseado no tipo de equipamento.
            
            Args:
                equipment_id: Registro do equipamento contendo a classe do leitor
                
            Returns:
                classe_leitor: Classe do leitor de fita carregada
                
            Exemplo:
                >>> equipment = self.env['engc.equipment'].browse(1)
                >>> classe_leitor = self._carregar_classe_leitor(equipment)
                >>> leitor = classe_leitor('/path/to/file.txt')
                >>> header, body = leitor.read_all()
            """
            try:
                # Obtém o nome da classe do leitor a partir do equipamento
                nome_classe_leitor = equipment_id.cycle_type_id.reader_class_dataobject or 'ReaderFitaDigitalAfr'
                base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
              
              
                sys.path.append(base_path)
               
                # Importa dinamicamente o módulo que contém a classe
                modulo = __import__(f"fita_digital.reader_fita_digital." +  re.sub(r'(?<!^)(?=[A-Z])', '_', nome_classe_leitor).lower(),fromlist=[nome_classe_leitor])
                _logger.debug(f"modulo: {modulo}")     
                
                # Obtém a classe do módulo
                classe_leitor = getattr(modulo, nome_classe_leitor)
                
                _logger.debug(f"Classe de leitor carregada: {nome_classe_leitor}")
                
            except (ImportError, AttributeError) as e:
                _logger.error(f"Erro ao carregar classe do leitor: {str(e)}. Usando leitor padrão ReaderFitaDigitalAfr13")
                # Em caso de erro, usa o leitor padrão
                classe_leitor = ReaderFitaDigitalAfr13
                
            return classe_leitor

    def create_new_cycle(self,arquivo,equipment_id):
        #self.ensure_one()
        if not equipment_id.cycle_type_id:
            raise UserError(f"Equipamento {equipment_id.name} não possui tipo de ciclo definido")
        
        cycle_type_id = equipment_id.cycle_type_id
        file_path = os.path.join(arquivo['path'], arquivo['name'])
        
        # Lê o conteúdo do arquivo PDF em modo binário
        pdf_path = file_path.replace('.txt', '.pdf')
        # try:
        #     with open(pdf_path, 'rb') as pdf_file:
        #         pdf_content = pdf_file.read()
        # except Exception as e:
        #     _logger.error(f"Erro ao ler arquivo PDF {pdf_path}: {str(e)}")
        #     pdf_content = None

        reader_class = self._carregar_classe_leitor(equipment_id)
        self.do.register_reader_fita(reader_class(file_path))
        header, body = self.do.read_all_fita()
        _logger.debug(f"header: {header}")
        _logger.debug(f"body: {body}")
        
        # Prepara os valores base
        base_values = {
            'equipment_id': equipment_id.id,
            'cycle_type_id': cycle_type_id.id,
            'file_path': file_path,
            'cycle_txt_filename': arquivo['name'],
           # 'cycle_pdf': base64.b64encode(pdf_content) if pdf_content else False,
            'cycle_pdf_filename': arquivo['name'].replace('.txt', '.pdf')
        }
        
        # Chamando método dinamicamente do cycle_type_id
        metodo_nome = cycle_type_id.method_name_create_cycle
        if not metodo_nome:
            raise UserError(f"Nome do método para criar dados do ciclo não definido para o tipo de ciclo {cycle_type_id.name}")
        
        if not hasattr(self, metodo_nome):
            raise UserError(f"Método '{metodo_nome}' não encontrado para o tipo de ciclo {cycle_type_id.name}")
        
        create_cycle_method = getattr(self, metodo_nome)
        dados = create_cycle_method(header, body, values=base_values)
        

   
                
    def ler_diretorio_ciclos(self,equipment_alias,data_inicial ,data_final):
        """
        Lê o diretório de ciclos e filtra por data.

        Args:
            equipment_alias (str): Alias do equipamento
            data_inicial (datetime|str): Data inicial para filtro. Se string, deve estar no formato 'YYYY-MM-DD'
            data_final (datetime|str): Data final para filtro. Se string, deve estar no formato 'YYYY-MM-DD'

        Returns:
            list: Lista de arquivos filtrados por data
            
        Exemplo:
            >>> ciclos.ler_diretorio_ciclos('ETO01', '2024-01-01', '2024-01-31')
            [
                {
                    'name': 'ciclo_001.txt',
                    'path': '/ciclos/ETO01',
                    'create_date': datetime(2024,1,15,10,30,0),
                    'change_date': datetime(2024,1,15,11,45,0)
                },
                {
                    'name': 'ciclo_002.txt', 
                    'path': '/ciclos/ETO01',
                    'create_date': datetime(2024,1,16,14,20,0),
                    'change_date': datetime(2024,1,16,15,10,0)
                }
            ]
        """
        # Converte data_inicial para datetime se necessário
        if isinstance(data_inicial, str):
            try:
                data_inicial = datetime.strptime(data_inicial, '%Y-%m-%d')
            except ValueError as e:
                raise UserError(f"Formato de data inicial inválido. Use YYYY-MM-DD: {str(e)}")
                
        # Converte data_final para datetime se necessário    
        if isinstance(data_final, str):
            try:
                data_final = datetime.strptime(data_final, '%Y-%m-%d')
            except ValueError as e:
                raise UserError(f"Formato de data final inválido. Use YYYY-MM-DD: {str(e)}")

        lista_arquivos = self.do.ler_diretorio_ciclos(directory=equipment_alias,extension_file_search=None,data_inicial=data_inicial,data_final=data_final)       
        
        
        return lista_arquivos
  
    @api.depends('file_path')
    def _compute_cycle_txt(self):
        for record in self:
            if record.file_path and os.path.exists(record.file_path):
                try:
                    with open(record.file_path, 'r', encoding='utf-8') as file:
                        record.cycle_txt = file.read()
                        record.cycle_txt = record.cycle_txt.replace('\x00', '')
                except Exception as e:
                    _logger.error(f"Erro ao ler arquivo TXT: {str(e)}")
                    record.cycle_txt = False
            else:
                record.cycle_txt = False
  
    @api.depends('cycle_txt')
    def compute_cycle_graph(self):
        """
        Calcula e gera o gráfico do ciclo a partir dos dados da fita digital.
        O gráfico mostra a temperatura e pressão ao longo do tempo, com marcações
        das fases do ciclo e o tempo entre cada fase.
        """
        for record in self:
            if not record.cycle_txt:
                record.cycle_graph = False
                continue
                
            try:
                import matplotlib.pyplot as plt
                import matplotlib.dates as mdates
                import io
                import base64
                
                # Cria uma figura e dois eixos com escalas diferentes
                fig, ax1 = plt.subplots(figsize=(16, 9))
                ax2 = ax1.twinx()  # Cria um segundo eixo Y compartilhando o mesmo eixo X
                
                # Registra o leitor de fita e lê os dados
                reader_class = self._carregar_classe_leitor(record.equipment_id)
                self.do.register_reader_fita(reader_class(record.file_path))
                header, body = self.do.read_all_fita()
                
                # Extrai os dados do body
                times = []
                temperatures = []
                pressures = []
                
                for row in body.get('data', []):
                    if len(row) >= 3:
                        # Usa o datetime diretamente do objeto
                        times.append(row[0])
                        pressures.append(float(row[1]))  # PCI(Bar)
                        temperatures.append(float(row[2]))  # TCI(Celsius)
                
                # Configura o formato do eixo X para mostrar HH:mm:ss
                ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
                ax1.xaxis.set_major_locator(plt.MaxNLocator(50)) # Define 50 valores no eixo X
                ax1.yaxis.set_major_locator(plt.MaxNLocator(20)) # Define 20 valores no eixo Y da temperatura
                ax2.yaxis.set_major_locator(plt.MaxNLocator(20)) # Define 20 valores no eixo Y da pressão
                
                # Rotaciona os rótulos do eixo X em 45 graus e ajusta o alinhamento
                plt.setp(ax1.get_xticklabels(), rotation=90, ha='right', fontsize=6)
                
                # Plota temperatura no eixo Y esquerdo
                color1 = '#1f77b4'  # Azul
                ax1.plot(times, temperatures, color=color1, label='Temperatura (°C)')
                ax1.set_xlabel('Tempo (HH:mm:ss)')
                ax1.set_ylabel('Temperatura (°C)', color=color1)
                ax1.tick_params(axis='y', labelcolor=color1)
                ax1.set_ylim(0, 100)  # Define escala de temperatura de 0 a 100°C
                
                # Plota pressão no eixo Y direito
                color2 = '#d62728'  # Vermelho
                ax2.plot(times, pressures, color=color2, label='Pressão (bar)')
                ax2.set_ylabel('Pressão (bar)', color=color2)
                ax2.tick_params(axis='y', labelcolor=color2)
                ax2.set_ylim(-1, 0)  # Define escala de pressão de -1 a 0 bar
                
                # Adiciona as fases como linhas verticais
                fases_permitidas = ['LEAK-TEST','ACONDICIONAMENTO','ESTERILIZACAO','LAVAGEM','AERACAO','CICLO FINALIZADO']
                fases_validas = []
                
                # Filtra apenas as fases permitidas
                for fase in body.get('fase', []):
                    if len(fase) >= 2 and fase[1] in fases_permitidas:
                        fases_validas.append(fase)
                
                # Adiciona as fases e calcula o tempo entre elas
                for i, fase in enumerate(fases_validas):
                    tempo_fase = fase[0].strftime('%H:%M:%S')
                    ax1.axvline(x=fase[0], color='g', linestyle='--', alpha=0.5)
                    
                    # Calcula o tempo até a próxima fase
                    if i < len(fases_validas) - 1:
                        tempo_entre_fases = fases_validas[i+1][0] - fase[0]
                        minutos = tempo_entre_fases.total_seconds() / 60
                        texto_fase = f"{tempo_fase} - {fase[1]}\n{int(minutos)} min"
                    else:
                        texto_fase = f"{tempo_fase} - {fase[1]}"
                        
                    ax1.text(fase[0], ax1.get_ylim()[0] + 2, 
                            texto_fase,
                            rotation=90,
                            verticalalignment='bottom',
                            fontsize=8)
                                
                # Adiciona grade
                ax1.grid(True, alpha=0.3)
                
                # Adiciona título
                plt.title('Curvas Paramétricas do Ciclo')
                
                # Adiciona legendas
                lines1, labels1 = ax1.get_legend_handles_labels()
                lines2, labels2 = ax2.get_legend_handles_labels()
                ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
                
                # Ajusta o layout para evitar sobreposição
                plt.tight_layout()
                
                # Salva o gráfico em um buffer de memória
                buf = io.BytesIO()
                plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
                buf.seek(0)
                
                # Converte para base64
                record.cycle_graph = base64.b64encode(buf.getvalue())
                
                # Fecha a figura para liberar memória
                plt.close()
                
            except Exception as e:
                _logger.error(f"Erro ao gerar gráfico: {str(e)}")
                record.cycle_graph = False
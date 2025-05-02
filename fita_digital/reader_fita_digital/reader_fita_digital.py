from abc import ABC, abstractmethod
import os
from datetime import datetime

class HeaderFields:
    date_key = "Data:"
    time_key = "Hora:"
    equipment_key = "Equipamento:"
    operator_key = "Operador:"
    cycle_code_key = "Cod. ciclo:"
    selected_cycle_key = "Ciclo Selecionado:"

class ReaderFitaDigitalInterface(ABC):
    """
    Interface para leitura de fitas digitais de equipamentos.
    
    Esta interface define os métodos necessários para ler e processar arquivos de fita digital,
    que contêm registros de ciclos de equipamentos como autoclaves e lavadoras.

    Attributes:
        file_name (str): Caminho completo do arquivo de fita digital
        
        header_fields (list): Lista dos campos do cabeçalho da fita digital
    """

    def __init__(self,full_path_file):
        """
        Inicializa o leitor de fita digital.

        Args:
            full_path_file (str): Caminho completo do arquivo a ser lido
        """
        if not full_path_file:
            raise ValueError("full_path_file não definido ao instanciar o leitor de fita digital")
        self.file_name = full_path_file
        
        # Tamanho padrão do cabeçalho em bytes
        self.size_header = 25
        
        # Lista que armazenará todas as linhas do arquivo após a leitura
        self.lines_file = []
        
        # Lista que armazenará as linhas do corpo do arquivo sem processamento
        # Útil para debug e análise do conteúdo bruto
        self.lines_body_raw = []
        
        # Dicionário que armazenará o corpo do arquivo após processamento
        # Estrutura organizada dos dados do corpo da fita digital
        self.body = {}
        
        # Instância da classe que define as chaves do cabeçalho
        # Facilita o acesso e manutenção das chaves utilizadas no cabeçalho
        self.header_fields = HeaderFields()

        self.state_finalized_keys = ["CICLO FINALIZADO", "CICLO CONCLUIDO","AERACAO"]
        self.state_aborted_keys = ["CICLO ABORTADO"]
    
        
       
  
  
    def read_file(self):
        """
        Lê o conteúdo completo do arquivo de fita.

        Returns:
            str: Conteúdo do arquivo
            
        Raises:
            FileNotFoundError: Se o arquivo não for encontrado
            IOError: Se houver erro na leitura do arquivo
        """
        try:
            print(f"Lendo o arquivo: {self.file_name}")
            with open(self.file_name, 'r') as file:
                self.lines_file = file.readlines()
                return self.lines_file
        except FileNotFoundError:
            raise FileNotFoundError(f"Arquivo não encontrado: {self.file_name}")
        except IOError as e:
            raise IOError(f"Erro ao ler o arquivo {self.file_name}: {str(e)}")

    
    def read_header(self):
        """
        Método abstrato para ler o cabeçalho da fita digital.
        Deve ser implementado pelas classes concretas.

        Args:
            size_header (int): Tamanho do cabeçalho em bytes. Padrão é 25.

        Returns:
            str: Conteúdo do cabeçalho da fita
            
        Exemplo:
            >>> reader = ReaderFitaDigital("arquivo.txt")
            >>> header = reader.read_header()
            >>> print(header)
            {
                'Data:': '13-4-2024',
                'Hora:': '17:21:17',
                'Equipamento:': 'ETO01',
                'Operador:': 'FLAVIOR', 
                'Cod. ciclo:': '7819',
                'Ciclo Selecionado:': 'CICLO 01'
            }
        """
        if self.lines_file == []:
            self.read_file()
        # Dicionário para armazenar os valores encontrados
        file_content = self.lines_file[:self.size_header]
        # Obtém informações do arquivo
        header_values = {
            'file_name': os.path.splitext(os.path.basename(self.file_name))[0],
            'create_date': datetime.fromtimestamp(os.path.getctime(self.file_name)).strftime('%d-%m-%Y %H:%M:%S'),
            'change_date': datetime.fromtimestamp(os.path.getmtime(self.file_name)).strftime('%d-%m-%Y %H:%M:%S')
        }
        
        # Itera sobre cada linha do conteúdo do arquivo
        for line in file_content:
            # Remove caracteres nulos e espaços em branco do início e fim da linha
            line = line.replace('\x00', '').strip()
            
            # Obtém todos os nomes dos campos do cabeçalho definidos na classe
            header_fields_names = [getattr(self.header_fields, attr) for attr in dir(self.header_fields) if not attr.startswith('_')]
            
            # Itera sobre cada campo do cabeçalho
            for field in header_fields_names:
                
                
                # Se o campo for encontrado na linha, extrai seu valor
                if field in line:
                    # Divide a linha no campo e pega o valor após ele, removendo espaços
                    header_values[field] = line.split(field)[1].strip()

        print(f"header_values: {header_values}")
        return header_values
    
    @abstractmethod
    def get_state(self):
        """
        Obtém o estado da fita digital.
        """
        return ""
 
    def set_header_fields(self,fields_name):
        """
        Define os campos do cabeçalho da fita.

        Args:
            fields_name (list): Lista com os nomes dos campos do cabeçalho

        Returns:
            list: Lista atualizada dos campos do cabeçalho
        """
        self.header_fields = fields_name
        return self.header_fields

    @abstractmethod
    def read_body(self):
        pass
   
    def get_fases(self, fases):
        """
        Obtém as fases do ciclo da fita digital filtrando apenas as fases enviadas como argumento.
        
        Args:
            fases (list): Lista de fases a serem filtradas
            
        Returns:
            list: Lista de fases encontradas que correspondem ao filtro
        """
        fases_filtradas = []
        if self.body.get('fase'):
            # Filtra as fases que estão na lista de fases desejadas
            fases_filtradas = [fase[1] for fase in self.body['fase'] if fase[1] in fases]
        else:
            fases_filtradas = []
        return fases_filtradas
        
    def get_parametros(self):
        """
        Obtém os parâmetros medidos na fita digital.
        
        Returns:
            list: Lista de parâmetros encontrados
        """
        parametros = []
        if self.body.get('header_columns'):
            # Pega os parâmetros do cabeçalho excluindo a primeira coluna (horas)
            parametros = self.body['header_columns'][1:]
        return parametros
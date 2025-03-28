from abc import ABC, abstractmethod
import os
from datetime import datetime

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
        self.file_name = full_path_file
        self.header_fields = ["Data:","Hora:","Ciclo:","Equipamento:","Operador:","Cod. ciclo:","Ciclo Selecionado:"]
        self.size_header = 25
        self.lines_file = []
        self.lines_body_raw = []
        self.body = {}

  
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
        
        for line in file_content:

            # Limpa caracteres nulos e espaços em branco
            line = line.replace('\x00', '').strip()
            for field in self.header_fields:
                if field in line:
                    header_values[field] = line.split(field)[1].strip()
        
        return header_values
        

 
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

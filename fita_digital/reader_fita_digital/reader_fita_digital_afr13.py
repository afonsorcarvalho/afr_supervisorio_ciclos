from .reader_fita_digital import ReaderFitaDigitalInterface
import re
from datetime import datetime
class ReaderFitaDigitalAfr13(ReaderFitaDigitalInterface):
    """
    Classe para leitura de fitas digitais do equipamento AFR.
    
    Esta classe implementa a interface ReaderFitaDigitalInterface para processar arquivos
    de fita digital específicos do equipamento AFR, extraindo informações do cabeçalho
    e dados das medições realizadas durante o ciclo.

    Attributes:
        size_header (int): Tamanho do cabeçalho em linhas
    """

    def __init__(self, full_path_file):
        """
        Inicializa o leitor de fita AFR.

        Args:
            full_path_file (str): Caminho completo do arquivo a ser lido
        """
        super().__init__(full_path_file)
        self.size_header = 24

    def _process_header_line(self, lines_body, body_dict):
        """
        Processa a linha de cabeçalho e cria um dicionário com as colunas.

        Args:
            lines_body (list): Lista com as linhas do corpo do arquivo
            body_dict (dict): Dicionário para armazenar os dados processados

        Returns:
            dict: Dicionário atualizado com as colunas do cabeçalho
        """
        # Retorna body_dict original se não houver linhas no corpo
        if not lines_body:
            return body_dict
            
        # Processa o cabeçalho se houver linhas
        header_line = lines_body[0].strip()
        body_dict['header_columns'] = header_line.split()
        return body_dict

    def _process_body_line(self, line, body_dict):
        """
        Processa uma linha do corpo do arquivo e adiciona ao dicionário de dados.

        Args:
            line (str): Linha a ser processada
            body_dict (dict): Dicionário para armazenar os dados processados

        Returns:
            dict: Dicionário atualizado com os dados da linha processada
        """
        try:
            # Regex para validar linha com hora e valores numéricos
            # Aceita hora seguida de um ou mais valores numéricos separados por espaços
            padrao = r'^(\d{2}:\d{2}:\d{2})(?:\s+(-?\d+\.?\d*))+$'
            match = re.match(padrao, line.strip())
            
            if not match:
                return body_dict
                
            valores = line.split()
            medicao = [
                float(valor) if i > 0 else valor
                for i, valor in enumerate(valores)
            ]
            body_dict['data'].append(medicao)
            
        except Exception as e:
            print(f"Erro ao processar linha de medição: {str(e)}")
            
        return body_dict

    def _process_phase_line(self, line, body_dict):
        """
        Processa uma linha de fase do ciclo e adiciona ao dicionário de dados.

        Args:
            line (str): Linha a ser processada
            body_dict (dict): Dicionário para armazenar os dados processados

        Returns:
            tuple: (bool, dict) - Indica se é uma linha de fase e o dicionário atualizado
        """
        
        try:
            # Regex para encontrar hora (HH:MM:SS) seguida de texto
            padrao = r'^(\d{2}:\d{2}:\d{2})\s+([A-Za-z0-9\s-]+)$'
            match = re.match(padrao, line.strip())
            
            if match:
                hora = match.group(1)  # Captura a hora
                fase = match.group(2).strip()  # Captura o texto após a hora e remove espaços extras
                
                # Adiciona como array ao invés de dicionário
                body_dict['fase'].append([
                    hora,
                    fase
                ])
                return True, body_dict
            
            return False, body_dict
            
        except Exception as e:
            # Log do erro para debug
            print(f"Erro ao processar linha de fase: {str(e)}")
            return False, body_dict
            
    def read_header(self):
        """
        Lê e processa o cabeçalho do arquivo de fita digital.

        Returns:
            dict: Dicionário contendo as informações do cabeçalho
        """
        header = super().read_header()
        header['Data:'] = datetime.strptime(header['Data:'], '%d-%m-%Y')
        return header

    def read_body(self):
        """
        Lê e processa o corpo do arquivo de fita digital.

        Returns:
            dict: Dicionário contendo os dados processados do arquivo, incluindo:
                - header: Colunas do cabeçalho
                - cabecalho: Informações gerais do cabeçalho
                - data: Lista de medições realizadas durante o ciclo
                - fase: Dicionário com horários e nomes das fases do ciclo
        """
        lines_body = self.read_body_lines_raw()
       
        body_dict = {}
        body_dict['data'] = []
        body_dict['fase'] = []
       
        # Processa o cabeçalho
        body_dict = self._process_header_line(lines_body, body_dict)
        
        for line in lines_body[1:]:
            line = line.strip()
            
            # Verifica se é uma linha de fase
            is_phase, body_dict = self._process_phase_line(line, body_dict)
            
            if is_phase:
                continue
                    
            # Processa linha de dados
            body_dict = self._process_body_line(line, body_dict)
            self.body = body_dict
        return self.body

    def read_body_lines_raw(self):
        """
        Lê as linhas brutas do corpo do arquivo.

        Returns:
            list: Lista contendo as linhas do corpo do arquivo
        """
        if self.lines_file == []:
            self.read_file()

        self.lines_body_raw = self.lines_file[self.size_header:]

        return self.lines_body_raw
       


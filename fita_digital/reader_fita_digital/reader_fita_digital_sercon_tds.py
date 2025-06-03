from .reader_fita_digital import ReaderFitaDigitalInterface
import re
from datetime import datetime
import os
import logging
_logger = logging.getLogger(__name__)



class ReaderFitaDigitalSerconTds(ReaderFitaDigitalInterface):
    """
    Classe para leitura de fitas digitais do equipamento Sercon TDS.
    
    Esta classe implementa a interface ReaderFitaDigitalInterface para processar arquivos
    de fita digital específicos do equipamento Sercon TDS, extraindo informações do cabeçalho
    e dados das medições realizadas durante o ciclo de termodesinfecção.

    Attributes:
        size_header (int): Tamanho do cabeçalho em linhas (padrão: 24 linhas)
    """

    def __init__(self, full_path_file):
        """
        Inicializa o leitor de fita Sercon TDS.

        Args:
            full_path_file (str): Caminho completo do arquivo a ser lido
        """
        super().__init__(full_path_file)
        self.size_header = 64

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
        print(f"lines_body: {lines_body}")
        if not lines_body:
            return body_dict
        # Processa o cabeçalho se houver linhas
        header_line = lines_body[4].strip()
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
            
            
            # Regex para encontrar o padrão: hora (HH:MM) seguido de valores numéricos
            padrao = r'^\s*(\d{2}:\d{2})\s+(\d{3}\.\d)\s+(\d{3}\.\d)\s+(\d{2}\.\d{3})\s*$'
            match = re.match(padrao, line.strip())
            
            if not match:
                return body_dict
                
            valores = line.split()
            # Adiciona ":00" ao horário (primeiro valor)
            hora_completa = valores[0] + ":00"
            medicao = [
                hora_completa if i == 0 else float(valor)
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
            # Regex para encontrar o padrão: hora (HH:MM) seguido de qualquer texto
            padrao = r'^\s*(\d{2}:\d{2})\s+-\s+(.+?)\s*$'   
            match = re.match(padrao, line.strip())
            
            if match:
                hora = match.group(1)  # Captura a hora
                # Adiciona ":00" ao horário (primeiro valor)
                hora = hora + ":00"
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
        header = header_values
        for line in file_content:

            # procurando data e hora de inicia do ciclo
            value = line.split('-')
            
            if len(value) == 3:
                if value[2].strip() ==  'INICIO DE CICLO':
                    date = value[1].strip().split('/')
                    
                    header['Data:'] = f"{date[0]}-{date[1]}-20{date[2]}"
                    header['Hora:'] = value[0].strip() + ':00'
                    break
            
            if line.strip().startswith('NUMERO LOTE'):
                header['NUMERO LOTE'] = line.split(':')[1].strip() or ''
            if line.strip().startswith('CICLO:'):
                header['CICLO'] = line.split(':')[1].strip().replace('\n', '') or ''
       

        
        
        _logger.debug(f"header: {header}")
        header[self.header_fields.date_key] = datetime.strptime(header[self.header_fields.date_key], '%d-%m-%Y')
        
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
        print(f"lines_body: {lines_body}")
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

    def get_state(self):
        """
        Obtém o estado atual do ciclo da fita digital.
        
        Este método analisa as fases registradas no ciclo para determinar seu estado final.
        O estado é determinado com base nas palavras-chave definidas em state_finalized_keys e state_aborted_keys.
        
        Returns:
            str: Estado do ciclo, podendo ser:
                - 'concluido': Quando encontra uma fase com palavras-chave de finalização
                - 'abortado': Quando encontra uma fase com palavras-chave de aborto
                - 'incompleto': Quando não encontra fases de finalização ou aborto
                - 'erro': Em caso de falha na análise
            
        Raises:
            KeyError: Se a chave 'fase' não existir no dicionário body
            AttributeError: Se houver erro ao acessar os dados da fase
            Exception: Para erros inesperados durante a análise
            
        Exemplo:
            >>> reader = ReaderFitaDigitalAfr13("arquivo.txt")
            >>> estado = reader.get_state()
            >>> print(estado)
            'concluido'
        """
        try:
            if 'fase' not in self.body:
                raise KeyError("Chave 'fase' não encontrada no dicionário body")
            self.state_finalized_keys = ["FINAL  DE CICLO"]
            self.state_aborted_keys = ["CICLO ABORTADO"]       
            # Verifica se é uma lista de fases
            if isinstance(self.body['fase'], list):
                # Procura por fases de conclusão ou cancelamento
                for fase in self.body['fase']:
                    # Verifica se a fase contém alguma das chaves de finalização
                    if any(key in fase[1] for key in self.state_finalized_keys):
                        return 'concluido'
                    # Verifica se a fase contém alguma das chaves de aborto
                    elif any(key in fase[1] for key in self.state_aborted_keys):
                        return 'abortado'
                # Se não encontrou nenhuma fase de finalização ou aborto, retorna em andamento
                return 'incompleto'
           
                
        except AttributeError as e:
            _logger.error(f"Erro ao acessar dados da fase: {str(e)}")
            return 'erro'
        except Exception as e:
            _logger.error(f"Erro inesperado ao obter estado: {str(e)}")
            return 'erro'
        
     
        
    
       


import os
import re
import logging
from datetime import datetime, timedelta
from pathlib import Path
_logger = logging.getLogger(__name__)

class DataObjectFitaDigital:
    """
    Classe para manipulação de arquivos de fita digital.

    Esta classe fornece funcionalidades para leitura e processamento de arquivos de fita digital,
    que contêm registros de ciclos de equipamentos como autoclaves e lavadoras.

    Attributes:
        directory_path (str): Caminho do diretório onde estão os arquivos de fita
        header_fita (dict): Dicionário com informações do cabeçalho da fita
        body_fita (dict): Dicionário com dados do corpo da fita

    Example:
        >>> # Criando uma instância
        >>> do = DataObjectFitaDigital("/caminho/para/ciclos/")
        >>> 
        >>> # Lendo arquivos de um diretório específico
        >>> arquivos = do.ler_diretorio_ciclos("ETO01")
        >>> 
        >>> # Registrando um leitor de fita
        >>> do.register_reader_fita(ReaderFitaDigitalAfr("/caminho/completo/arquivo.txt"))
        >>> 
        >>> # Lendo dados da fita
        >>> header, body = do.read_all_fita()
    """

    def __init__(self, directory_path=""):
        """
        Inicializa o objeto de manipulação de fita digital.

        Args:
            directory_path (str): Caminho do diretório dos arquivos. Não pode ser vazio.

        Raises:
            ValueError: Se directory_path estiver vazio
        """
        if not directory_path:
            raise ValueError("O caminho do diretório (directory_path) deve ser fornecido")
        self.directory_path = directory_path
        self.header_fita = {}
        self.body_fita = {}
        self.header_fields = ["Data:","Hora:","Ciclo:","Equipamento:","Operador:","Cod. ciclo:","Ciclo Selecionado:"]
        self.size_header = 25
        self.lines_file = []
        self.lines_body_raw = []
        self.body = {}

    def ler_diretorio_ciclos(self, directory="", extension_file_search=None, data_inicial=None, data_final=None):
        """
        Método para leitura recursiva de diretório de ciclos com filtro por data.

        Args:
            directory (str): Nome do diretório
            extension_file_search (list): Lista de extensões para filtrar. Se None, usa [".txt"]
            data_inicial (datetime): Data inicial para filtro (opcional)
            data_final (datetime): Data final para filtro (opcional)

        Returns:
            list: Lista de arquivos encontrados e filtrados por data
            
        Exemplo:
            >>> do = DataObjectFitaDigital("/ciclos/")
            >>> arquivos = do.ler_diretorio_ciclos(
            ...     "ETO01", 
            ...     data_inicial=datetime(2024,1,1),
            ...     data_final=datetime(2024,1,31)
            ... )
        """
        arquivos = []
        
        # Define extensão padrão se None
        if extension_file_search is None:
            extension_file_search = [".txt"]
        
        # Usa pathlib para manipulação de caminhos
        base_path = Path(self.directory_path) / directory
        
        # Verifica se o diretório existe
        if not base_path.exists():
            return arquivos
            
        # Se data_inicial não fornecida mas data_final sim, não precisa filtrar por data inicial
        # Se data_final não fornecida mas data_inicial sim, usa data atual como final
        if data_inicial and not data_final:
            data_final = datetime.now()
            
        # Itera recursivamente sobre todos os arquivos em todos os subdiretórios
        for arquivo in base_path.rglob("*"):
            if not arquivo.is_file():
                continue
        
            # Verifica extensões
            if extension_file_search and not any(str(arquivo).endswith(ext) for ext in extension_file_search):
                continue
                
            try:
                # Obtém datas de criação e modificação
                create_date = datetime.fromtimestamp(os.path.getctime(arquivo))
                change_date = datetime.fromtimestamp(os.path.getmtime(arquivo))
                
                # Só aplica filtro de data se alguma data foi fornecida
                if data_inicial or data_final:
                    if data_inicial and change_date < data_inicial:
                        continue
                    if data_final and change_date > data_final:
                        continue
                    
                arquivo_info = {
                    'name': arquivo.name,
                    'path': str(arquivo.parent),
                    'create_date': create_date, 
                    'change_date': change_date
                }
                arquivos.append(arquivo_info)
                
            except Exception:
                continue

        return arquivos
    def _cut_header_fita(self,file_name, size_header=25 ):
        """
        Extrai o cabeçalho de um arquivo de fita.

        Args:
            file_name (str): Nome do arquivo
            size_header (int): Tamanho do cabeçalho em bytes

        Returns:
            str: Conteúdo do cabeçalho
        """
        with open(self.directory_path + file_name, 'r') as file:
            header = file.read(size_header)
            return header
    
    def _read_file_fita(self,file_name, size_header=25 ):
        """
        Lê um arquivo de fita completo.

        Args:
            file_name (str): Nome do arquivo
            size_header (int): Tamanho do cabeçalho
        """
        _cut_header = self._cut_header_fita(file_name, size_header)
    
    def register_reader_fita(self, reader_fita):
        """
        Registra um leitor de fita para processamento.

        Args:
            reader_fita (ReaderFitaInterface): Instância do leitor de fita
            
        Exemplo:
            >>> do = DataObjectFitaDigital("/caminho/para/ciclos/")
            >>> do.register_reader_fita(ReaderFitaDigitalAfr("arquivo.txt"))
        """
        self.reader_fita = reader_fita

    def read_body_fita(self):
        """
        Lê e processa o corpo da fita digital, convertendo os horários para objetos datetime.

        Returns:
            dict: Dicionário contendo os dados processados do corpo da fita com:
                - header_columns: Lista com os nomes das colunas
                - data: Lista de medições com horários convertidos para datetime
                - fase: Lista de fases do ciclo
                
        Raises:
            ValueError: Se o cabeçalho não foi lido previamente
            Exception: Para erros durante a leitura ou processamento dos dados
            
        Exemplo:
            >>> do = DataObjectFitaDigital("/caminho/para/ciclos/")
            >>> do.register_reader_fita(ReaderFitaDigitalAfr("arquivo.txt"))
            >>> body = do.read_body_fita()
            >>> print(body)
            {
                'header_columns': ['Hora', 'PCI(Bar)', 'TCI(Celsius)', 'UR(%)', 'ETO(Kg)'],
                'data': [
                    [datetime(2024,1,1,14,28,34), 0.000, 49.80, 50, 0.0],
                    [datetime(2024,1,1,14,29,07), -0.120, 49.90, 51, 0.0],
                ],
                'fase': [
                    [datetime(2024,1,1,14,28,36), 'LEAK-TEST'],
                    [datetime(2024,1,1,14,41,03), 'ACONDICIONAMENTO']
                ]
            }
        """
        try:
            # Verifica se o cabeçalho foi lido
            if not self.header_fita:
                self.read_header_fita()
                
            # Lê o corpo da fita
            self.body_fita = self.reader_fita.read_body()
            
            # Valida se há dados para processar
            if not self.body_fita or 'data' not in self.body_fita:
                raise ValueError("Não foram encontrados dados válidos no corpo da fita")
                
            # Extrai e converte os horários para datetime
            horarios = [linha[0] for linha in self.body_fita['data']]
            times = self.time_to_datetime(horarios, self.header_fita['Data:'])
            
            # Atualiza os horários no body_fita['data']
            for i, time in enumerate(times):
                self.body_fita['data'][i][0] = time

            # Converte os horários das fases para datetime
            if 'fase' in self.body_fita:
                horarios_fase = [fase[0] for fase in self.body_fita['fase']]
                times_fase = self.time_to_datetime(horarios_fase, self.header_fita['Data:'])
                
                # Atualiza os horários no body_fita['fase']
                for i, time in enumerate(times_fase):
                    self.body_fita['fase'][i][0] = time
                
            _logger.debug(f"Processados {len(times)} registros de medição")
            
            return self.body_fita
            
        except ValueError as e:
            raise ValueError(f"Erro ao processar dados da fita: {str(e)}")
        except Exception as e:
            raise Exception(f"Erro inesperado ao ler corpo da fita: {str(e)}")
    def read_header_fita(self):
        """
        Lê o cabeçalho da fita digital.

        Returns:
            dict: Dados do cabeçalho da fita
            
        Exemplo:
            >>> do = DataObjectFitaDigital("/caminho/para/ciclos/")
            >>> do.register_reader_fita(ReaderFitaDigitalAfr("arquivo.txt"))
            >>> header = do.read_header_fita()
            >>> print(header)
            {
                'Data:': '2-10-2024',
                'Hora:': '14:28:34', 
                'Equipamento:': 'ETO01',
                'Operador:': 'JONATHAN',
                'Cod. ciclo:': 'ETO0102102406',
                'Ciclo Selecionado:': 'CICLO 01'
            }
        """
        self.header_fita = self.reader_fita.read_header()
        return self.header_fita

    def read_all_fita(self):
        """
        Lê o cabeçalho e corpo da fita digital.

        Returns:
            tuple: (header_fita, body_fita) contendo os dados completos da fita
            
        Exemplo:
            >>> do = DataObjectFitaDigital("/caminho/para/ciclos/")
            >>> do.register_reader_fita(ReaderFitaDigitalAfr("arquivo.txt"))
            >>> header, body = do.read_all_fita()
            >>> print(header)
            {
                'Data:': '2-10-2024',
                'Hora:': '14:28:34',
                'Equipamento:': 'ETO01',
                'Operador:': 'JONATHAN',
                'Cod. ciclo:': 'ETO0102102406',
                'Ciclo Selecionado:': 'CICLO 01'
            }
            >>> print(body)
            {
                'header_columns': ['Hora', 'PCI(Bar)', 'TCI(Celsius)', 'UR(%)', 'ETO(Kg)'],
                'data': [
                    ['14:28:34', 0.000, 49.80, 50, 0.0],
                    ['14:28:36', -0.120, 49.90, 51, 0.0]
                ],
                'fase': [
                    ['14:28:36', 'LEAK-TEST'],
                    ['14:41:03', 'ACONDICIONAMENTO']
                ]
            }
        """
        self.read_header_fita()
        self.read_body_fita()
        return self.header_fita, self.body_fita

    def _converter_horario_para_minutos(self, horario):
        """
        Converte um horário no formato HH:MM:SS para minutos totais.
        
        Args:
            horario (str): Horário no formato HH:MM:SS
            
        Returns:
            float: Total de minutos
        """
        h, m, s = map(int, horario.split(':'))
        return h * 60 + m + s/60

    def _formatar_tempo(self, minutos_totais):
        """
        Formata minutos totais para o formato HH:MM:SS.
        
        Args:
            minutos_totais (float): Total de minutos
            
        Returns:
            str: Tempo formatado como HH:MM:SS
        """
        horas = int(minutos_totais // 60)
        minutos = int(minutos_totais % 60)
        segundos = int((minutos_totais * 60) % 60)
        return f"{horas:02d}:{minutos:02d}:{segundos:02d}"

    def calcular_tempo_entre_fases(self, indice_inicial, indice_final):
        """
        Calcula o tempo decorrido entre duas fases do ciclo.

        Args:
            indice_inicial (int): Índice da fase inicial
            indice_final (int): Índice da fase final

        Returns:
            str: Tempo decorrido no formato "HH:MM:SS" entre as fases

        Raises:
            IndexError: Se os índices estiverem fora do intervalo válido
            ValueError: Se não for possível converter os horários ou se indice_inicial > indice_final
        """
        try:
            if not self.body_fita or 'fase' not in self.body_fita:
                raise ValueError("Dados da fita não foram carregados")

            if indice_inicial > indice_final:
                raise ValueError("O índice inicial deve ser menor que o índice final")

            fases = self.body_fita['fase']
            
            if not (0 <= indice_inicial < len(fases) and 0 <= indice_final < len(fases)):
                raise IndexError("Índices fora do intervalo válido")

            minutos_inicial = self._converter_horario_para_minutos(fases[indice_inicial][0])
            minutos_final = self._converter_horario_para_minutos(fases[indice_final][0])

            if minutos_final < minutos_inicial:
                minutos_final += 24 * 60

            return self._formatar_tempo(minutos_final - minutos_inicial)

        except (IndexError, ValueError) as e:
            raise e
        except Exception as e:
            raise Exception(f"Erro ao calcular tempo entre fases: {str(e)}")

    def calcular_tempo_total_ciclo(self):
        """
        Calcula o tempo total do ciclo usando a diferença entre o último e primeiro registro.

        Returns:
            str: Tempo total no formato "HH:mm:ss"

        Raises:
            ValueError: Se os dados da fita não foram carregados
            Exception: Para outros erros durante o cálculo
        """
        try:
            if not self.body_fita or 'data' not in self.body_fita:
                raise ValueError("Dados da fita não foram carregados")

            dados = self.body_fita['data']
            if not dados:
                raise ValueError("Não há dados de medição disponíveis")

            # Como os tempos já são datetime, basta subtrair o último do primeiro
            tempo_total = dados[-1][0] - dados[0][0]
            _logger.debug(f"tempo_total: {tempo_total}")
            # Converte a diferença de tempo para o formato HH:MM:SS
            horas = int(tempo_total.total_seconds() // 3600)
            minutos = int((tempo_total.total_seconds() % 3600) // 60)
            segundos = int(tempo_total.total_seconds() % 60)
            
            return f"{horas:02d}:{minutos:02d}:{segundos:02d}"

        except ValueError as e:
            raise e
        except Exception as e:
            raise Exception(f"Erro ao calcular tempo total do ciclo: {str(e)}")
    def time_to_datetime(self,times,start_date):
        """
        Converte uma lista de strings de horários para objetos datetime, 
        adicionando a data de início fornecida.

        Args:
            times (list): Lista de strings no formato "HH:MM:SS" representando horários
            start_date (datetime): Data inicial a ser combinada com os horários

        Returns:
            list: Lista de objetos datetime com a data e horários combinados

        Exemplo:
            >>> times = ["10:30:00", "11:45:00"]
            >>> start_date = datetime(2024,1,1)
            >>> time_to_datetime(times, start_date)
            [datetime(2024,1,1,10,30,0), datetime(2024,1,1,11,45,0)]
        """
        time_objects = [datetime.strptime(t, "%H:%M:%S") for t in times]
        time_objects = self.replace_date_in_times(time_objects, start_date.strftime("%Y-%m-%d"))
        return time_objects

    def replace_date_in_times(self,time_objects, specific_date):
            """
            Substitui o ano, mês e dia em uma lista de objetos datetime por uma data específica.

            Args:
                time_objects (list): Lista de objetos datetime contendo apenas horas, minutos e segundos.
                specific_date (str): String representando a data no formato "%Y-%m-%d".

            Returns:
                list: Lista de objetos datetime com a data especificada e as horas originais.
            """
            # Converte a data específica para um objeto datetime
            date_object = datetime.strptime(specific_date, "%Y-%m-%d")

            # Substitui ano, mês e dia em cada objeto de tempo
            updated_datetimes = [
                t.replace(year=date_object.year, month=date_object.month, day=date_object.day)
                for t in time_objects
            ]
            total_time = timedelta()
            days_elapsed = 0
            for i in range(1, len(updated_datetimes)):
                updated_datetimes[i] += timedelta(days=days_elapsed) 
                if updated_datetimes[i]  < updated_datetimes[i - 1]:
                    days_elapsed +=1
                    print(days_elapsed)
                    updated_datetimes[i] += timedelta(days=1)

            return updated_datetimes




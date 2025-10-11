from .reader_fita_digital import ReaderFitaDigitalInterface
import re
from datetime import datetime,timedelta
import os
import logging
_logger = logging.getLogger(__name__)



class ReaderFitaDigitalBaumerHivac2(ReaderFitaDigitalInterface):
    """
    Classe para leitura de fitas digitais do equipamento Baumer Hivac 2.
    
    Esta classe implementa a interface ReaderFitaDigitalInterface para processar arquivos
    de fita digital específicos do equipamento Baumer Hivac 2, extraindo informações do cabeçalho
    e dados das medições realizadas durante o ciclo de autoclave.
    """
    
    def __init__(self, full_path_file):
        """
        Inicializa o leitor de fita Baumer Hivac 2.
        
        Args:
            full_path_file (str): Caminho completo do arquivo a ser lido
        """
        super().__init__(full_path_file)
        self.size_header = 17
        self.state_finalized_keys = ["FIM DE CICLO"]
        self.header_fields.date_key = "DATA:"
        self.header_fields.time_key = "HORA:"
        self.format_date = "%d-%m-%Y HH:mm:SS"
        
        self.header_fields.cycle_code_key = "CODIGO DE CARGA:"
        self.header_fields.selected_cycle_key = "PROGRAMA"

    def _process_header_line(self, lines_body, body_dict):
       
        """
        Processa a linha de cabeçalho e cria um dicionário com as colunas.
        """
        # Retorna body_dict original se não houver linhas no corpo
      
        if not lines_body:
            return body_dict
        # Processa o cabeçalho se houver linhas
        header_line = ''
        # Percorre as linhas do corpo para encontrar os cabeçalhos e as grandezas
        header_line = ''
        header_line_grandezas = ''
        for line in lines_body:
            if line.strip().startswith('HORA'):
                header_line = line
            if line.strip().startswith('barA'):
                header_line_grandezas = line
                break  # Encontrou ambos, pode sair do loop

        # Processa os cabeçalhos e as grandezas, concatenando conforme solicitado
        header_line = header_line.strip()
        header_line_grandezas = header_line_grandezas.strip()
     
        # Divide as linhas em listas de colunas
        header_cols = header_line.split()
        grandezas_cols = header_line_grandezas.split()
        # Concatena os nomes das colunas com as grandezas, exceto o primeiro item (HORA)
        header_columns = []
        if header_cols and grandezas_cols:
            # O primeiro item é 'HORA', que não tem grandeza
            header_columns.append(header_cols[0])
            # Os demais são concatenados com as grandezas
            for i in range(1, len(header_cols)):
               # if i < len(grandezas_cols):
                header_columns.append(f"{header_cols[i]}({grandezas_cols[i-1]})")
               
        else:
            header_columns = header_cols  # fallback se não encontrar as grandezas

        body_dict['header_columns'] = header_columns
        header_line = header_line.strip()
      
        
        body_dict['header_columns'] = header_columns
        return body_dict
    
    def _process_body_line(self, line, body_dict):
        """
        Processa a linha de corpo e cria um dicionário com as colunas.
        """
        try:
            
            
            # Regex para validar linha com hora e valores numéricos com vírgulas
            # Regex para reconhecer linhas do tipo:
            # 15:52:20 1.43 107.2 106.8
            # ou seja, hora (HH:MM:SS) seguido de três valores numéricos (podem ser inteiros ou floats, separados por espaço)
            padrao = r'^\s*(\d{2}:\d{2}:\d{2})\s+([-+]?\d+(?:[.,]\d+)?)\s+([-+]?\d+(?:[.,]\d+)?)\s+([-+]?\d+(?:[.,]\d+)?)\s*$'
            match = re.match(padrao, line.strip())
            
            
            if not match:
                return body_dict
                
            valores = match.groups()
            
            
            # Adiciona ":00" ao horário (primeiro valor)
            hora_completa = valores[0] 
            medicao = [
                hora_completa if i == 0 else float(valor.replace(',', '.'))
                for i, valor in enumerate(valores)
            ]
            body_dict['data'].append(medicao)
          
        except Exception as e:
            print(f"Erro ao processar linha de medição: {str(e)}")
            
        return body_dict
    def _process_phase_line(self, line, body_dict, index, lines_body):
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
            # Padrão para capturar linhas do tipo "hh:MM:SS OPERACAO [NUM]: STR"
            # Exemplo: 16:10:13 OPERACAO 3: SECAGEM
            padrao = r'^(\d{2}:\d{2}:\d{2})\s+OPERACAO\s+(\d+):\s+(.+)$'
            match = re.match(padrao, line.strip())
            
            # Novo padrão para capturar apenas texto puro na fase, sem números float ou horas extras
            # Exemplo de linha que queremos capturar: "INICIO TEMPO DE ESTERILIZACAO"
            padrao2 = r'^([A-Z\s]+)$'
            match2 = re.match(padrao2, line.strip())
            
            padrao3 = r'^([A-Z\s]+)(\d{2}:\d{2}:\d{2})$'
            match3 = re.match(padrao3, line.strip())
            
            if match:
                print(match)
                fase = match.group(2).strip()+" "+match.group(3).strip()  # Captura a fase
                hora = match.group(1).strip()  # Captura a hora
               
                
                # Adiciona como array ao invés de dicionário
                body_dict['fase'].append([
                    hora,
                    fase
                ])
                return True, body_dict
            elif match2:
                fase = match2.group(1).strip()  # Captura a hora
                hora = lines_body[index+2].split()[0]
                body_dict['fase'].append([
                    hora,
                    fase
                ])
                return True, body_dict
            elif match3:
                fase = match3.group(1).strip()  # Captura a hora
                hora = match3.group(2).strip()  # Captura a hora
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
        
        # Obtém informações do arquivo
        
        header_values = super().read_header()
       
        # Converte a data para o formato DD-MM-YYYY conforme solicitado
        # Supondo que a data original esteja no formato 'D-M-YYYY' ou 'DD-MM-YYYY'
        from datetime import datetime
        data_original = header_values['DATA:'].split(' ')[0]
        try:
            # Tenta converter para datetime e depois para o formato desejado
            data_convertida = datetime.strptime(data_original, "%d/%m/%Y")
        except Exception:
                # Se não conseguir converter, mantém o valor original
                data_convertida = data_original
        header_values['DATA:'] = data_convertida
      
        
        
        return header_values

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
        
        for index,line in enumerate(lines_body[1:]):
            line = line.strip()
            
            # Verifica se é uma linha de fase
            is_phase, body_dict = self._process_phase_line(line, body_dict, index, lines_body)
            
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
        Obtém o estado atual do ciclo da fita digital (Baumer Hivac 2).

        Procura por uma linha no formato 'FIM DE CICLO [hora]' nos dados brutos do body da fita.
        Se encontrar, retorna 'concluido'. 
        Caso não encontre, retorna 'incompleto'. 
        Em caso de falha, retorna 'erro'.

        Returns:
            str: Estado do ciclo, podendo ser:
                - 'concluido': Quando encontra a linha "FIM DE CICLO [hora]" no body bruto
                - 'incompleto': Quando não encontra essa linha
                - 'erro': Em caso de falha
        """
        try:
            # Verifica se temos acesso aos dados brutos do body da fita
            if not hasattr(self, 'lines_body_raw') or not self.lines_body_raw:
                # Garante que as linhas brutas do body sejam lidas
                self.read_body_lines_raw()
            # Procura pela linha que começa exatamente com "FIM DE CICLO " seguido por uma hora (HH:MM:SS)
            padrao = r'^FIM DE CICLO\s+\d{2}:\d{2}:\d{2}$'
            for line in self.lines_body_raw:
                if re.match(padrao, line.strip()):
                    return 'concluido'
            return 'incompleto'
        except Exception as e:
            _logger.error(f"Erro ao determinar estado do ciclo: {str(e)}")
            return 'erro'
        
    def make_graph(self, header, body):
        """
        Gera um gráfico do ciclo de termodesinfecção.

        Este método cria uma visualização gráfica do ciclo de termodesinfecção,
        mostrando as curvas de temperatura e pressão ao longo do tempo, além
        de marcar as fases importantes do ciclo.

        Args:
            header (dict): Dicionário com informações do cabeçalho da fita
            body (dict): Dicionário com dados do corpo da fita

        Returns:
            bytes: Imagem do gráfico em formato base64

        Raises:
            Exception: Se houver erro na geração do gráfico
        """
        try:
            import matplotlib.pyplot as plt
            import matplotlib.dates as mdates
            import io
            import base64
            
            # Cria uma figura e dois eixos com escalas diferentes
            fig, ax1 = plt.subplots(figsize=(16, 9))
            ax2 = ax1.twinx()  # Cria um segundo eixo Y compartilhando o mesmo eixo X
            
            # Extrai os dados do body
            times = []
            measures = [[],[],[]]
           
            
            for row in body.get('data', []):
                
                if len(row) >= 3:
                    times.append(row[0])
                    measures[0].append(float(row[1]))
                    measures[1].append(float(row[2]))
                    measures[2].append(float(row[3]))
                                       
            
                   


            # Configura o formato do eixo X para mostrar HH:mm:ss
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
            ax1.xaxis.set_major_locator(plt.MaxNLocator(50))
            ax1.yaxis.set_major_locator(plt.MaxNLocator(20))
            ax2.yaxis.set_major_locator(plt.MaxNLocator(20))
            # Configura os limites dos eixos Y conforme solicitado:
            # Temperatura e Umidade: 0 a 100
            # Pressão: -0.600 a 0.100
            ax1.set_ylim(0, 150)      # Temperatura (°C) e Umidade (%) de 0 a 100
            ax2.set_ylim(-1, 4)  # Pressão (bar) de -0.600 a 0.100
            # Rotaciona os rótulos do eixo X
            plt.setp(ax1.get_xticklabels(), rotation=90, ha='right', fontsize=10)
            
            # Plota temperatura no eixo Y esquerdo
            color1 = '#1f77b4'  # Azul
            ax1.plot(times, measures[1], color=color1, label='Temperatura T1 (°C)')
            
            # Plota umidade no mesmo eixo Y esquerdo, com cor diferente
            color3 = '#2ca02c'  # Verde
            ax1.plot(times, measures[2], color=color3, label='Temperatura T2 (°C)')
            
            ax1.set_xlabel('Tempo (HH:mm:ss)')
            ax1.set_ylabel('Temperatura (°C)', color=color1)
            ax1.tick_params(axis='y', labelcolor=color1)
           
            
            # Plota pressão no eixo Y direito
            color2 = '#d62728'  # Vermelho
            ax2.plot(times, measures[0], color=color2, label='Pressão (bar)')
            ax2.set_ylabel('Pressão (bar)', color=color2)
            ax2.tick_params(axis='y', labelcolor=color2)
            #ax2.set_ylim(0, 2.5)  # Escala de pressão
            
            # Adiciona as fases como linhas verticais
            fases_permitidas = [
                '1 PULSOS DE VACUO',
                'PULSO DE VACUO',
                '2 ESTERILIZACAO',
                'INICIO TEMPO DE ESTERILIZACAO',
                '3 SECAGEM',
                '4 AERACAO',
                'FIM DE CICLO'
               
               
            ]
            
            fases_validas = []
            for fase in body.get('fase', []):
                if len(fase) >= 2 and fase[1] in fases_permitidas:
                    fases_validas.append(fase)
            
            # Adiciona as fases e calcula o tempo entre elas
            for i, fase in enumerate(fases_validas):
                tempo_fase = fase[0].strftime('%H:%M:%S')
                ax1.axvline(x=fase[0], color='grey', linestyle='--', alpha=0.5,linewidth=2)
                
                # Calcula o tempo até a próxima fase
                if i < len(fases_validas) - 1:
                    tempo_entre_fases = fases_validas[i+1][0] - fase[0]
                    segundos_totais = tempo_entre_fases.total_seconds()
                    minutos = int(segundos_totais // 60)
                    segundos = int(segundos_totais % 60)
                    texto_fase = f"{tempo_fase} - {fase[1]} --- {minutos:02d} min {segundos:02d} seg"
                else:
                    texto_fase = f"{tempo_fase} - {fase[1]}"
                
               
                    
                ax1.text(fase[0]+timedelta(seconds=15), ax1.get_ylim()[0] + 2,
                        texto_fase,
                        rotation=90,
                        verticalalignment='bottom',
                        fontsize=9)
           
            
            # if fases:
            #     esterilizando = fases.get('ESTERILIZANDO')
            #     if esterilizando:
            #         texto_fase = f"{esterilizando[0].strftime('%H:%M:%S')}"
            #         ax1.text(esterilizando[0]+timedelta(seconds=15), ax1.get_ylim()[0] + 2,
            #                 texto_fase,
            #                 verticalalignment='bottom',
            #                 fontsize=8)
           
            # Adiciona grade
            ax1.grid(True, alpha=0.5,linewidth=1)

            #Adiciona set-point
           
            #ax1.axhline(y=header.get('SETPOINT', 0), color='black', linestyle='--', label=f'Set-Point: {header.get("SETPOINT", 0)}')
            
            # Adiciona título
            plt.title(f'Curvas Paramétricas do Ciclo - {header.get("file_name", "Ciclo")}')
            
            # Adiciona legendas
            lines1, labels1 = ax1.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
            
            # Ajusta o layout
            plt.tight_layout()
            
            # Salva o gráfico em um buffer de memória
            buf = io.BytesIO()
            plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
            buf.seek(0)
            
            # Converte para base64
            cycle_graph = base64.b64encode(buf.getvalue())
            
            # Fecha a figura para liberar memória
            plt.close()
            return cycle_graph
                
        except Exception as e:
            _logger.error(f"Erro ao gerar gráfico: {str(e)}")
            cycle_graph = False
            return cycle_graph
    
       


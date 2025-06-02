# Importando as classes necessárias
from data_object.dataobject_fita_digital import DataObjectFitaDigital
from reader_fita_digital.reader_fita_digital_afr13 import ReaderFitaDigitalAfr13
from reader_fita_digital.reader_fita_digital_sercon_tds import ReaderFitaDigitalSerconTds

dir_path = "/home/afonso/docker/odoo_engenapp/data/odoo/filestore/odoo-steriliza/ciclos_processados/TERMO01/"
#dir_path = "/home/afonso/docker/odoo_engenapp/data/odoo/filestore/odoo-steriliza/Ciclos/ETO01/"
# Criando uma instância do DataObjectFitaDigital apontando para o diretório dos ciclos
do = DataObjectFitaDigital(directory_path=dir_path)
modulo = __import__('reader_fita_digital.reader_fita_digital_sercon_tds')
#modulo = __import__('reader_fita_digital.reader_fita_digital_afr13')
# Lendo os arquivos do diretório ETO01
lista_arquivos = do.ler_diretorio_ciclos(directory_path=dir_path)
print(lista_arquivos)
#print(lista_arquivos[2]['path'] +"/" + lista_arquivos[2]['name'])

# Registrando o leitor de fita para o terceiro arquivo encontrado
do.register_reader_fita(ReaderFitaDigitalSerconTds(lista_arquivos[2]['path'] +"/" + lista_arquivos[2]['name']))
#do.register_reader_fita(ReaderFitaDigitalAfr13(lista_arquivos[2]['path'] +"/" + lista_arquivos[2]['name']))
#do.set_size_header(24)
do.set_size_header(64)
print(do.reader_fita.read_header())
print(do.read_all_fita())
#print(do.calcular_estatisticas_ciclo(fases=['LEAK-TEST','ACONDICIONAMENTO', 'UMIDIFICACAO', 'ESTERILIZACAO', 'LAVAGEM','AERACAO','CICLO ABORTADO','CICLO FINALIZADO']))
#print(do.calcular_estatisticas_ciclo(fases=['LEAK-TEST','ACONDICIONAMENTO', 'UMIDIFICACAO', 'ESTERILIZACAO', 'LAVAGEM','AERACAO','CICLO ABORTADO']))

#print(do.calcular_estatisticas_ciclo(fase_inicial='ESTERILIZACAO', fase_final='LAVAGEM')) 

# Calcula a mortalidade e obtém o gráfico
#resultado, figura = do.calcular_mortalidade_intervalos(N0=1000000, fase_inicial='ESTERILIZACAO', fase_final='LAVAGEM', plot=True)

# Salva o gráfico em arquivo PNG
#figura.savefig('plot.png')

#print(resultado)
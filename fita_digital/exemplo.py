# Importando as classes necessárias
from data_object.dataobject_fita_digital import DataObjectFitaDigital
from reader_fita_digital.reader_fita_digital_afr13 import ReaderFitaDigitalAfr13

# Criando uma instância do DataObjectFitaDigital apontando para o diretório dos ciclos
do = DataObjectFitaDigital("/home/afonso/docker/odoo_engenapp/data/odoo/filestore/odoo-steriliza/Ciclos/")
modulo = __import__('reader_fita_digital.reader_fita_digital_afr13')
# Lendo os arquivos do diretório ETO01
lista_arquivos = do.ler_diretorio_ciclos("ETO01")
print(lista_arquivos)
#print(lista_arquivos[2]['path'] +"/" + lista_arquivos[2]['name'])

# Registrando o leitor de fita para o terceiro arquivo encontrado
do.register_reader_fita(ReaderFitaDigitalAfr13(lista_arquivos[2]['path'] +"/" + lista_arquivos[2]['name']))
print(do.reader_fita.read_header())

print(do.read_all_fita())
print(do.calcular_tempo_total_ciclo())
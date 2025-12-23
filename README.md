# geneplus-public-scraping-sumary-and-pedigree
Este repositório contém scripts em Python para coleta automatizada de dados públicos dos sumários e pedigrees disponibilizados no site da Embrapa Geneplus, organizando as informações em arquivos estruturados no formato .jsonl.

> #### Aviso: Este projeto não possui vínculo institucional com a Embrapa ou com o Programa Geneplus. Utiliza exclusivamente dados públicos disponíveis no site oficial.

-----------------------------
## Objetivos
Automatizar a coleta de:
1. Animais presentes nos sumários Geneplus
2. Informações de pedigree (genealogia) associadas a esses animais
3. Organizar os dados conforme a raça e o tipo de contrato (touros, touros_futuro e femeas).

--------------------------
## Execução
Para executar o script é necessário ter o python instalado no computador, disponível em:

1. https://www.python.org/

Necessário a presença de biblioteas: 
1. requests
2. json
3. os
4. urllib.parse.

------------------------------
## Arquivos necessário 
Antes da execução, é necessário garantir que os seguintes arquivos estejam no mesmo diretório:
1. coleta_dados_geneplus.py sendo esse o código utilizado para a coleta
2. link.txt sendo o arquivo que possui as chaves necessárias (identificação das raças, IDs utilizados pelas URLs do Geneplus, Contratos associados, nomes dos arquivos de saída) para ter acesso aos sumários da Embrapa em seu site e o correto funcionamento do primeiro.

----------------------------
## Resultados
O script irá retornar:
1. Sumários Geneplus com arquivos .jsonl separados por:
    * Raça
    * Tipo de contrato (touros, touros_futuro e femeas)

Sendo cada linha do sumário correspondente aos animais presentes no sumários.

2. Genealogia com arquivos .jsonl de acordo com:
    * Raça

O scirpt garante a coleta de todos os indivíduos na aba de genealogia no site da Embrapa Geneplus, entretanto é recomendado a consistência do pedigre, em raros casos as fêmeas não possuem genealogia, não sendo gerado a linha de sua genealogia.

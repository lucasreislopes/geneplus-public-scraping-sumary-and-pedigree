import requests
import json
import os
from urllib.parse import unquote

def ler_animais_jsonl(caminho):
    animais = set()
    if not os.path.exists(caminho):
        return animais

    with open(caminho, "r", encoding="utf-8") as f:
        for linha in f:
            if linha.strip():
                registro = json.loads(linha)
                animal = registro.get("animal")
                if animal:
                    animais.add(animal)
    return animais

def ler_registros_jsonl(caminho):
    registros = []
    if not os.path.exists(caminho):
        return registros

    with open(caminho, "r", encoding="utf-8") as f:
        for linha in f:
            if linha.strip():
                registros.append(json.loads(linha))
    return registros

def extrair_ancestrais(registros):
    chaves = ["p", "m", "pp", "pm", "mp", "mm",
              "mmm", "mmp", "mpm", "mpp",
              "pmm", "pmp", "ppm", "ppp"]

    ancestrais = set()
    for r in registros:
        for c in chaves:
            v = r.get(c)
            if v:
                ancestrais.add(v)
    return ancestrais

def montar_url_session(id_raca):
    return (
        "https://gppluson.geneplus.com.br/publico/sumario/"
        f"{id_raca}"
    )

def montar_url_api(id_raca):
    return (
        "https://gppluson.geneplus.com.br/publico/sumario/"
        f"{id_raca}/filtro/iqg_basico/desc/0"
    )

def montar_url_pedigree(id_raca):
    return (
        "https://gppluson.geneplus.com.br/publico/sumario/"
        f"{id_raca}/gene"
    )

session = requests.Session()

with open("link.txt", "r", encoding="utf-8") as f:
    RACAS = json.load(f)

#### só é necessário escolher as chaves de animal
# RACAS_ALVO = {"nelore"} # rodar individualmente
RACAS_ALVO = {"brangus", "brahman", "senepol", "caracu", # utiliza animal
              "brangus", "limousin", "sindi", "santa_gertrudis",
              "sindi", "guzera", "tabapua", "montana", "canchim"}

for nome_raca, cfg in RACAS.items():

     # ---- filtro de raça
    if nome_raca not in RACAS_ALVO:
        continue

    # inserir for aqui
    id_raca = cfg["id_raca"]
    arquivo_pedigree = cfg["pedigree"]

    # 1. Abrir página para gerar cookies
    session.get(montar_url_session(id_raca),
        headers={"User-Agent": "Mozilla/5.0"}
        )

    # 2. Extrair CSRF token
    xsrf_token = session.cookies.get("XSRF-TOKEN")
    xsrf_token = unquote(xsrf_token)

    # 3. Endpoint da API
    url_api = montar_url_api(id_raca)

    headers_api = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": montar_url_session(id_raca),
        "X-XSRF-TOKEN": xsrf_token
    }

    print("#### Iniciando coleta dos animais da Geneplus #### \n")

    for tipo, contrato_cfg in cfg["contratos"].items():

        contrato = contrato_cfg["id"]
        arquivo = contrato_cfg["arquivo"]

        page = 1
        total_registros = 0 #

        open(arquivo, "a", encoding="utf-8").close()
        print(f"### Iniciando contrato {contrato} ({arquivo}) ###")

        while True: 

            payload = {
                "page": page,
                "ativo": "0", # filtro para todos os animais ["1" para só os animais ativos]
                "contrato": contrato
            }

            r = session.post(url_api, headers=headers_api, json=payload, timeout=(5,30))
            r.raise_for_status()

            if r.status_code != 200:
                print(f"Erro na página {page} — status {r.status_code}")
                break

            data = r.json()
            registros = data.get("data", [])
            total_geneplus = data.get("total", 0) 

            animais_ja_coletados = ler_animais_jsonl(arquivo)
            total_arquivo = len(animais_ja_coletados)

            if total_arquivo >= total_geneplus:
                print(
                f"[OK] {arquivo} já completo "
                f"({total_arquivo}/{total_geneplus}). Coleta ignorada."
                )
                break

            if not registros:
                print("Fim da paginação.")
                break

            total_registros += len(registros)
            if page % 100 == 0:
                print(f"Página {page} — {len(registros)} \n"
                        f"Já foram {total_registros} registros acumulados"
                        f"registros do contrato {arquivo}" 
                    )
            
            novos = 0
            with open(arquivo, "a", encoding="utf-8") as f:
                for r in registros:
                    animal = r.get("animal")
                    if not animal or animal in animais_ja_coletados:
                        continue

                    animais_ja_coletados.add(animal)
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
                    novos += 1
                
            page += 1   
            
        print(
            f"[OK] Coleta finalizada — contrato {contrato} | arquivo: {arquivo}"
        )
    # ########################## pedigree
    animal_ped = set()

    for tipo, contrato_cfg in cfg["contratos"].items():
        arquivo = contrato_cfg["arquivo"]

        if os.path.exists(arquivo):
            animal_ped |= set(ler_animais_jsonl(arquivo))

    print(f"[OK] Total de animais base: {len(animal_ped)}")

    print("#### Iniciando coleta dos animais do pedigree da Geneplus #### \n"
          f"\n### Iniciando contrato {contrato} ({arquivo}) ####")

    #######################
    base_url = montar_url_pedigree(id_raca)
    open(arquivo_pedigree, "a", encoding="utf-8").close()

    FASE1_FLAG = f"{arquivo_pedigree}.fase1_ok"

    while True: 

        #### fase 1
        if not os.path.exists(FASE1_FLAG):
            set_animais = ler_animais_jsonl(arquivo_pedigree)
            
            lista_animais = animal_ped - set_animais

            if not lista_animais:
                open(FASE1_FLAG, "w").close()
                print("[OK] Fase 1 concluída — todos os animais base coletados")
                continue

            print(f"[FASE 1] Coletando {len(lista_animais)} animais base")

        #### fase 2
        else:
            registros_json = ler_registros_jsonl(arquivo_pedigree)
            set_animais = ler_animais_jsonl(arquivo_pedigree)

            set_vovo = extrair_ancestrais(registros_json)
            lista_animais = set_vovo - set_animais

            if not lista_animais:
                print("[OK] Nenhum novo ancestral para coletar. Processo finalizado.")
                break
                
            print(f"[FASE 2] Coletando {len(lista_animais)} ancestrais")
        
        registros_json = []

        with open(arquivo_pedigree, "r", encoding="utf-8") as f:
            for linha in f:
                if linha.strip():
                    registros_json.append(json.loads(linha))

        ####

        if not lista_animais:
            print("[OK] Nenhum novo animal para coletar. Processo finalizado")
            break

        pedigree_coletado = 0
        respostas_vazias = 0
        
        for animal in lista_animais:

            try:
                payload = {
                    "animal": animal
                }

                url = f"{base_url}?animal={animal}"

                r = session.get(url, headers=headers_api, params=payload, timeout=(5,30))
                r.raise_for_status()

            except requests.exceptions.RequestException as e:
                print(f"[ERRO CONEXÃO] {animal}: {e}")
                continue

            if not r.text.strip():
                print(f"[ERRO] Resposta vazia para animal {animal}")
                respostas_vazias += 1
                continue

            try:
                pedigree = r.json()
            except json.JSONDecodeError:
                print(f"[ERRO JSON] Animal {animal}")
                print(r.text[:200])
                continue

            # ---- empilhar no JSON
            with open(arquivo_pedigree, "a", encoding="utf-8") as f:
                f.write(json.dumps(pedigree, ensure_ascii=False) + "\n")

            pedigree_coletado += 1
            if pedigree_coletado % 500 == 0:
                print(f"Já foram coletados {pedigree_coletado}\n"
                    f"Restam: {len(lista_animais)-pedigree_coletado}")
    
        # --- condição de parada definitiva ---
        if pedigree_coletado == 0 and respostas_vazias == len(lista_animais):
            print(
                "[OK] Todos os animais restantes retornaram resposta vazia. "
                "Nenhum pedigree novo foi obtido. Encerrando processo."
            )
            break

    if os.path.exists(FASE1_FLAG):
        os.remove(FASE1_FLAG)
        
    print(f"[OK] pedigree dos animais da Geneplus coletados com sucesso, total de: {len(lista_animais)}")
    print(f"[OK] Total de animais com pedigree armazenados: {len(set_animais)}")

    print(f"[OK] Raça {nome_raca} finalizada \n")









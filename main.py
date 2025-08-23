import functions_framework
import llama_index
from llama_index.llms.cohere import Cohere
import json
import requests
import uuid
from datetime import datetime, timezone
import os
import cohere
import pinecone
from pinecone import Pinecone
from typing import List, Dict


ORACLE_API_URL = "https://g56e15c6771c555-nutriaidb.adb.sa-saopaulo-1.oraclecloudapps.com/ords/admin/chats/"

@functions_framework.http
def hello_http(request):

    request_json = request.get_json(silent=True)

    if request_json and 'prompt' in request_json:
        user_prompt = request_json['prompt']

    if request_json and 'id_usuario' in request_json:
        id_usuario = request_json['id_usuario']

    if request_json and 'id_paciente' in request_json:
        id_paciente = request_json['id_paciente']

    if request_json and 'nm_chat' in request_json:
        nm_chat = request_json['nm_chat']

    
    chats_por_nome = buscar_e_filtrar_chats(nm_chat=nm_chat, uid_usuario=id_usuario)

    salvar_chat(id_usuario, user_prompt, nm_chat, id_paciente)

    chats_simplificados = []
    for chat in chats_por_nome:
        # Pega a mensagem
        mensagem = chat['ds_mensagens_chat']
        
        data_texto = chat['dt_criacao_chat']

        data_objeto = datetime.fromisoformat(data_texto.replace('Z', '+00:00'))

        tempo_formatado = data_objeto.strftime('%d/%m/%Y %H:%M:%S')
        
        chats_simplificados.append({
            'mensagem': mensagem,
            'tempo': tempo_formatado
        })

    chats_ordenados = sorted(chats_simplificados, key=lambda item: item['tempo'])

    print(chats_ordenados)


    resultado_completo = buscar_e_responder(user_prompt, chats_ordenados)

    resposta = f"{resultado_completo.get('resposta', 'N/A')} \n"

    if resultado_completo["fontes"]:
        for fonte in resultado_completo["fontes"]:
            resposta += f" Fontes \n- ID: {fonte.get('id', 'N/A')}, Fonte: {fonte.get('source', 'N/A')}, Pagina: {fonte.get('page_label', 'N/A')}"
    else:
        print("Nenhuma fonte foi recuperada.")


    salvar_chat(id_usuario, resposta, nm_chat, id_paciente)

    return resposta

def salvar_chat(id_usuario, message, nm_chat, id_paciente):

    
    print("Iniciando salvamento do chat no Oracle...")

    data_de_criacao_iso = datetime.now(timezone.utc).isoformat()

    oracle_payload = {
        "uid_usuario_chat":id_usuario,
        "nm_chat": nm_chat,
        "ds_mensagens_chat": message,
        "id_paciente": id_paciente,
        "dt_criacao_chat": data_de_criacao_iso,
    }

    headers = {"Content-Type": "application/json"}
    
    oracle_response = requests.post(ORACLE_API_URL, data=json.dumps(oracle_payload), headers=headers)
    oracle_response.raise_for_status()
    
    print(f"Chat salvo com sucesso. ID: {id_usuario}")
    return id_usuario

def get_chat_date(chat_record):
    """
    Função auxiliar segura para extrair e converter a data de um registro de chat.
    Retorna um objeto datetime válido ou uma data mínima se a data for nula ou inválida.
    """
    date_str = chat_record.get('dt_criacao_chat')

    if not date_str:
        return datetime.min

    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        try:
            return datetime.strptime(date_str, "%d/%m/%Y, %I:%M:%S %p")
        except (ValueError, TypeError):
            print(f"AVISO: Não foi possível converter a data '{date_str}'. Tratando como antigo.")
            return datetime.min

def buscar_e_filtrar_chats(id_chat=None, uid_usuario=None, nm_chat=None):
    """
    Busca todos os chats da API Oracle, filtra em memória e os ordena por data de forma segura.
    """
    print("Buscando todos os chats da API...")
    try:
        response = requests.get(ORACLE_API_URL)
        response.raise_for_status()

        todos_os_chats = response.json().get('items', [])
        print(f"Encontrados {len(todos_os_chats)} chats no total.")

        # A lógica de filtragem continua a mesma
        resultados_filtrados = []
        for chat in todos_os_chats:
            match_id = (id_chat is None) or (str(chat.get('id_chat')) == str(id_chat))
            match_uid = (uid_usuario is None) or (chat.get('uid_usuario_chat') == uid_usuario)
            match_nm = (nm_chat is None) or (nm_chat.lower() in str(chat.get('nm_chat', '')).lower())
            if match_id and match_uid and match_nm:
                resultados_filtrados.append(chat)
        
        print(f"Após a filtragem, restaram {len(resultados_filtrados)} chats.")


        resultados_ordenados = sorted(resultados_filtrados, key=get_chat_date)

        print("Chats ordenados com sucesso.")
        return resultados_ordenados

    except requests.exceptions.RequestException as e:
        print(f"Erro ao fazer a requisição para a API: {e}")
        return None
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
        return None

def buscar_e_responder(pergunta, chats_ordenados) -> Dict:


    COHERE_API_KEY = "RAjqpE9uTVFfTTaF0RIGUM4PaKBeQ7insNIu9KLC"
    PINECONE_API_KEY = "pcsk_5RSTcB_8GfPp22T2dhbtGz59ihsbPZQnG6HHnia2QJosnBy22T8ZTu1wdcwhqdWqhRrUcm"
    PINECONE_INDEX_NAME = "teste"


    TOP_K = 4
    TEMPERATURE = 0.3


    PERSONA = """
        **Você é "Nutri-Cortex", um Assistente de IA de suporte à decisão para nutricionistas.**

        Sua função é processar, correlacionar e resumir informações da base de dados científicos e dos prontuários de pacientes. Você existe para otimizar o tempo do nutricionista, destacando informações relevantes.

        **Regras Inquebráveis:**
        1. **Posicionamento de Assistente:** Suas respostas são informações para a avaliação do profissional. A decisão final é 100% do nutricionista.
        2. **Fidelidade ao Contexto:** Sua resposta DEVE ser gerada EXCLUSIVAMENTE a partir dos documentos fornecidos. É PROIBIDO usar conhecimento externo.
        3. **Cite Suas Fontes:** Sempre que possível, referencie a origem da sua informação.
        4. **Informação Faltante:** Se a informação não estiver nos documentos, afirme claramente: "A informação necessária para responder a esta pergunta não foi encontrada nos documentos fornecidos."
        5. **Objetividade e Precisão:** Apresente os dados de forma neutra, técnica e profissional.

        Abaixo voce tem acesso ao historico da conversa com o profissional, lembre de sempre levar ele em consideração:

        {chats_ordenados}


    """

    try:
        cliente_cohere = cohere.Client(api_key=COHERE_API_KEY)
        pc = Pinecone(api_key=PINECONE_API_KEY)
        indice_pinecone = pc.Index(name=PINECONE_INDEX_NAME)


        response_query = cliente_cohere.embed(
            texts=[pergunta],
            model='embed-multilingual-v3.0',
            input_type='search_query'
        )
        vetor_da_pergunta = response_query.embeddings[0]


        resultados_pinecone = indice_pinecone.query(
            vector=vetor_da_pergunta,
            top_k=TOP_K,
            include_metadata=True
        )



        documentos_recuperados = []
        for match in resultados_pinecone['matches']:
            documentos_recuperados.append({
                "id": match['id'],
                "text": match['metadata'].get('text', ''),
                "source": match['metadata'].get('file_name', 'N/A'),
                "page_label": match['metadata'].get('page_label', '')
            })


        resposta_final = cliente_cohere.chat(
            model="command-r",
            message=pergunta,
            documents=documentos_recuperados,
            preamble=PERSONA,
            temperature=TEMPERATURE
        )


        return {
            "resposta": resposta_final.text,
            "fontes": documentos_recuperados
        }
    except Exception as e:
        print(f"Ocorreu um erro dentro da função buscar_e_responder: {e}")
        return {
            "resposta": "Desculpe, ocorreu um erro ao processar sua solicitação.",
            "fontes": []
        }
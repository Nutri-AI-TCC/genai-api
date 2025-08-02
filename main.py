import functions_framework
import llama_index
from llama_index.llms.cohere import Cohere
import json
import requests
import uuid
from datetime import datetime, timezone

ORACLE_API_URL = "https://g56e15c6771c555-nutriaidb.adb.sa-saopaulo-1.oraclecloudapps.com/ords/admin/chats/"

@functions_framework.http
def hello_http(request):

    # Tenta pegar o JSON do corpo da requisição
    request_json = request.get_json(silent=True)

    # Verifica se o JSON e a chave 'prompt' existem
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
        
        # Pega a data (que está como texto)
        data_texto = chat['dt_criacao_chat']
        
        # Converte o texto da data para um objeto datetime do Python
        # O .replace('Z', '+00:00') ajuda o Python a entender o fuso horário UTC
        data_objeto = datetime.fromisoformat(data_texto.replace('Z', '+00:00'))

        tempo_formatado = data_objeto.strftime('%d/%m/%Y %H:%M:%S')
        
        # Adiciona um novo dicionário com os dados limpos à nossa lista
        chats_simplificados.append({
            'mensagem': mensagem,
            'tempo': tempo_formatado
        })

    chats_ordenados = sorted(chats_simplificados, key=lambda item: item['tempo'])

    print(chats_ordenados)


    api_key = "RAjqpE9uTVFfTTaF0RIGUM4PaKBeQ7insNIu9KLC"

    llm = Cohere(model="command-r-08-2024", api_key=api_key)

    prompt = f"""

    Você é um assistente de um nutricionista, e deve ajudar a responder perguntas com base em seu conhecimento, sua função é somente auxiliar, 
    tirando duvidas sobre alimentação.

    O usuário é nutricionista, ele precisa de ajuda com um paciente, por isso você deve ajudar respondendo suas duvidas.

    Aqui está um histórico da conversa até o momento, lembre se leva-lo em consideração:

    {chats_ordenados}


    A pergunta do usuário é a seguinte: {user_prompt}
    Responda em Português

    """

    resp = llm.complete(prompt)

    print(resp.text)


    salvar_chat(id_usuario, resp.text, nm_chat, id_paciente)

    return resp.text

def salvar_chat(id_usuario, message, nm_chat, id_paciente):

    
    print("Iniciando salvamento do chat no Oracle...")

    data_de_criacao_iso = datetime.now(timezone.utc).isoformat()

    # Payload (corpo da requisição) para a API do Oracle
    oracle_payload = {
        "uid_usuario_chat":id_usuario,
        "nm_chat": nm_chat,
        "ds_mensagens_chat": message,
        "id_paciente": id_paciente,
        "dt_criacao_chat": data_de_criacao_iso,
    }

    headers = {"Content-Type": "application/json"}
    
    # Faz a requisição POST e levanta uma exceção em caso de erro (4xx ou 5xx)
    oracle_response = requests.post(ORACLE_API_URL, data=json.dumps(oracle_payload), headers=headers)
    oracle_response.raise_for_status()
    
    print(f"Chat salvo com sucesso. ID: {id_usuario}")
    return id_usuario

def get_chat_date(chat_record):
    """
    Função auxiliar segura para extrair e converter a data de um registro de chat.
    Retorna um objeto datetime válido ou uma data mínima se a data for nula ou inválida.
    """
    # Usar .get() é mais seguro pois retorna None se a chave não existir
    date_str = chat_record.get('dt_criacao_chat')

    # Se a data for Nula ou uma string vazia, trata como a data mais antiga possível
    if not date_str:
        return datetime.min

    # Tenta converter a data (primeiro o formato ISO, depois o formato customizado)
    try:
        # Opção A: Formato ISO 8601 (ex: "2025-07-26T18:30:00Z")
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        try:
            # Opção B: Formato customizado (ex: "26/07/2025, 03:00:29 PM")
            return datetime.strptime(date_str, "%d/%m/%Y, %I:%M:%S %p")
        except (ValueError, TypeError):
            # Se nenhum formato funcionar, trata como a data mais antiga
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

        # --- ORDENAÇÃO SEGURA USANDO A FUNÇÃO AUXILIAR ---
        # A função `get_chat_date` lida com todos os casos de erro (nulos, formatos, etc.)
        resultados_ordenados = sorted(resultados_filtrados, key=get_chat_date)

        print("Chats ordenados com sucesso.")
        return resultados_ordenados

    except requests.exceptions.RequestException as e:
        print(f"Erro ao fazer a requisição para a API: {e}")
        return None
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
        return None
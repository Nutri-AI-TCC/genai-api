import functions_framework
import llama_index
from llama_index.llms.cohere import Cohere
import json
import requests
import uuid
from datetime import datetime, timezone

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

    
    salvar_chat(id_usuario, user_prompt, nm_chat, id_paciente)

    api_key = "RAjqpE9uTVFfTTaF0RIGUM4PaKBeQ7insNIu9KLC"

    llm = Cohere(model="command-r-08-2024", api_key=api_key)

    prompt = f"""

    Você é um assistente de um nutricionista, e deve ajudar a responder perguntas com base em seu conhecimento, sua função é somente auxiliar, 
    tirando duvidas sobre alimentação.

    O usuário é nutricionista, ele precisa de ajuda com um paciente, por isso você deve ajudar respondendo suas duvidas.

    A pergunta do usuário é a seguinte: {user_prompt}
    Responda em Português

    """

    resp = llm.complete(prompt)

    print(resp.text)


    salvar_chat(id_usuario, resp.text, nm_chat, id_paciente)

    return resp.text

def salvar_chat(id_usuario, message, nm_chat, id_paciente):

    ORACLE_API_URL = "https://g56e15c6771c555-nutriaidb.adb.sa-saopaulo-1.oraclecloudapps.com/ords/admin/chats/"
    
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
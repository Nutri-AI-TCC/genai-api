import functions_framework
import llama_index
from llama_index.llms.cohere import Cohere

@functions_framework.http
def hello_http(request):

    # Tenta pegar o JSON do corpo da requisição
    request_json = request.get_json(silent=True)

    # Verifica se o JSON e a chave 'prompt' existem
    if request_json and 'prompt' in request_json:
        user_prompt = request_json['prompt']

    api_key = "RAjqpE9uTVFfTTaF0RIGUM4PaKBeQ7insNIu9KLC"

    llm = Cohere(model="command", api_key=api_key)

    resp = llm.complete(user_prompt)

    print(resp)

    return resp

def salvar_chat(id_usuario, message, nm_chat, id_paciente):

    ORACLE_API_URL = "https://g56e15c6771c555-nutriaidb.adb.sa-saopaulo-1.oraclecloudapps.com/ords/admin/chats/"
    
    print("Iniciando salvamento do chat no Oracle...")

    data_de_criacao_iso = datetime.now(timezone.utc).isoformat()

    # Payload (corpo da requisição) para a API do Oracle
    oracle_payload = {
        "uid_usuario_chat":"uid-002",
        "nm_chat": nm_chat,
        "ds_mensagens_chat": message,
        "dt_criacao_chat": data_de_criacao_iso
    }

    headers = {"Content-Type": "application/json"}
    
    # Faz a requisição POST e levanta uma exceção em caso de erro (4xx ou 5xx)
    oracle_response = requests.post(ORACLE_API_URL, data=json.dumps(oracle_payload), headers=headers)
    oracle_response.raise_for_status()
    
    print(f"Chat salvo com sucesso. ID: {id_usuario}")
    return id_usuario
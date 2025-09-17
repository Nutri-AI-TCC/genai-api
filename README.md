# NutriAI Chat Assistant API 🤖

Esta API funciona como um assistente de IA para nutricionistas. Ela recebe uma pergunta, analisa o histórico da conversa e utiliza um modelo de linguagem avançado para gerar uma resposta contextualizada.

## ✨ Funcionalidades Principais

- **Assistente Inteligente**: Atua como um assistente de nutrição, respondendo a perguntas com base em um vasto conhecimento.
- **Consciência de Contexto**: Leva em consideração o histórico de um chat para fornecer respostas que fazem sentido dentro da conversa contínua.
- **Persistência de Diálogo**: Salva automaticamente a pergunta e a resposta, construindo um histórico para futuras interações.

---

## 🕹️ Como Usar a API

Existe um único endpoint para interagir com o assistente.

- **Método:** `POST`
- **URL:** `[https://<SUA_URL_DO_CLOUD_FUNCTION>](https://us-central1-nutri-ai-463621.cloudfunctions.net/agent-pd)`

### Exemplo de Payload (O que você envia)

Você precisa enviar um JSON com os seguintes campos. O `prompt` é a sua pergunta, e os outros campos fornecem o contexto para salvar e recuperar o histórico do chat.

```json
{
    "prompt": "Olá tudo bem?",
    "id_paciente": 161,
    "id_chat": 223
}

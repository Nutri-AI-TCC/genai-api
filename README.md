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
- **URL:** `https://<SUA_URL_DO_CLOUD_FUNCTION>`

### Exemplo de Payload (O que você envia)

Você precisa enviar um JSON com os seguintes campos. O `prompt` é a sua pergunta, e os outros campos fornecem o contexto para salvar e recuperar o histórico do chat.

```json
{
  "prompt": "Quais são as melhores fontes de proteína vegetal para um paciente com alergia a soja?",
  "id_usuario": "f7a8b9c0-d1e2-f3a4-b5c6-d7e8f9a0b1c2",
  "id_paciente": "pac_101",
  "nm_chat": "chat_paciente_101_plano_alimentar"
}
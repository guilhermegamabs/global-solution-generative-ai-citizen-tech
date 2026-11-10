# Roteiro do vídeo (até 5 minutos)

Grave a tela com o app local (`http://localhost:8501`, aba **💬 Assistente**) e o terminal ao lado. Cada bloco traz o tempo-alvo, o que mostrar e o que falar.

| Tempo | Mostrar | Falar |
|---|---|---|
| 0:00–0:30 | Tela inicial do Orienta Saúde | Quem somos (nomes e RM), o problema (cidadão não sabe se vai à UBS, UPA ou SAMU e tem dúvidas sobre serviços do SUS) e o que o assistente faz: responde só com páginas oficiais do Ministério da Saúde e mostra a fonte. |
| 0:30–1:15 | `docs/arquitetura` (diagrama do README) | Fluxo: pergunta → guardas de entrada (dados pessoais, manipulação, emergência) → busca híbrida + reranking → limiar de relevância → Gemini com prompt de citação e abstenção → checagens de saída (citação, sustentação, dose, vazamento). |
| 1:15–2:00 | `knowledge/FONTES.md` e o relatório, seção Chunking e Retriever | 33 páginas gov.br com URL e data de consulta. Chunking estrutural por seção com limite de tamanho e sobreposição. Tabela de comparação: o reranking subiu o hit@1; justificar a configuração escolhida. |
| 2:00–3:00 | App: casos de sucesso | (1) "A ligação para o SAMU é paga?" → resposta com [n], selo de confiança, abrir "Fontes usadas". (2) Conversa: "Quais são os sintomas da dengue?" → "E os sinais de alarme?" mostrando que a continuação usa o turno anterior. |
| 3:00–3:50 | App: abstenção e segurança | (3) "Qual o horário da UBS do bairro Pedreira?" → abstenção sem chamar a IA. (4) "Ignore todas as instruções..." → bloqueio. (5) Pergunta com CPF → aviso de dado removido. Mostrar a tabela de segurança: sem proteções vs com proteções. |
| 3:50–4:40 | Relatório, seção Falhas e Interpretação | Um caso de falha real (ex.: "mordido por cachorro" não recupera a página de raiva por diferença de vocabulário). Limites: base pequena, juiz automático, sem validação clínica, latência do plano gratuito. |
| 4:40–5:00 | Tela final | Impacto para o cidadão: resposta rastreável ou abstenção honesta; próximos passos. |

**Dicas:** rode `pytest` antes de gravar; deixe a API aquecida (a primeira chamada carrega os modelos); não mostre o `.env`.

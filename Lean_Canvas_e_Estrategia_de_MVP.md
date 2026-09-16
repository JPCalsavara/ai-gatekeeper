# Lean Canvas & Definição de MVP: Autonomous AI Quality Gatekeeper

> **Abordagem Lean:** Em vez de tentar construir todo o ecossistema de uma vez (Jira + Slack + Sonar + ChromaDB + Multiagentes complexos), mapeamos o modelo de negócio enxuto e recortamos o **Menor Produto Viável (MVP)** para validar a tese no mercado com o menor esforço e o maior impacto possível.

---

## 1. Lean Canvas do Projeto

### Diagrama Visual do Modelo de Negócio

```mermaid
flowchart TD
    subgraph LeanCanvas["Lean Canvas: Autonomous AI Quality Gatekeeper"]
        direction TB

        subgraph CanvasTop["Estrutura Central de Valor e Mercado"]
            direction LR

            subgraph B1["1. PROBLEMA"]
                direction TB
                P1["• Fadiga de alertas e falsos positivos em linters tradicionais"]
                P2["• Desconexão entre diretrizes internas (RFCs) e código no PR"]
                P3["• Custo proibitivo e falta de privacidade em SaaS proprietários"]
            end

            subgraph B4["4. SOLUÇÃO"]
                direction TB
                S1["• Triagem inteligente de falhas de testes (cruza log com diff)"]
                S2["• Reconciliação com regras do repositório (Context Harness)"]
                S3["• Telemetria aberta de tokens e custos (USD) visível no PR"]
            end

            subgraph B3["3. PROPOSTA DE VALOR"]
                direction TB
                PV["'O Quality Gate de IA aberto (BYOK) que reconcilia testes quebrados e diretrizes internas direto no seu CI/CD, por frações de centavos por PR.'"]
            end

            subgraph B9["9. VANTAGEM INJUSTA"]
                direction TB
                VI1["• Arquitetura agnóstica (BYOK) executando no runner da empresa com privacidade total e sem lock-in"]
                VI2["• Model Tiering dinâmico (Flash + Pro) que corta custos em mais de 85% frente a SaaS fechados"]
            end

            subgraph B2["2. SEGMENTO DE CLIENTES"]
                direction TB
                SC1["• Early Adopters: Tech Leads e Devs Sêniores cansados de perder tempo com PRs quebrados"]
                SC2["• Times com restrições de compliance/privacidade (Fintechs, Healthtechs) impedidos de usar SaaS externos"]
            end
        end

        subgraph CanvasBottom["Distribuição, Métricas e Monetização"]
            direction LR

            subgraph B7["7. MÉTRICAS-CHAVE"]
                direction TB
                M1["• PRs analisados / mês"]
                M2["• Taxa de aprovação das correções sugeridas"]
                M3["• Estrelas e Forks no repositório GitHub"]
                M4["• Custo médio por PR mantido abaixo de $0.005 USD"]
            end

            subgraph B8["8. CANAIS"]
                direction TB
                C1["• GitHub Marketplace (Action oficial)"]
                C2["• Comunidades técnicas (Reddit r/devops, Hacker News, LinkedIn)"]
                C3["• Conteúdo técnico (artigos de arquitetura e tutoriais práticos)"]
            end

            subgraph B5["5. FONTES DE RECEITA"]
                direction TB
                R1["• Fase 1 (Open-Source): Sponsorships (GitHub Sponsors) e autoridade/portfólio"]
                R2["• Fase 2 (Open-Core): Dashboard web corporativo para métricas consolidadas de times"]
            end
        end
    end
```

### Detalhamento dos Blocos do Lean Canvas

| Bloco | Detalhes |
| :--- | :--- |
| **1. Problema** | • Fadiga de alertas e falsos positivos em linters tradicionais.<br/>• Desconexão entre diretrizes internas (RFCs) e o código submetido no PR.<br/>• Custo proibitivo e falta de privacidade em SaaS de IA proprietários. |
| **4. Solução** | • Triagem inteligente de falhas de testes (cruza log com diff).<br/>• Reconciliação com regras do repositório (Context Harness).<br/>• Telemetria aberta de tokens e custos (USD) visível no PR. |
| **3. Proposta de Valor** | *"O Quality Gate de IA aberto (BYOK) que reconcilia testes quebrados e diretrizes internas direto no seu CI/CD, por frações de centavos por PR."* |
| **9. Vantagem Injusta** | • **Arquitetura agnóstica (BYOK)** que roda dentro do runner da empresa, garantindo privacidade total sem lock-in.<br/>• **Model Tiering dinâmico (Flash + Pro)** que corta custos em mais de 85% frente a SaaS fechados. |
| **2. Segmento de Clientes** | • **Early Adopters:** Tech Leads e Devs Sêniores cansados de perder tempo com PRs quebrados e ruídos.<br/>• **Times de Engenharia** com restrições de compliance/privacidade (Fintechs, Healthtechs) que não podem usar SaaS externos. |
| **8. Canais** | • GitHub Marketplace (Action oficial).<br/>• Comunidades técnicas (Reddit `r/devops`, Hacker News, LinkedIn).<br/>• Conteúdo técnico (artigos de arquitetura e tutoriais práticos). |
| **7. Métricas-Chave** | • PRs analisados / mês.<br/>• Taxa de aprovação das correções sugeridas.<br/>• Estrelas e Forks no repositório GitHub.<br/>• Custo médio por PR mantido < $0.005 USD. |
| **5. Fontes de Receita** | • **Fase 1 (Open-Source):** Sponsorships (GitHub Sponsors) e portfólio.<br/>• **Fase 2 (Open-Core):** Dashboard web corporativo para métricas consolidadas de times. |

---

## 2. O Maior Erro do Escopo Inicial: O Risco de Sobrecarga

Se começarmos implementando simultaneamente:
- [ ] MCP Server do Jira;
- [ ] MCP Server do Slack;
- [ ] ChromaDB vetorial local;
- [ ] Integração profunda com SonarQube SARIF;
- [ ] 5 agentes em grafo cíclico...

👉 **O projeto demorará meses para rodar, será difícil de depurar e ninguém conseguirá testar com facilidade.**

> 💡 **O segredo do Lean** é achar a fatia vertical mais fina que gera o momento *"UAU"* na primeira execução.

---

## 3. O Recorte Lean: Decomposição em Fases

```mermaid
flowchart TD
    V01["MVP v0.1 (Semana 1) - O Núcleo do Valor\n• Diagnóstico de Teste Quebrado (Logs + Diff)\n• 1 Arquivo de Regras Estático (docs/rules.md)\n• 2 Nós LangGraph: Flash (Análise) + Pro (Decisão)\n• Telemetria de custo postada no comentário do PR"]

    V02["Versão v0.2 (Semana 2-3) - Context Harness & Sonar\n• RAG local com ChromaDB para repositórios com RFCs\n• Ingestão de relatórios determinísticos do Sonar\n• Empacotamento como GitHub Action oficial"]

    V10["Versão v1.0 (Futuro) - Conectores MCP Corporativos\n• Integração MCP com Jira (Critérios de Aceite)\n• Integração MCP com Slack (Decisões de canais)\n• Dashboard de governança multi-repositório"]

    V01 -->|"Validação com usuários"| V02
    V02 -->|"Tração comunitária"| V10

    classDef mvp fill:#e1f5fe,stroke:#0288d1,stroke-width:2px;
    classDef v02 fill:#f3e5f5,stroke:#7b1fa2,stroke-width:1.5px;
    classDef v10 fill:#fff3e0,stroke:#f57c00,stroke-width:1.5px;
    class V01 mvp;
    class V02 v02;
    class V10 v10;
```

---

## 4. Especificação do MVP v0.1 (O Que Construir Agora)

### O Problema que o MVP Resolve no Dia 1
> Todo desenvolvedor odeia abrir um PR, ver o CI vermelho porque um teste unitário quebrou e ter que rolar 500 linhas de logs do GitHub Actions para descobrir o que aconteceu.

### O Que Entra no MVP v0.1

1. **Entrada 1:** O arquivo `diff.txt` gerado pelo git.
2. **Entrada 2:** O arquivo `test.log` (extraído da execução do PyTest, Jest ou similar no CI).
3. **Entrada 3:** Um arquivo simples `docs/rules.md` (regras básicas de arquitetura da equipe injetadas diretamente no prompt, sem banco vetorial ainda).
4. **Orquestração LangGraph Enxuta (2 nós):**
   - **Nó 1 (Gemini 2.5 Flash):** Analisa o log do teste, cruza com as linhas modificadas no diff e identifica a causa raiz.
   - **Nó 2 (Gemini 2.5 Pro):** Valida a severidade, confere com o `rules.md` e formata o parecer final.
5. **Saída:** Um comentário no PR no GitHub contendo:
   - Teste exato que quebrou e a linha do diff responsável;
   - Bloco de código sugerindo o patch de correção;
   - Tabela de LLMOps mostrando quanto custou a análise em centavos (USD).

### Arquitetura do Pipeline do MVP v0.1

```mermaid
flowchart TD
    subgraph Inputs["1. Entradas (CI Runner)"]
        direction TB
        E1["diff.txt\n(Git Diff das mudanças)"]
        E2["test.log\n(Log de execução PyTest/Jest)"]
        E3["docs/rules.md\n(Diretrizes estáticas do repo)"]
    end

    subgraph LangGraph["2. Orquestração LangGraph (2 Nós)"]
        direction TB
        N1["Nó 1: Gemini 2.5 Flash\n• Triagem de falhas\n• Cruza log com diff\n• Identifica causa raiz"]
        N2["Nó 2: Gemini 2.5 Pro\n• Validação de severidade\n• Conformidade com rules.md\n• Geração do patch final"]
        N1 -->|"Diagnóstico preliminar"| N2
    end

    subgraph Output["3. Saída (GitHub PR Comment)"]
        direction TB
        O1["Identificação do teste quebrado e linha do diff"]
        O2["Patch de código sugerido para correção"]
        O3["Tabela LLMOps de telemetria e custo (< $0.003 USD)"]
    end

    E1 --> N1
    E2 --> N1
    E3 --> N2
    N2 --> Output

    classDef inputStyle fill:#f0f4c3,stroke:#9e9d24,stroke-width:1.5px;
    classDef nodeStyle fill:#e8eaf6,stroke:#3f51b5,stroke-width:2px;
    classDef outputStyle fill:#e8f5e9,stroke:#388e3c,stroke-width:2px;
    class E1,E2,E3 inputStyle;
    class N1,N2 nodeStyle;
    class O1,O2,O3 outputStyle;
```

---

## 5. Experimento Lean: Como Validar em 7 Dias

Para validar se o projeto tem tração real antes de gastar semanas codificando integrações complexas:

```mermaid
flowchart LR
    D1["Dias 1 e 2:\nConstruir MVP\n(gatekeeper_mvp.py + CI)"]
    D2["Dia 3:\nRepo público,\nREADME impecável e GIF/print"]
    D3["Dia 4:\nTeste BYOK\ncom amigo dev de IA"]
    D4["Dias 5 e 6:\nPost técnico viral\n(LinkedIn / Dev.to)"]
    D5["Dia 7:\nMedição de tração\ne validação de demanda"]

    D1 --> D2 --> D3 --> D4 --> D5

    classDef stepStyle fill:#fce4ec,stroke:#c2185b,stroke-width:1.5px;
    class D1,D2,D3,D4,D5 stepStyle;
```

### Roteiro Diário de Validação

1. **Dia 1 e 2:** Escrever o script Python do MVP (`gatekeeper_mvp.py`) com LangGraph e o workflow simples do GitHub Actions.
2. **Dia 3:** Criar um repositório público com um README impecável, contendo um GIF/print de um PR real onde o agente identifica o bug do teste e posta a correção com a telemetria de custos.
3. **Dia 4:** Testar com o seu amigo que mexe com IA:
   - Pedir para ele rodar no repositório dele colocando apenas a `GEMINI_API_KEY`.
   - Coletar o feedback imediato: *A configuração foi rápida? O comentário foi útil? O custo fez sentido?*
4. **Dia 5 e 6:** Publicar um post técnico curto (no LinkedIn ou Dev.to) com o título:
   > *"Por que paramos de pagar $40/dev em ferramentas de review de PR e construímos nosso próprio Quality Gatekeeper com Gemini Flash por $0.002 por execução."*
5. **Dia 7:** Medir o interesse:
   - Se houver pessoas comentando e pedindo suporte para Sonar e Jira, você validou a demanda antes de codificar a complexidade do MCP.

---

## 6. Critérios de Sucesso do MVP (Go / No-Go)

| Métrica de Validação | Meta Mínima (Sucesso) |
| :--- | :--- |
| **Tempo de Onboarding** | Um desenvolvedor novo consegue rodar no seu repo em **menos de 5 minutos**. |
| **Precisão de Diagnóstico** | Identifica corretamente a linha causadora da quebra de teste em **ao menos 8 de 10 casos reais**. |
| **Custo por PR** | Custo médio de execução mantido **abaixo de $0.003 USD**. |
| **Falsos Positivos** | **Nenhuma recomendação** que quebre padrões estabelecidos no `docs/rules.md`. |

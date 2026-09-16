# Diretrizes de Arquitetura e Engenharia do Projeto

## 1. Segurança & Autenticação
- Nunca permita credenciais, senhas, tokens ou connection strings em texto plano no código.
- Todas as queries de banco devem usar parametrização (Prepared Statements ou ORM). Concatenação de strings em SQL é proibida (BLOCKER).
- Endpoints que manipulam dados de usuários devem validar permissão/escopo no handler.

## 2. Padrões de Projeto & Qualidade
- Tratamento de exceções: Não engula exceções com `catch (Exception e) {}` ou `except Exception: pass` vazios.
- Injeção de dependência deve ser feita via construtor/interfaces, evitando instanciar serviços diretamente com `new`.
- Funções não devem ultrapassar 50 linhas de código (Code Smell).

## 3. Estratégia de Testes
- Todo novo endpoint ou serviço de regra de negócio deve vir acompanhado de testes unitários ou de integração no mesmo PR.
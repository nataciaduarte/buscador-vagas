# Buscador de Vagas e Estágios

Plataforma que coleta todos os dias vagas de estágio no Rio de Janeiro e permite filtrar por palavra-chave, local e período. A estrutura foi feita para crescer: novas buscas e fontes de vagas entram com poucas linhas de código.

**Acesse o site:** https://buscador-vagas-natacia.streamlit.app

## O problema

Procurar estágio exige abrir vários sites todos os dias. Este projeto reúne as vagas num só lugar, com filtros pensados para quem está começando.

## Como funciona

1. Todo dia às 7h (horário de Brasília), o GitHub Actions executa um coletor em Python.
2. O coletor consulta a API da Adzuna e busca as vagas mais recentes.
3. As vagas são limpas, deduplicadas e salvas em um banco SQLite.
4. Vagas com mais de 30 dias são removidas automaticamente.
5. O banco atualizado é salvo no repositório, e o site em Streamlit passa a exibir as vagas novas.

A chave da API fica guardada nos Secrets do GitHub e nunca aparece no código. O site público só lê o banco de dados e não tem acesso a nenhuma credencial.

## Tecnologias

- Python (requests, pandas)
- SQL com SQLite
- Streamlit (interface web)
- GitHub Actions (coleta diária automática)
- Streamlit Community Cloud (hospedagem)

## O que aprendi

- Consumir uma API REST com autenticação por chave
- Modelar uma tabela e evitar duplicatas com chave primária
- Proteger credenciais com arquivo .env e GitHub Secrets
- Automatizar uma rotina diária de coleta de dados
- Publicar uma aplicação web que se atualiza a cada envio de código

## Próximos passos

- Ampliar a coleta para vagas de emprego em todo o Brasil
- Adicionar outras fontes de vagas
- Montar um painel no Power BI com vagas por cidade e categoria
- Classificar automaticamente o nível da vaga (estágio, júnior, pleno) com Machine Learning

## Como rodar no seu computador

1. Crie uma chave gratuita em https://developer.adzuna.com
2. Crie um arquivo `.env` com `ADZUNA_APP_ID` e `ADZUNA_APP_KEY`
3. Instale as dependências: `pip install -r requirements.txt`
4. Colete as vagas: `python coletor.py`
5. Abra o site: `streamlit run app.py`

## Créditos

Dados de vagas fornecidos pela [API da Adzuna](https://www.adzuna.com.br).

## Autora

**Natacia Duarte**, estudante de Inteligência Artificial e Machine Learning.

[LinkedIn](https://www.linkedin.com/in/natácia-duarte-7a4860381) · [GitHub](https://github.com/nataciaduarte)
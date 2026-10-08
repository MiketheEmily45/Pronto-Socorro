# Fila de Pronto-Socorro — Sistema Distribuído (Web II)

Sistema distribuído de fila de atendimento para pronto-socorro hospitalar desenvolvido com **Django**, **Django REST Framework** e frontend puro (HTML5, CSS3 moderno e Vanilla JavaScript), em conformidade com as regras da disciplina de **Programação Web II** (Avaliação 2 / Bloco 3).

---

## 1. Visão Geral da Arquitetura

O sistema opera de forma distribuída em rede local (LAN/Wi-Fi):
- **Servidor Central (Notebook do Servidor)**: Executa a aplicação Django com o banco de dados e a API REST em `0.0.0.0:8000`.
- **Estação da Recepção (Notebook do Administrador)**: Acessa a interface administrativa web em `/admin-fila/` para triagem, cadastro, remoção e chamada de pacientes. As operações exigem autenticação via Token (armazenado em `sessionStorage`).
- **Sala de Espera (TV / Monitor / Segundo Notebook)**: Acessa o painel público em `/painel/`, sem necessidade de login. Atualiza automaticamente em tempo real (polling de 2,5s), exibe a contagem de pessoas aguardando, destaca o paciente chamado com dados reduzidos (**LGPD**) e emite **aviso sonoro** sintetizado via Web Audio API.

---

## 2. Estrutura do Projeto

```text
fila-ps/
│
├── config/                  # Configurações do projeto Django
│   ├── settings.py          # Settings flexíveis (SQLite/PostgreSQL, Hosts, Estáticos, Hasher rápido)
│   ├── urls.py              # Roteamento central (/admin-fila/, /painel/, /admin/, /api/)
│   ├── wsgi.py / asgi.py
│
├── fila/                    # Aplicação principal
│   ├── models.py            # Modelos: Paciente, Chamada, Sala e Medico
│   ├── services.py          # Regras de negócio atômicas (FIFO, locks com select_for_update)
│   ├── serializers.py       # Serializers DRF (proteção de dados LGPD)
│   ├── views.py             # Views da API REST e TemplateViews do frontend
│   ├── urls.py              # Rotas da API (/api/...)
│   ├── admin.py             # Registro no Django Admin
│   ├── tests.py             # Suíte de 28 testes automatizados
│   └── migrations/          # Histórico de migrações do banco
│
├── templates/
│   └── fila/
│       ├── admin_fila.html  # Interface de recepção e triagem administrativa
│       └── painel.html      # Interface pública de alto contraste para TV/sala de espera
│
├── static/                  # Arquivos estáticos adicionais
├── requirements.txt         # Dependências do projeto
├── .env.example             # Exemplo de variáveis de ambiente
└── README.md                # Este documento
```

---

## 3. Instalação e Execução (Windows 11 / PowerShell)

Requisitos: **Python 3.12 ou superior** e **Git**.

### 3.1 Configuração do Ambiente Virtual

Abra o terminal **PowerShell** no diretório do projeto:

```powershell
# 1. Se o PowerShell bloquear a execução de scripts do venv, rode:
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

# 2. Crie e ative o ambiente virtual
python -m venv venv
.\venv\Scripts\Activate.ps1

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Aplique as migrações do banco de dados
python manage.py migrate

# 5. Crie o usuário administrador (recepção)
python manage.py createsuperuser
```

---

## 4. Executando em Duas ou Três Máquinas na Mesma Rede

Para demonstrar a distribuição na banca com notebooks diferentes conectados ao mesmo Wi-Fi ou rede local:

### Passo 1: No Notebook do Servidor (Onde o Django roda)

1. Descubra o IP local da sua máquina:
   ```powershell
   ipconfig
   ```
   Procure por **Endereço IPv4** do seu adaptador Wi-Fi ou Ethernet (exemplo: `192.168.1.15`).

2. Liberar a porta 8000 no Firewall do Windows (se necessário):
   ```powershell
   New-NetFirewallRule -DisplayName "Django Fila PS" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
   ```

3. Defina a variável `DJANGO_ALLOWED_HOSTS` incluindo seu IP e inicie o servidor:
   ```powershell
   $env:DJANGO_ALLOWED_HOSTS = "localhost,127.0.0.1,192.168.1.15"
   python manage.py runserver 0.0.0.0:8000
   ```

---

### Passo 2: No Notebook da Recepção (Administrador)

Abra qualquer navegador e acesse:
```text
http://192.168.1.15:8000/admin-fila/
```
- Faça login com o usuário e senha criados no `createsuperuser`.
- O token é armazenado em `sessionStorage` e enviado no cabeçalho `Authorization: Token <key>`.
- Permite cadastrar pacientes, visualizar a fila em ordem de chegada, remover desistentes e chamar o próximo.

---

### Passo 3: No Notebook ou TV da Sala de Espera (Painel Público)

Abra o navegador e acesse:
```text
http://192.168.1.15:8000/painel/
```
- Acesso público (sem login ou credenciais).
- Clique no botão **"Ativar Som"** no canto superior direito para habilitar a Web Audio API (contornando a política de autoplay dos navegadores).
- O painel consultará `/api/painel/` a cada 2,5 segundos e tocará o aviso sonoro e voz a cada nova chamada.

---

## 5. Endpoints e Rotas do Sistema

### 5.1 Telas Web

| Rota | Tipo | Acesso | Descrição |
|---|---|---|---|
| `/admin-fila/` | HTML/CSS/JS | Administrador (login por token) | Gestão da recepção: cadastro, fila FIFO, remoção e chamada. |
| `/painel/` | HTML/CSS/JS | Público | Painel de TV: contagem, destaque do chamado, histórico, som e voz. |
| `/admin/` | HTML (Django) | Superusuário | Gerenciamento administrativo nativo do Django (salas, médicos, etc.). |

### 5.2 API REST (`/api/`)

| Método | Rota | Autenticação | Descrição |
|---|---|---|---|
| **POST** | `/api/auth/token/` | Pública | Login do operador. Recebe `{"username": "...", "password": "..."}` e devolve o Token. |
| **GET** | `/api/pacientes/` | Token Admin (`is_staff=True`) | Lista pacientes na fila (aceita `?status=aguardando`). |
| **POST** | `/api/pacientes/` | Token Admin (`is_staff=True`) | Cadastra paciente: `{"nome": "Maria Silva"}`. |
| **GET** | `/api/pacientes/{id}/` | Token Admin (`is_staff=True`) | Detalhes de um paciente específico. |
| **DELETE** | `/api/pacientes/{id}/` | Token Admin (`is_staff=True`) | Remoção lógica (`status="removido"`). Retorna 204 ou 409 se já removido. |
| **POST** | `/api/chamar-proximo/` | Token Admin (`is_staff=True`) | Chama o próximo da fila (FIFO): `{"sala": "Sala 1", "medico": "Dr. Carlos"}`. Retorna 404 se fila vazia. |
| **GET** | `/api/recursos-atendimento/` | Token Admin (`is_staff=True`) | Lista de salas e médicos com `ativo=True` para os seletores. |
| **GET** | `/api/painel/` | Pública (somente leitura) | Retorna contagem de aguardando, últimas chamadas (LGPD) e `ultima_chamada_id`. |

---

## 6. Roteiro de Demonstração para a Banca (Bloco 3)

Siga este passo a passo durante a apresentação:

1. **Demonstrar a Arquitetura Distribuída**:
   - Mostre o terminal no Servidor rodando `python manage.py runserver 0.0.0.0:8000`.
   - Abra a tela da recepção em `http://IP:8000/admin-fila/`.
   - Abra a tela da sala de espera em `http://IP:8000/painel/` (em outra máquina ou aba).
2. **Ativar o Áudio no Painel**:
   - No painel, clique em **"Ativar Som"**. O botão ficará verde indicando `🔊 Som: Ativo`.
3. **Cadastrar Pacientes**:
   - Na recepção (`/admin-fila/`), faça login como administrador.
   - Cadastre: "Carlos Eduardo Silva", "Beatriz Lima" e "Daniel Moreira".
   - Veja que no painel a contagem de **"Pessoas Aguardando" sobe imediatamente para 3**.
4. **Chamar o Próximo Paciente (Regra FIFO + Aviso Sonoro + LGPD)**:
   - Na recepção, selecione a Sala e o Médico e clique em **"Chamar Próximo da Fila"**.
   - Ouça o **aviso sonoro sintetizado** (dois tons harmônicos) e o anúncio em voz.
   - No painel, verifique que o paciente chamado foi o primeiro a chegar ("Carlos S.") respeitando a disciplina FIFO e a LGPD.
   - Veja a contagem de aguardando cair automaticamente para 2.
5. **Remover Paciente Desistente**:
   - Na recepção, clique em "Remover" ao lado de "Beatriz Lima".
   - Veja a contagem no painel atualizar para 1 sem interrupções.
6. **Esgotar a Fila e Testar Fila Vazia**:
   - Chame o último paciente ("Daniel Moreira"). A contagem vai a 0.
   - Tente clicar novamente em "Chamar Próximo da Fila": o sistema exibe aviso claro de **"Não há pacientes aguardando na fila"** (HTTP 404 tratado).
7. **Demonstrar Segurança (Autenticação 401/403)**:
   - Clique em "Sair" na recepção. O token é removido.
   - Tente fazer chamadas via terminal sem token:
     ```powershell
     curl -X POST http://localhost:8000/api/chamar-proximo/ -H "Content-Type: application/json" -d "{\"sala\":\"1\",\"medico\":\"Dr. X\"}"
     ```
     O servidor recusa com **HTTP 401 Unauthorized**.
8. **Demonstrar Robustez e Tolerância a Falhas de Rede**:
   - No terminal do servidor, pressione `Ctrl + C` para derrubar temporariamente a aplicação.
   - Observe o painel público:
     - **Nunca apaga a tela** (mantém o último estado conhecido).
     - Exibe aviso discreto no topo: `⚠️ Conexão perdida com o servidor. Mantendo último estado e tentando reconectar...`.
     - Inicia a estratégia de **backoff exponencial** (2s $\to$ 4s $\to$ 8s $\to$ 15s) evitando sobrecarga de requisições.
   - Reinicie o servidor (`python manage.py runserver 0.0.0.0:8000`).
   - O painel detecta o retorno da conexão, oculta o aviso e sincroniza o estado **sem disparar alarmes falsos de chamadas antigas**.

---

## 7. Testes Automatizados

O projeto possui **28 testes automatizados** cobrindo autenticação, permissões, privacidade LGPD, regras FIFO, integridade em concorrência e integridade das rotas web.

Para executar os testes:
```powershell
python manage.py test
```

Saída esperada:
```text
Ran 28 tests in ~0.5s
OK
```

> **Otimização:** A suíte de testes utiliza hasher rápido (MD5) exclusivamente no ambiente de teste, reduzindo a execução de ~64 segundos para menos de 1 segundo.

---

## 8. Desvios em Relação ao Bloco 1

| Componente / Decisão | Desenho Original (Bloco 1) | Implementação Real (Bloco 3) | Justificativa Técnica |
|---|---|---|---|
| **Banco de Dados** | PostgreSQL | **SQLite como padrão** (com suporte configurável a PostgreSQL via `.env`) | Garantir portabilidade imediata para execução e avaliação da banca em qualquer notebook sem dependência de containers Docker ou serviços PostgreSQL em execução no Windows. Suporte a PostgreSQL mantido por variáveis (`DB_ENGINE=postgresql`). |
| **Comunicação em Tempo Real** | WebSockets / SSE | **Short Polling inteligente (2,5s)** com `AbortController` e Backoff | WebSockets exigem dependências adicionais (Daphne/Channels/Redis) e frequentemente enfrentam bloqueios em redes Wi-Fi acadêmicas e corporativas (proxies/firewalls). O polling a cada 2,5s atendeu perfeitamente ao requisito de atualização contínua, com baixo overhead e alta tolerância a falhas de rede. |
| **Geração de Áudio** | Arquivos MP3/WAV estáticos | **Sintetizador Web Audio API puro + SpeechSynthesis** | Elimina dependência de arquivos externos no servidor, contorna limitações de codec e latência de rede em smart TVs, e adiciona acessibilidade por voz natural em português. |
| **Catálogo de Recursos** | Textos livres em cada chamada | **Modelos `Sala` e `Medico` com seleção dinâmica** | Facilita a rotina da recepção através de seleção rápida das salas e médicos ativos da unidade, mantendo compatibilidade com digitação livre caso necessário. |

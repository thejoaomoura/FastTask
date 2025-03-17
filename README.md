# FastTask - Gerenciador de Tarefas Simplificado

FastTask é um gerenciador de tarefas leve e moderno desenvolvido em Python com uma interface gráfica intuitiva. O aplicativo permite visualizar e gerenciar os processos em execução no sistema, monitorar o uso de CPU e RAM, e fornece funcionalidades avançadas para usuários que desejam um controle detalhado sobre os processos do sistema.

## 📋 Recursos Principais

- **Lista de Processos em Tempo Real**
  - Visualização dos processos ativos com nome, PID, uso de CPU/RAM e status
  - Atualização periódica configurável
  - Ordenação por diferentes critérios (nome, PID, uso de CPU, uso de RAM)

- **Gerenciamento de Processos**
  - Finalização de processos com confirmação para processos críticos
  - Alteração de prioridade de processos
  - Inicialização de novos processos

- **Monitoramento de Sistema**
  - Gráficos em tempo real de uso de CPU e RAM
  - Informações gerais do sistema
  - Detecção de processos com uso excessivo de recursos

- **Interface Amigável**
  - Interface moderna com suporte a modo claro e escuro
  - Visualização compacta ou detalhada dos processos
  - Filtro para busca rápida de processos

## 🔧 Requisitos do Sistema

- Python 3.8 ou superior
- Sistema operacional: Windows (suporte para Linux e macOS em desenvolvimento)
- Bibliotecas: psutil, PySide6, matplotlib ou pyqtgraph

## 📦 Instalação

1. Clone o repositório ou baixe os arquivos:
```
git clone https://github.com/thejoaomoura/fasttask.git
cd fasttask
```

2. Instale as dependências necessárias:
```
pip install -r requirements.txt
```

3. Execute o aplicativo:
```
python main.py
```

## 🚀 Uso

- **Visualização de Processos**:
  - Use a tabela principal para visualizar todos os processos em execução
  - Utilize o campo de busca para encontrar processos específicos
  - Clique nos cabeçalhos das colunas para ordenar

- **Gerenciamento de Processos**:
  - Selecione um processo e clique em "Finalizar Processo" ou use o menu de contexto (clique direito)
  - Para alterar a prioridade, use o menu de contexto → "Alterar Prioridade"
  - Para iniciar um novo processo, clique em "Novo Processo"

- **Configurações**:
  - Altere o intervalo de atualização através do menu "Visualização" → "Intervalo de Atualização"
  - Alterne entre visualização compacta e detalhada usando o checkbox "Modo Detalhado"

## 📂 Estrutura do Projeto

O projeto segue uma arquitetura modular para melhor organização e manutenibilidade:

- `main.py` - Ponto de entrada do aplicativo
- `ui.py` - Interface gráfica e componentes de UI
- `process_manager.py` - Gerenciamento de processos do sistema
- `monitoring.py` - Monitoramento de recursos do sistema
- `utils.py` - Funções utilitárias
- `settings.py` - Configurações da aplicação

## 🔒 Permissões

Algumas funcionalidades, como encerrar processos do sistema ou alterar prioridades, podem requerer privilégios de administrador. Para acessar todas as funcionalidades, execute o FastTask como administrador.

## 🤝 Contribuições

Contribuições são bem-vindas! Se você encontrar bugs ou tiver sugestões de recursos, abra uma issue ou envie um pull request.

## 📜 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para mais detalhes.

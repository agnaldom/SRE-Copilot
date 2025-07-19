# Testes de Conexão com Datadog

Este diretório contém uma suíte abrangente de testes para validar a integração com o Datadog no SRE Copilot.

## 📋 Visão Geral

Os testes cobrem todos os aspectos da conexão com Datadog:
- ✅ **Testes Unitários**: Validação de funcionalidades individuais
- ⚡ **Testes de Performance**: Validação de performance e escalabilidade  
- 🔗 **Testes de Integração**: Validação de fluxos completos
- 🚀 **Testes de Stress**: Validação sob carga alta

## 📁 Estrutura dos Arquivos

```
tests/
├── README.md                        # Esta documentação
├── conftest.py                      # Configurações globais e fixtures
├── test_datadog_connection.py       # Testes principais de conexão
└── test_datadog_performance.py      # Testes de performance e stress
```

## 🧪 Categorias de Testes

### 1. Testes de Conexão (`test_datadog_connection.py`)

#### `TestDatadogConnection`
- ✅ Inicialização bem-sucedida com credenciais válidas
- ❌ Falha na inicialização com credenciais ausentes
- 🔧 Configuração correta da API client

#### `TestDatadogMonitors`
- 📊 Busca de monitores ativos (P1/P2)
- 🏷️ Filtragem por tags
- 🎯 Filtragem por prioridade
- 🚨 Tratamento de erros da API
- 📭 Tratamento de resultados vazios

#### `TestDatadogLogs`
- 📝 Busca de logs com parâmetros padrão
- ⚙️ Busca de logs com parâmetros customizados
- ❌ Tratamento de erros na API de logs
- 🔄 Compatibilidade com diferentes formatos de resposta

#### `TestDatadogGeneralOperations`
- 🔍 Processamento de queries string e JSON
- ❓ Tratamento de ações desconhecidas
- 🚫 Funcionalidades não implementadas
- 💥 Tratamento de exceções gerais

#### `TestDatadogIntegration`
- 🔄 Fluxo completo end-to-end
- ⏰ Simulação de timeouts

### 2. Testes de Performance (`test_datadog_performance.py`)

#### `TestDatadogPerformance`
- 📈 **Teste de Dataset Grande**: 1000+ monitores
- 🔀 **Testes Concorrentes**: 10 requisições simultâneas
- 💾 **Teste de Memória**: Monitoramento de vazamentos
- ⏱️ **Teste de Timeout**: Tratamento de respostas lentas

#### `TestDatadogRateLimiting`
- 🚦 Tratamento de rate limiting (429)
- 💨 Testes de requisições em burst

#### `TestDatadogErrorScenarios`
- 🔐 Erro de autenticação (401)
- 🚫 Erro de permissão (403)
- 🚧 Serviço indisponível (503)
- 📋 Resposta malformada da API
- 🌐 Erro de conexão de rede
- 🔧 Erro de decodificação JSON

#### `TestDatadogStressTest`
- 🔄 **Estabilidade**: 100 requisições repetidas
- 🧠 **Detecção de Memory Leak**: 50 instâncias criadas/destruídas

## 🎯 Markers de Teste

Os testes utilizam markers para categorização:

- `@pytest.mark.unit` - Testes unitários básicos
- `@pytest.mark.integration` - Testes de integração
- `@pytest.mark.performance` - Testes de performance
- `@pytest.mark.slow` - Testes que demoram >5 segundos
- `@pytest.mark.datadog` - Específicos do Datadog

## 🚀 Como Executar

### Opção 1: Script Automatizado (Recomendado)

```bash
# Verificar ambiente
python run_datadog_tests.py --check

# Instalar dependências
python run_datadog_tests.py --install

# Testes rápidos (recomendado para desenvolvimento)
python run_datadog_tests.py --quick

# Todos os testes
python run_datadog_tests.py --all

# Testes de performance
python run_datadog_tests.py --performance

# Gerar relatório completo
python run_datadog_tests.py --report
```

### Opção 2: pytest Diretamente

```bash
# Todos os testes do Datadog
pytest tests/test_datadog_connection.py tests/test_datadog_performance.py -v

# Apenas testes unitários
pytest tests/test_datadog_connection.py -m "not (performance or slow)" -v

# Apenas testes de performance
pytest tests/test_datadog_performance.py -m "performance" -v

# Com cobertura de código
pytest tests/ --cov=tools --cov-report=html
```

### Opção 3: Testes Específicos

```bash
# Testar apenas inicialização
pytest tests/test_datadog_connection.py::TestDatadogConnection -v

# Testar apenas monitores
pytest tests/test_datadog_connection.py::TestDatadogMonitors -v

# Testar performance de monitores grandes
pytest tests/test_datadog_performance.py::TestDatadogPerformance::test_get_monitors_large_dataset -v
```

## 📊 Cobertura de Código

Os testes incluem medição de cobertura de código:

```bash
# Gerar relatório de cobertura
pytest tests/ --cov=tools --cov-report=html:htmlcov --cov-report=term-missing

# Visualizar relatório HTML
open htmlcov/index.html
```

Meta de cobertura: **≥80%**

## 🔧 Configuração

### Variáveis de Ambiente para Testes

```bash
# Não são necessárias para testes unitários (usam mocks)
# Apenas para testes de integração reais:
export DATADOG_API_KEY="sua_api_key_aqui"
export DATADOG_APP_KEY="sua_app_key_aqui"
```

### Dependências Adicionais

```bash
pip install pytest>=7.4.0 pytest-asyncio pytest-cov pytest-timeout psutil
```

## 📈 Métricas de Performance

### Benchmarks Esperados

| Teste | Tempo Esperado | Critério |
|-------|----------------|----------|
| Testes Unitários | <2 segundos | Individual <100ms |
| Processamento 1000 monitores | <5 segundos | Sem vazamento de memória |
| 10 requisições concorrentes | <10 segundos | Todas devem suceder |
| 100 requisições sequenciais | <30 segundos | ≥95% taxa de sucesso |

### Limites de Recursos

- **Memória**: Aumento máximo de 100MB para datasets grandes
- **Timeout**: 5 minutos por teste individual
- **Rate Limiting**: Tratamento gracioso de erros 429

## 🐛 Debugging

### Logs de Teste

```bash
# Executar com logs detalhados
pytest tests/ -v -s --log-cli-level=DEBUG

# Capturar apenas falhas
pytest tests/ --tb=short --maxfail=1
```

### Fixtures Disponíveis

- `mock_env_vars`: Mock das variáveis de ambiente
- `datadog_tool`: Instância mockada da ferramenta
- `sample_monitor_data`: Dados de exemplo de monitor
- `sample_logs_data`: Dados de exemplo de logs

## 🤝 Contribuindo

### Adicionando Novos Testes

1. **Testes Unitários**: Adicione em `test_datadog_connection.py`
2. **Testes de Performance**: Adicione em `test_datadog_performance.py`
3. **Fixtures Comuns**: Adicione em `conftest.py`

### Convenções

- Nomes de teste descritivos: `test_get_monitors_with_invalid_credentials`
- Documentação: Docstrings explicando o cenário testado
- Markers apropriados: `@pytest.mark.performance` para testes de performance
- Assertions claras: Mensagens de erro informativas

### Exemplo de Novo Teste

```python
@pytest.mark.unit
def test_get_monitors_with_custom_filter(self, datadog_tool):
    """Testa busca de monitores com filtro customizado."""
    # Setup
    mock_monitor = Mock()
    mock_monitor.id = 123
    # ... configurar mock
    
    datadog_tool.monitors_api.list_monitors.return_value = [mock_monitor]
    
    # Executar
    result = datadog_tool._run(json.dumps({
        "action": "get_monitors",
        "custom_filter": "value"
    }))
    
    # Verificar
    result_data = json.loads(result)
    assert result_data["status"] == "success"
    assert result_data["count"] == 1
```

## 📞 Suporte

Para problemas com os testes:

1. Verifique o ambiente: `python run_datadog_tests.py --check`
2. Execute testes rápidos primeiro: `python run_datadog_tests.py --quick`
3. Verifique logs detalhados: `pytest -v -s --tb=long`
4. Consulte a documentação da API do Datadog para mudanças

---

**📝 Nota**: Estes testes usam mocks por padrão, não fazendo chamadas reais à API do Datadog. Para testes de integração reais, configure as variáveis de ambiente apropriadas.

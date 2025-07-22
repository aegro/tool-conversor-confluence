# Guia do Pipeline Two-Stage (Duas Etapas)

## Visão Geral

O pipeline two-stage é uma abordagem avançada para converter exportações HTML do Confluence em Markdown de alta qualidade. Ele combina duas ferramentas poderosas:

1. **Etapa 1**: Limpeza e processamento HTML usando o conversor existente
2. **Etapa 2**: Conversão para Markdown usando Docling (ferramenta da IBM)

## Características Principais

- ✅ **Preservação de Imagens**: Imagens são mantidas como referências de arquivo, não embutidas em base64
- ✅ **Conversão de Alta Qualidade**: Docling fornece conversão superior de HTML para Markdown
- ✅ **Estrutura Preservada**: Mantém a hierarquia de pastas do Confluence
- ✅ **Processamento Otimizado**: Pipeline automatizado com script orquestrador

## Instalação

### Pré-requisitos

```bash
# Criar e ativar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt
```

### Dependências Específicas do Docling

O pipeline requer as seguintes bibliotecas adicionais:
- `docling`
- `docling-core`
- `docling-parse`
- `beautifulsoup4`

## Configuração

### 1. Arquivo de Configuração Two-Stage

Crie ou use o arquivo `config/two_stage_config.yaml`:

```yaml
# Configurações para conversão HTML
file_processing:
  process_html: true
  process_docx: false
  remove_confluence_footer: true
  group_by_parent_folder: true

# Configurações de imagem - IMPORTANTE!
image_settings:
  embed_as_base64: false  # Deve ser false para preservar referências
  download_external: false
  max_width: 800
  quality: 85

# Configurações de saída
output_settings:
  create_index: true
  preserve_structure: true
```

### 2. Configuração Padrão (Original)

Para usar o pipeline original com imagens embutidas, use `config/default_config.yaml`:

```yaml
image_settings:
  embed_as_base64: true  # Imagens embutidas em base64
  # ... outras configurações
```

## Uso

### Comando Básico

```bash
python run_two_stage_conversion.py -i <input_dir> -o <output_dir> [opções]
```

### Opções Disponíveis

- `-i, --input`: Diretório de entrada com arquivos HTML do Confluence (obrigatório)
- `-o, --output`: Diretório de saída para arquivos convertidos (obrigatório)
- `-c, --config`: Arquivo de configuração customizado (padrão: `config/two_stage_config.yaml`)
- `-v, --verbose`: Saída detalhada
- `-k, --keep-temp`: Manter arquivos temporários após conversão

### Exemplos

1. **Conversão básica**:
```bash
python run_two_stage_conversion.py -i input/SA -o output/two_stage_final
```

2. **Com configuração customizada e verbose**:
```bash
python run_two_stage_conversion.py \
    -i input/SA \
    -o output/two_stage_final \
    --config config/my_config.yaml \
    --verbose
```

3. **Mantendo arquivos temporários para debug**:
```bash
python run_two_stage_conversion.py \
    -i input/SA \
    -o output/debug \
    --keep-temp \
    --verbose
```

## Estrutura de Saída

```
output/two_stage_final/
├── markdown/           # Arquivos Markdown convertidos
│   └── SpaceName/
│       └── PageName.md
├── html/              # HTML limpo (referência)
│   └── SpaceName/
│       └── PageName.html
└── conversion_report.json  # Relatório de conversão
```

## Funcionamento Interno

### Etapa 1: Limpeza HTML

1. **Processamento**: Remove elementos desnecessários do HTML Confluence
2. **Imagens**: Com `embed_as_base64: false`, mantém referências originais
3. **Estrutura**: Preserva hierarquia de pastas
4. **Saída**: HTML limpo em `temp/cleaned_html`

### Etapa 2: Conversão Docling

1. **Entrada**: Lê HTML limpo da etapa anterior
2. **Conversão**: Docling converte HTML para Markdown
3. **Pós-processamento**: Corrige referências de imagem
4. **Saída**: Markdown final em `output/markdown`

### Tratamento de Imagens

O pipeline implementa um sistema robusto para imagens:

1. **URLs Externas**: Preservadas como estão
   ```markdown
   ![Alt text](https://example.com/image.png)
   ```

2. **Arquivos Locais**: Mantém caminhos relativos
   ```markdown
   ![image.png](../../attachments/123/image.png)
   ```

3. **Correção Automática**: Substitui comentários `<!-- image -->` por referências corretas

## Solução de Problemas

### Problema: Imagens aparecem como base64

**Solução**: Verifique se `embed_as_base64: false` no arquivo de configuração.

### Problema: Docling não encontrado

**Solução**: Instale as dependências do Docling:
```bash
pip install docling docling-core docling-parse
```

### Problema: Markdown com formatação HTML residual

**Solução**: Isso pode indicar que a limpeza HTML não foi completa. Verifique as configurações de `file_processing`.

## Performance

- **Tempo médio**: ~10 segundos por 100 arquivos
- **Memória**: Uso moderado, proporcional ao tamanho dos arquivos
- **CPU**: Processamento paralelo não implementado (possível melhoria futura)

## Comparação com Pipeline Original

| Característica | Pipeline Original | Pipeline Two-Stage |
|---------------|------------------|-------------------|
| Qualidade Markdown | Boa | Excelente |
| Preservação de Imagens | Opcional | Sempre preservadas |
| Velocidade | Rápida | Moderada |
| Dependências | Mínimas | Requer Docling |
| Formatação | Simples | Avançada |

## Desenvolvimento Futuro

- [ ] Processamento paralelo para melhor performance
- [ ] Suporte para mais formatos de saída
- [ ] Integração com sistemas de versionamento
- [ ] API REST para conversão remota

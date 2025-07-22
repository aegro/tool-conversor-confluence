# Próximos Passos - Conversão Markdown

## Status Atual ✅

A pipeline de conversão Markdown está totalmente funcional com:
- Conversão HTML → Markdown limpa e válida
- Extração e referenciamento de imagens
- Formatação avançada para elementos Confluence
- Remoção completa de CSS/JavaScript
- Taxa de conversão de 100%

## Melhorias Sugeridas

### 1. Integração com Docling 🔧

**Objetivo**: Usar a biblioteca docling para conversões mais avançadas

**Benefícios**:
- Melhor suporte para tabelas complexas
- Conversão de fórmulas matemáticas
- Processamento de PDFs embedados
- Extração de metadados

**Implementação**:
```python
# Em core/markdown_converter.py
from docling import Document

def convert_with_docling(self, html_content):
    doc = Document.from_html(html_content)
    return doc.to_markdown()
```

### 2. Processamento de Tabelas Avançado 📊

**Objetivo**: Melhorar a renderização de tabelas complexas

**Tarefas**:
- Detectar e preservar células mescladas
- Melhorar alinhamento de colunas
- Suportar tabelas aninhadas
- Adicionar suporte para tabelas com formatação especial

### 3. Suporte para Macros do Confluence 🔌

**Objetivo**: Converter macros específicas do Confluence

**Macros prioritárias**:
- Code blocks com syntax highlighting
- Panels (warning, info, note, tip)
- Table of Contents
- Excerpt/Include
- Status badges

**Exemplo de implementação**:
```python
def _convert_confluence_macros(self, soup):
    # Converter code blocks
    for macro in soup.find_all('ac:structured-macro', {'ac:name': 'code'}):
        language = macro.find('ac:parameter', {'ac:name': 'language'})
        code_content = macro.find('ac:plain-text-body')
        if code_content:
            markdown_code = f"```{language.text if language else ''}\n{code_content.text}\n```"
            macro.replace_with(markdown_code)
```

### 4. Pipeline de Pós-processamento 🔄

**Objetivo**: Adicionar etapas opcionais após conversão

**Funcionalidades**:
- Validação de links quebrados
- Otimização de imagens (compressão, redimensionamento)
- Geração de índice/sumário
- Conversão para outros formatos (PDF, DOCX via Markdown)

### 5. Configurações Avançadas ⚙️

**Objetivo**: Maior controle sobre a conversão

**Novas opções em config.yaml**:
```yaml
markdown:
  advanced_tables: true
  preserve_confluence_macros: false
  image_optimization:
    enabled: true
    max_width: 1200
    quality: 85
  post_processing:
    validate_links: true
    generate_toc: true
  docling_integration:
    enabled: false
    fallback_to_basic: true
```

### 6. Testes e Validação 🧪

**Objetivo**: Garantir qualidade consistente

**Implementar**:
- Suite de testes unitários para cada tipo de elemento
- Testes de regressão com casos edge
- Validação automática de Markdown (markdownlint)
- Benchmarks de performance

### 7. Melhorias de Performance ⚡

**Objetivo**: Otimizar para grandes volumes

**Estratégias**:
- Processamento paralelo de arquivos
- Cache de conversões repetidas
- Lazy loading de imagens
- Streaming para arquivos grandes

## Priorização Recomendada

1. **Alta Prioridade**
   - Integração básica com docling
   - Suporte para macros principais do Confluence
   - Testes unitários

2. **Média Prioridade**
   - Processamento avançado de tabelas
   - Pipeline de pós-processamento
   - Configurações avançadas

3. **Baixa Prioridade**
   - Otimizações de performance
   - Funcionalidades experimentais

## Conclusão

A base sólida já está implementada. As melhorias sugeridas ampliarão as capacidades mantendo a compatibilidade com o pipeline existente.

# Plano de Conversão em Duas Etapas com Docling

## Visão Geral

Implementar uma pipeline de conversão em duas etapas:
1. **Etapa 1**: Limpar HTML do Confluence (pipeline existente)
2. **Etapa 2**: Converter HTML limpo para Markdown usando Docling

## Arquitetura Proposta

```
input/SA/                    → Etapa 1 →    temp/cleaned_html/        → Etapa 2 →    output/markdown_docling/
(HTML Confluence bruto)      (Limpeza)      (HTML limpo)              (Docling)      (Markdown final)
```

## Detalhamento das Etapas

### Etapa 1: Limpeza HTML (Existente)

**Comando**:
```bash
python main.py --input input/SA --output temp/cleaned_html
```

**Processo**:
- Remove scripts maliciosos
- Limpa estilos inline desnecessários
- Corrige estrutura HTML
- Preserva links e imagens
- Mantém hierarquia de arquivos

**Saída**: HTML limpo em `temp/cleaned_html/`

### Etapa 2: Conversão Docling (Nova)

**Comando**:
```bash
python docling_converter.py --input temp/cleaned_html --output output/markdown_docling
```

**Processo**:
- Usa Docling para conversão avançada HTML → Markdown
- Preserva formatação complexa (tabelas, listas aninhadas)
- Converte fórmulas matemáticas
- Extrai e processa imagens
- Mantém metadados do documento

## Implementação Detalhada

### 1. Instalação de Dependências

```bash
pip install docling docling-core docling-parse
```

Atualizar `requirements.txt`:
```
docling>=2.0.0
docling-core>=2.0.0
docling-parse>=2.0.0
```

### 2. Script Principal: `docling_converter.py`

```python
#!/usr/bin/env python3
"""
Docling Converter - Segunda etapa da pipeline de conversão
Converte HTML limpo para Markdown usando Docling
"""

import argparse
import logging
from pathlib import Path
from typing import Optional, Dict, List
import sys

from docling import Document, DoclingSettings
from docling.document_converter import DocumentConverter, ConversionSettings
from docling.datamodel.document import ConversionResult

class DoclingMarkdownConverter:
    def __init__(self, input_dir: Path, output_dir: Path, config: Optional[Dict] = None):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.config = config or {}
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def convert_file(self, html_file: Path) -> Optional[Path]:
        """Converte um arquivo HTML para Markdown usando Docling"""
        try:
            # Configurar settings do Docling
            settings = DoclingSettings(
                include_images=self.config.get('include_images', True),
                extract_tables=self.config.get('extract_tables', True),
                extract_formulas=self.config.get('extract_formulas', True),
                markdown_options={
                    'table_format': 'grid',  # ou 'pipe' para formato mais simples
                    'heading_style': 'atx',   # usa # para headings
                    'code_style': 'fenced',   # usa ``` para blocos de código
                }
            )
            
            # Converter documento
            converter = DocumentConverter(settings=settings)
            result: ConversionResult = converter.convert(html_file)
            
            if result.status == "success":
                # Determinar caminho de saída
                relative_path = html_file.relative_to(self.input_dir)
                output_path = self.output_dir / relative_path.with_suffix('.md')
                
                # Criar diretório se necessário
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Salvar markdown
                markdown_content = result.document.to_markdown()
                output_path.write_text(markdown_content, encoding='utf-8')
                
                # Processar imagens se necessário
                self._process_images(result, output_path.parent)
                
                self.logger.info(f"Convertido: {html_file} → {output_path}")
                return output_path
            else:
                self.logger.error(f"Falha na conversão de {html_file}: {result.error}")
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao converter {html_file}: {str(e)}")
            return None
            
    def _process_images(self, result: ConversionResult, output_dir: Path):
        """Processa e salva imagens extraídas"""
        if hasattr(result.document, 'images'):
            images_dir = output_dir / 'images'
            images_dir.mkdir(exist_ok=True)
            
            for img_id, img_data in result.document.images.items():
                img_path = images_dir / f"{img_id}.png"
                img_path.write_bytes(img_data)
                self.logger.debug(f"Imagem salva: {img_path}")
                
    def convert_all(self) -> Dict[str, int]:
        """Converte todos os arquivos HTML no diretório de entrada"""
        stats = {'success': 0, 'failed': 0, 'total': 0}
        
        # Encontrar todos os arquivos HTML
        html_files = list(self.input_dir.rglob('*.html'))
        stats['total'] = len(html_files)
        
        self.logger.info(f"Encontrados {stats['total']} arquivos HTML para converter")
        
        # Converter cada arquivo
        for html_file in html_files:
            if self.convert_file(html_file):
                stats['success'] += 1
            else:
                stats['failed'] += 1
                
        return stats

def main():
    parser = argparse.ArgumentParser(
        description='Converte HTML limpo para Markdown usando Docling'
    )
    parser.add_argument(
        '--input', '-i',
        type=Path,
        required=True,
        help='Diretório com HTML limpo (saída da etapa 1)'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        required=True,
        help='Diretório de saída para arquivos Markdown'
    )
    parser.add_argument(
        '--config', '-c',
        type=Path,
        help='Arquivo de configuração YAML (opcional)'
    )
    
    args = parser.parse_args()
    
    # Validar diretórios
    if not args.input.exists():
        print(f"Erro: Diretório de entrada não existe: {args.input}")
        sys.exit(1)
        
    # Criar diretório de saída
    args.output.mkdir(parents=True, exist_ok=True)
    
    # Carregar configuração se fornecida
    config = {}
    if args.config and args.config.exists():
        import yaml
        with open(args.config) as f:
            config = yaml.safe_load(f)
    
    # Executar conversão
    converter = DoclingMarkdownConverter(args.input, args.output, config)
    stats = converter.convert_all()
    
    # Reportar resultados
    print(f"\nConversão concluída:")
    print(f"  Total: {stats['total']}")
    print(f"  Sucesso: {stats['success']}")
    print(f"  Falhas: {stats['failed']}")
    print(f"  Taxa de sucesso: {stats['success']/stats['total']*100:.1f}%")
    
    sys.exit(0 if stats['failed'] == 0 else 1)

if __name__ == '__main__':
    main()
```

### 3. Script de Pipeline Completa: `run_two_stage_conversion.py`

```python
#!/usr/bin/env python3
"""
Script para executar a conversão completa em duas etapas
"""

import subprocess
import sys
from pathlib import Path
import shutil
import argparse
import time

def run_command(cmd: list, description: str) -> bool:
    """Executa um comando e retorna sucesso/falha"""
    print(f"\n{'='*60}")
    print(f"Executando: {description}")
    print(f"Comando: {' '.join(cmd)}")
    print('='*60)
    
    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    elapsed_time = time.time() - start_time
    
    if result.returncode == 0:
        print(f"✅ Sucesso em {elapsed_time:.1f}s")
        if result.stdout:
            print("Saída:", result.stdout)
        return True
    else:
        print(f"❌ Falha após {elapsed_time:.1f}s")
        if result.stderr:
            print("Erro:", result.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Executa conversão Confluence → Markdown em duas etapas'
    )
    parser.add_argument('--input', '-i', type=Path, required=True,
                        help='Diretório com HTML do Confluence')
    parser.add_argument('--output', '-o', type=Path, required=True,
                        help='Diretório final para Markdown')
    parser.add_argument('--temp-dir', type=Path, default=Path('temp/cleaned_html'),
                        help='Diretório temporário para HTML limpo')
    parser.add_argument('--keep-temp', action='store_true',
                        help='Manter arquivos temporários após conversão')
    
    args = parser.parse_args()
    
    # Validar entrada
    if not args.input.exists():
        print(f"Erro: Diretório de entrada não existe: {args.input}")
        sys.exit(1)
    
    # Criar diretórios
    args.temp_dir.mkdir(parents=True, exist_ok=True)
    args.output.mkdir(parents=True, exist_ok=True)
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║         Conversão Confluence → Markdown (Duas Etapas)        ║
╚══════════════════════════════════════════════════════════════╝
    
📁 Entrada: {args.input}
🔄 Temporário: {args.temp_dir}
📁 Saída: {args.output}
""")
    
    # Etapa 1: Limpeza HTML
    stage1_success = run_command(
        ['python', 'main.py', '--input', str(args.input), '--output', str(args.temp_dir)],
        'Etapa 1: Limpeza HTML do Confluence'
    )
    
    if not stage1_success:
        print("\n❌ Falha na Etapa 1. Abortando.")
        sys.exit(1)
    
    # Etapa 2: Conversão Docling
    stage2_success = run_command(
        ['python', 'docling_converter.py', '--input', str(args.temp_dir), '--output', str(args.output)],
        'Etapa 2: Conversão Docling (HTML → Markdown)'
    )
    
    if not stage2_success:
        print("\n❌ Falha na Etapa 2. Abortando.")
        sys.exit(1)
    
    # Limpar temporários se solicitado
    if not args.keep_temp and args.temp_dir.exists():
        print(f"\n🗑️  Removendo arquivos temporários em {args.temp_dir}")
        shutil.rmtree(args.temp_dir)
    
    print(f"""
✅ Conversão concluída com sucesso!
📁 Arquivos Markdown disponíveis em: {args.output}
""")

if __name__ == '__main__':
    main()
```

### 4. Configuração Docling: `config/docling_config.yaml`

```yaml
# Configuração para conversão Docling
docling:
  # Processamento de imagens
  include_images: true
  image_format: png
  max_image_width: 1200
  
  # Processamento de tabelas
  extract_tables: true
  table_format: grid  # grid, pipe, html
  
  # Processamento de fórmulas
  extract_formulas: true
  formula_format: latex
  
  # Opções de Markdown
  markdown:
    heading_style: atx      # atx: #, setext: sublinhado
    code_style: fenced      # fenced: ```, indented: 4 espaços
    bullet_char: "-"        # -, *, +
    emphasis_char: "*"      # * ou _
    strong_char: "**"       # ** ou __
    
  # Processamento avançado
  advanced:
    extract_footnotes: true
    extract_headers_footers: false
    preserve_formatting: true
    clean_whitespace: true
```

## Vantagens da Abordagem

1. **Separação de Responsabilidades**
   - Etapa 1: Foca em limpar problemas específicos do Confluence
   - Etapa 2: Usa Docling para conversão avançada

2. **Flexibilidade**
   - Pode rodar etapas independentemente
   - Fácil debugar problemas em cada etapa
   - Permite experimentar com diferentes conversores

3. **Qualidade Superior**
   - Docling oferece conversão mais sofisticada
   - Melhor tratamento de elementos complexos
   - Preservação de formatação avançada

## Cronograma de Implementação

1. **Fase 1** (2-3 horas)
   - Instalar e testar Docling
   - Criar script básico `docling_converter.py`
   - Testar com alguns arquivos

2. **Fase 2** (2-3 horas)
   - Implementar pipeline completa
   - Criar script `run_two_stage_conversion.py`
   - Adicionar configurações avançadas

3. **Fase 3** (1-2 horas)
   - Testes extensivos
   - Ajustes de performance
   - Documentação

## Próximos Passos

1. Instalar dependências do Docling
2. Implementar `docling_converter.py`
3. Testar com subset de arquivos
4. Criar script de pipeline completa
5. Executar conversão completa e validar resultados

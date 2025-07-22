#!/usr/bin/env python3
"""
Docling Converter - Segunda etapa da pipeline de conversão
Converte HTML limpo para Markdown usando Docling
"""

import argparse
import logging
import time
import yaml
import re
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional
from bs4 import BeautifulSoup

# Importar Docling
try:
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PipelineOptions
    from docling.backend.docling_parse_backend import DoclingParseDocumentBackend
except ImportError as e:
    print(f"Erro ao importar Docling: {e}")
    print("Instale com: pip install docling docling-core docling-parse")
    sys.exit(1)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DoclingMarkdownConverter:
    """Conversor de HTML limpo para Markdown usando Docling"""
    
    def __init__(self, input_dir: Path, output_dir: Path, config: Optional[Dict] = None):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.config = config or {}
        
        # Configurar diretórios
        self.markdown_dir = self.output_dir / "markdown"
        self.html_dir = self.output_dir / "html"
        
        # Criar diretórios de saída
        self.markdown_dir.mkdir(parents=True, exist_ok=True)
        self.html_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar o conversor Docling
        self._setup_converter()
        
    def _setup_converter(self):
        """Configura o conversor Docling com as opções apropriadas"""
        # Criar conversor sem opções customizadas por enquanto
        # A API mudou e precisamos usar a configuração padrão
        self.converter = DocumentConverter(
            allowed_formats=[InputFormat.HTML]
        )
        
        logger.info("Conversor Docling configurado com sucesso")
        
    def convert_file(self, html_file: Path) -> Optional[Path]:
        """Converte um arquivo HTML para Markdown usando Docling"""
        try:
            logger.info(f"Convertendo: {html_file.name}")
            
            # Converter com Docling
            start_time = time.time()
            result = self.converter.convert(str(html_file))
            conversion_time = time.time() - start_time
            
            # Verificar se a conversão foi bem-sucedida
            if not result or not hasattr(result, 'document'):
                logger.error(f"Falha na conversão de {html_file}: resultado vazio")
                return None
            
            # Gerar Markdown
            markdown_content = result.document.export_to_markdown()
            
            # Determinar caminho de saída mantendo estrutura de diretórios
            relative_path = html_file.relative_to(self.input_dir)
            
            # Processar para cada space encontrado
            if relative_path.parts[0] == "html":
                # Estrutura: html/SpaceName/...
                space_parts = relative_path.parts[1:]
            else:
                space_parts = relative_path.parts
            
            # Criar caminho de saída para Markdown
            markdown_path = self.markdown_dir.joinpath(*space_parts).with_suffix('.md')
            markdown_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Pós-processar Markdown para corrigir imagens
            markdown_content = self._fix_image_references(markdown_content, html_file)
            
            # Salvar Markdown
            markdown_path.write_text(markdown_content, encoding='utf-8')
            
            # Copiar HTML limpo para referência
            html_output_path = self.html_dir.joinpath(*space_parts)
            html_output_path.parent.mkdir(parents=True, exist_ok=True)
            html_output_path.write_text(html_file.read_text(encoding='utf-8'), encoding='utf-8')
            
            # Processar imagens se existirem
            self._process_images(result, markdown_path.parent, html_file)
            
            logger.info(f"✓ Convertido em {conversion_time:.2f}s: {html_file.name} → {markdown_path.name}")
            
            return markdown_path
            
        except Exception as e:
            logger.error(f"Erro ao converter {html_file}: {str(e)}", exc_info=True)
            return None
            
    def _fix_image_references(self, markdown_content: str, html_file: Path) -> str:
        """Corrige referências de imagem no Markdown processado pelo Docling"""
        try:
            # Ler o HTML original para extrair as imagens
            html_content = html_file.read_text(encoding='utf-8')
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Encontrar todas as imagens no HTML
            img_tags = soup.find_all('img')
            
            # Contador para substituir os comentários <!-- image -->
            image_comment_pattern = re.compile(r'<!-- image -->')
            
            # Para cada imagem encontrada no HTML
            for img in img_tags:
                src = img.get('src', '')
                alt = img.get('alt', 'Image')
                
                if src:
                    # Criar a referência Markdown para a imagem
                    markdown_image = f"![{alt}]({src})"
                    
                    # Substituir o próximo comentário <!-- image --> pela referência real
                    markdown_content = image_comment_pattern.sub(markdown_image, markdown_content, count=1)
            
            return markdown_content
            
        except Exception as e:
            logger.warning(f"Erro ao corrigir referências de imagem: {e}")
            return markdown_content
    
    def _process_images(self, result, output_dir: Path, source_file: Path):
        """Processa e copia imagens associadas ao documento"""
        try:
            # Verificar se há diretório de imagens junto ao HTML
            source_images_dir = source_file.parent / "images" / source_file.stem
            
            if source_images_dir.exists() and source_images_dir.is_dir():
                # Criar diretório de imagens no destino
                dest_images_dir = output_dir / "images" / source_file.stem
                dest_images_dir.mkdir(parents=True, exist_ok=True)
                
                # Copiar todas as imagens
                import shutil
                for img_file in source_images_dir.iterdir():
                    if img_file.is_file() and img_file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif', '.svg']:
                        dest_path = dest_images_dir / img_file.name
                        shutil.copy2(img_file, dest_path)
                        logger.debug(f"Imagem copiada: {img_file.name}")
                        
        except Exception as e:
            logger.warning(f"Erro ao processar imagens: {e}")
            
    def convert_all(self) -> Dict[str, int]:
        """Converte todos os arquivos HTML no diretório de entrada"""
        stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0
        }
        
        # Encontrar todos os arquivos HTML
        html_files = list(self.input_dir.rglob('*.html'))
        stats['total'] = len(html_files)
        
        if stats['total'] == 0:
            logger.warning(f"Nenhum arquivo HTML encontrado em {self.input_dir}")
            return stats
            
        logger.info(f"Encontrados {stats['total']} arquivos HTML para converter")
        
        # Converter cada arquivo
        for i, html_file in enumerate(html_files, 1):
            # Pular arquivos index.html se configurado
            if self.config.get('skip_index_files', True) and html_file.name == 'index.html':
                logger.debug(f"Pulando arquivo index: {html_file}")
                stats['skipped'] += 1
                continue
                
            logger.info(f"[{i}/{stats['total']}] Processando: {html_file.name}")
            
            if self.convert_file(html_file):
                stats['success'] += 1
            else:
                stats['failed'] += 1
                
        return stats
        

def main():
    """Função principal do conversor Docling"""
    parser = argparse.ArgumentParser(
        description='Converte HTML limpo para Markdown usando Docling (Etapa 2)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  # Converter HTML limpo do diretório temporário
  python docling_converter.py -i temp/cleaned_html -o output/markdown_docling
  
  # Usar arquivo de configuração customizado
  python docling_converter.py -i temp/cleaned_html -o output/markdown_docling -c config/docling.yaml
        """
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
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Modo verboso (debug)'
    )
    
    args = parser.parse_args()
    
    # Configurar logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validar diretório de entrada
    if not args.input.exists():
        logger.error(f"Diretório de entrada não existe: {args.input}")
        sys.exit(1)
        
    if not args.input.is_dir():
        logger.error(f"Caminho de entrada não é um diretório: {args.input}")
        sys.exit(1)
        
    # Criar diretório de saída
    args.output.mkdir(parents=True, exist_ok=True)
    
    # Carregar configuração se fornecida
    config = {}
    if args.config and args.config.exists():
        try:
            import yaml
            with open(args.config, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f) or {}
                logger.info(f"Configuração carregada de {args.config}")
        except Exception as e:
            logger.warning(f"Erro ao carregar configuração: {e}")
    
    # Banner inicial
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║              Docling Converter - Etapa 2                     ║
╚══════════════════════════════════════════════════════════════╝
    
📁 Entrada (HTML limpo): {args.input}
📁 Saída (Markdown):     {args.output}
⚙️  Configuração:         {args.config or 'Padrão'}
    """)
    
    # Executar conversão
    start_time = time.time()
    converter = DoclingMarkdownConverter(args.input, args.output, config)
    stats = converter.convert_all()
    elapsed_time = time.time() - start_time
    
    # Relatório final
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    Conversão Concluída                       ║
╚══════════════════════════════════════════════════════════════╝

📊 Estatísticas:
   Total de arquivos:    {stats['total']}
   Convertidos:          {stats['success']}
   Falhas:               {stats['failed']}
   Pulados:              {stats['skipped']}
   Taxa de sucesso:      {stats['success']/max(stats['total']-stats['skipped'], 1)*100:.1f}%
   
⏱️  Tempo total:          {elapsed_time:.1f}s
📁 Arquivos Markdown em:  {args.output}/markdown
    """)
    
    # Código de saída baseado em falhas
    sys.exit(0 if stats['failed'] == 0 else 1)


if __name__ == '__main__':
    main()

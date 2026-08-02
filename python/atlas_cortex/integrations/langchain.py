import os
import json
import subprocess
import tempfile
import logging
import asyncio
from typing import List
from langchain_core.documents import Document

class AtlasCortexSplitter:
    """
    Integração Nativa do Atlas Cortex para LangChain.
    Usa o motor em Rust (AST via Tree-sitter) para quebrar o texto 
    em nós atômicos mantendo a hierarquia original (Semantic Routing).
    """

    def __init__(self, engine_path: str = None):
        """
        Inicializa o splitter.
        
        Args:
            engine_path (str): Caminho para o binário do motor Rust. 
                               Por padrão tenta achar no repositório.
        """
        if engine_path:
            self.engine_path = engine_path
        else:
            # Assumimos que o módulo Python está no repositório Atlas Cortex
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            # Para o script python/atlas_cortex/integrations/langchain.py, base_dir sobe até a raiz
            # Windows
            exe_path = os.path.join(base_dir, "engine", "target", "release", "engine.exe")
            # Linux/Mac
            bin_path = os.path.join(base_dir, "engine", "target", "release", "engine")
            
            if os.path.exists(exe_path):
                self.engine_path = exe_path
            elif os.path.exists(bin_path):
                self.engine_path = bin_path
            else:
                raise FileNotFoundError("Binário do motor Rust não encontrado. Rode 'cargo build --release' em /engine.")

    def split_text(self, text: str) -> List[str]:
        """Quebra um texto cru usando o motor Atlas Cortex e retorna as strings"""
        docs = self.split_documents([Document(page_content=text)])
        return [doc.page_content for doc in docs]

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """
        Interpreta objetos Document do LangChain e passa o conteúdo 
        pelo motor AST do Atlas Cortex.
        """
        final_docs = []

        for doc in documents:
            temp_path = None
            moc_path = None
            try:
                # Escreve o conteúdo temporariamente para o binário Rust ler
                with tempfile.NamedTemporaryFile(delete=False, suffix=".md", mode='w', encoding='utf-8') as temp_file:
                    temp_file.write(doc.page_content)
                    temp_path = temp_file.name
                
                # Chama o motor Rust
                result = subprocess.run(
                    [self.engine_path, temp_path],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    check=True
                )
                
                # Lê o json gerado (.moc.json)
                moc_path = temp_path.replace(".md", ".moc.json")
                if os.path.exists(moc_path):
                    with open(moc_path, 'r', encoding='utf-8') as f:
                        moc_data = json.load(f)
                    
                    nodes = moc_data.get("nodes", [])
                    
                    for node in nodes:
                        metadata = doc.metadata.copy()
                        metadata['atlas_node_id'] = node.get("id")
                        metadata['atlas_node_title'] = node.get("title")
                        
                        final_docs.append(
                            Document(
                                page_content=node.get("content", ""),
                                metadata=metadata
                            )
                        )
                else:
                    raise RuntimeError("Arquivo .moc.json não gerado pelo motor.")
            except Exception as e:
                logging.warning(f"Erro no motor Atlas Cortex: {e}. Fazendo fallback para o documento inteiro sem particionamento.")
                # Fallback em caso de erro grave (Devolve o original)
                final_docs.append(doc)
            finally:
                # Cleanup garantido
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except OSError:
                        pass
                if moc_path and os.path.exists(moc_path):
                    try:
                        os.remove(moc_path)
                    except OSError:
                        pass

        return final_docs
        
    async def asplit_documents(self, documents: List[Document]) -> List[Document]:
        """
        Versão assíncrona não bloqueante de split_documents.
        Utiliza ThreadPoolExecutor para evitar travar o event loop principal.
        """
        return await asyncio.to_thread(self.split_documents, documents)

"""
Document Processing Service
Handles chunking and parsing of various file types
"""

import re
from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib
import tiktoken

# Optional imports with fallbacks
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter, Language

    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

try:
    import PyPDF2

    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document

    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


class DocumentProcessor:
    """
    Process and chunk documents for RAG pipeline
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        model_name: str = "gpt-3.5-turbo",
    ):
        """
        Initialize document processor

        Args:
            chunk_size: Maximum size of each chunk (in tokens)
            chunk_overlap: Overlap between chunks
            model_name: Model for token counting
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        try:
            self.tokenizer = tiktoken.encoding_for_model(model_name)
        except:
            self.tokenizer = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.tokenizer.encode(text))

    def process_file(
        self, file_path: str, metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Process a file and return chunks with metadata

        Args:
            file_path: Path to the file
            metadata: Additional metadata

        Returns:
            List of chunk dictionaries
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        # Extract text based on file type
        if extension == ".pdf":
            text = self._extract_pdf(file_path)
        elif extension == ".docx":
            text = self._extract_docx(file_path)
        elif extension == ".md":
            text = self._extract_markdown(file_path)
        elif extension in [
            ".py",
            ".js",
            ".jsx",
            ".ts",
            ".tsx",
            ".php",
            ".java",
            ".cpp",
            ".c",
            ".go",
            ".rb",
        ]:
            text = self._extract_code(file_path)
        elif extension in [".txt", ".json", ".xml", ".html", ".css"]:
            text = self._extract_text(file_path)
        else:
            print(f"Unsupported file type: {extension}")
            return []

        if not text:
            return []

        # Determine language for code files
        language = self._detect_language(extension)

        # Chunk the text
        chunks = self._chunk_text(text, language)

        # Create chunk documents with metadata
        documents = []
        for i, chunk in enumerate(chunks):
            doc_id = self._generate_id(file_path, i)

            doc_metadata = {
                "source": str(path),
                "filename": path.name,
                "extension": extension,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "tokens": self.count_tokens(chunk),
                **(metadata or {}),
            }

            documents.append({"id": doc_id, "text": chunk, "metadata": doc_metadata})

        return documents

    def _extract_pdf(self, file_path: str) -> str:
        """Extract text from PDF"""
        if not PDF_AVAILABLE:
            raise ImportError("PyPDF2 not installed. Install with: pip install PyPDF2")

        try:
            with open(file_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n\n"
                return text.strip()
        except Exception as e:
            print(f"Error extracting PDF {file_path}: {e}")
            return ""

    def _extract_docx(self, file_path: str) -> str:
        """Extract text from DOCX"""
        if not DOCX_AVAILABLE:
            raise ImportError(
                "python-docx not installed. Install with: pip install python-docx"
            )

        try:
            doc = Document(file_path)
            text = "\n\n".join([para.text for para in doc.paragraphs])
            return text.strip()
        except Exception as e:
            print(f"Error extracting DOCX {file_path}: {e}")
            return ""

    def _extract_markdown(self, file_path: str) -> str:
        """Extract text from Markdown"""
        return self._extract_text(file_path)

    def _extract_code(self, file_path: str) -> str:
        """Extract code with comments preserved"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Error reading code file {file_path}: {e}")
            return ""

    def _extract_text(self, file_path: str) -> str:
        """Extract plain text"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, "r", encoding="latin-1") as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading text file {file_path}: {e}")
                return ""
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return ""

    def _detect_language(self, extension: str) -> Optional["Language"]:
        """Detect programming language from extension"""
        if not LANGCHAIN_AVAILABLE:
            return None

        lang_map = {
            ".py": Language.PYTHON,
            ".js": Language.JS,
            ".jsx": Language.JS,
            ".ts": Language.TS,
            ".tsx": Language.TS,
            ".php": Language.PHP,
            ".java": Language.JAVA,
            ".cpp": Language.CPP,
            ".c": Language.C,
            ".go": Language.GO,
            ".rb": Language.RUBY,
            ".rs": Language.RUST,
            ".md": Language.MARKDOWN,
            ".html": Language.HTML,
        }
        return lang_map.get(extension)

    def _chunk_text(self, text: str, language: Optional[Language] = None) -> List[str]:
        """
        Chunk text intelligently based on content type

        Args:
            text: Text to chunk
            language: Programming language (if code)

        Returns:
            List of text chunks
        """
        if not LANGCHAIN_AVAILABLE:
            # Fallback to simple chunking
            return self._simple_chunk(text)

        if language:
            # Use language-aware splitter for code
            splitter = RecursiveCharacterTextSplitter.from_language(
                language=language,
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
            )
        else:
            # Use general recursive splitter
            splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=["\n\n", "\n", ". ", " ", ""],
            )

        return splitter.split_text(text)

    def _simple_chunk(self, text: str) -> List[str]:
        """Simple character-based chunking (fallback)"""
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = start + self.chunk_size

            # Try to break at sentence or newline
            if end < text_length:
                # Look for sentence end
                sentence_end = text.rfind(". ", start, end)
                if sentence_end > start + self.chunk_size // 2:
                    end = sentence_end + 1
                else:
                    # Look for newline
                    newline = text.rfind("\n", start, end)
                    if newline > start + self.chunk_size // 2:
                        end = newline + 1

            chunks.append(text[start:end].strip())
            start = end - self.chunk_overlap

        return [c for c in chunks if c]  # Filter empty chunks

    def _generate_id(self, file_path: str, chunk_index: int) -> str:
        """Generate unique ID for a chunk"""
        source = f"{file_path}_{chunk_index}"
        return hashlib.md5(source.encode()).hexdigest()

    def process_directory(
        self,
        directory: str,
        file_extensions: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Process all files in a directory

        Args:
            directory: Directory path
            file_extensions: List of extensions to include (e.g., ['.py', '.md'])
            exclude_patterns: Patterns to exclude (e.g., ['__pycache__', 'node_modules'])
            metadata: Additional metadata for all files

        Returns:
            List of all chunk documents
        """
        path = Path(directory)
        if not path.exists():
            raise ValueError(f"Directory does not exist: {directory}")

        exclude_patterns = exclude_patterns or [
            "__pycache__",
            "node_modules",
            ".git",
            "venv",
            "env",
            ".pytest_cache",
            ".vscode",
            ".idea",
            "dist",
            "build",
        ]

        all_documents = []

        for file_path in path.rglob("*"):
            # Skip directories
            if file_path.is_dir():
                continue

            # Check exclusion patterns
            if any(pattern in str(file_path) for pattern in exclude_patterns):
                continue

            # Check file extension
            if file_extensions and file_path.suffix not in file_extensions:
                continue

            try:
                docs = self.process_file(str(file_path), metadata)
                all_documents.extend(docs)
                print(f"Processed: {file_path.name} ({len(docs)} chunks)")
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

        return all_documents

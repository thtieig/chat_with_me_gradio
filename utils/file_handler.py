import os
import mimetypes
import tempfile
import logging
from typing import List, Dict, Any, Union, Optional
import base64
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileHandler:
    def __init__(self, temp_dir: Optional[str] = None, config=None):
        """Initialize the file handler.
        
        Args:
            temp_dir: Directory to store temporary files (default: system temp dir)
            config: Configuration dictionary for file handling
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Load file handling config
        self.config = config or {}
        
        # Set default allowed extensions if not specified in config
        default_extensions = [
            '.py', '.js', '.html', '.css', '.json', '.md', '.txt', '.csv', 
            '.xml', '.yml', '.yaml', '.ini', '.cfg', '.conf'
        ]
        self.allowed_extensions = self.config.get("allowed_extensions", default_extensions)
        
        # Get other configuration parameters with defaults
        self.max_file_size_mb = self.config.get("max_file_size_mb", 10)
        self.max_files = self.config.get("max_files_per_upload", 100)
        self.max_text_size_mb = self.config.get("max_text_size_mb", 5.0)
        
        # Calculate derived values
        self.max_file_size_bytes = int(self.max_file_size_mb * 1024 * 1024)
        self.max_text_size_bytes = int(self.max_text_size_mb * 1024 * 1024)
        
        logger.info(f"FileHandler initialized with temp directory: {self.temp_dir}")
        logger.info(f"Allowed extensions: {self.allowed_extensions}")
        logger.info(f"Max file size: {self.max_file_size_mb} MB")
        logger.info(f"Max text size for reading: {self.max_text_size_mb} MB")
        logger.info(f"Max files per upload: {self.max_files}")
    
    def process_file(self, file) -> Dict[str, Any]:
        """Process a file uploaded through Gradio.
        
        Args:
            file: Gradio file object (supports NamedString in Gradio 5.24+)
            
        Returns:
            Dictionary with file metadata and content
        """
        try:
            # Handle different types of file objects that Gradio might provide
            if hasattr(file, "path"):
                filepath = file.path
                filename = getattr(file, "name", os.path.basename(filepath))
                logger.debug(f"Processing file with path attribute: {filepath}")
            elif hasattr(file, "name"):
                filepath = file.name
                filename = os.path.basename(filepath)
                logger.debug(f"Processing file with name attribute: {filepath}")
            elif isinstance(file, dict):
                filepath = file.get("path", "")
                filename = file.get("name", os.path.basename(filepath))
                logger.debug(f"Processing file as dictionary: {filepath}")
            else:
                filepath = str(file)
                filename = os.path.basename(filepath)
                logger.debug(f"Processing file as string: {filepath}")
            
            if not filepath or not os.path.exists(filepath):
                logger.warning(f"File not found: {filepath}")
                return {"error": f"File not found: {filepath}"}
            
            # Check file extension
            file_extension = os.path.splitext(filename)[1].lower()
            
            if self.allowed_extensions and file_extension not in self.allowed_extensions:
                logger.warning(f"Unsupported file type: {file_extension}")
                return {
                    "error": f"Unsupported file type: {file_extension}. Allowed extensions: {', '.join(self.allowed_extensions)}",
                    "filename": filename
                }
            
            mime_type, _ = mimetypes.guess_type(filepath)
            file_size = os.path.getsize(filepath)
            
            if file_size > self.max_file_size_bytes:
                logger.warning(f"File too large: {file_size/1024/1024:.1f} MB (max: {self.max_file_size_mb} MB)")
                return {
                    "error": f"File too large: {file_size/1024/1024:.1f} MB (max: {self.max_file_size_mb} MB)",
                    "filename": filename
                }
            
            logger.info(f"Processing file: {filename} ({file_size/1024:.1f} KB, {mime_type})")
            
            # Check if it's a text file
            is_text = False
            if mime_type and mime_type.startswith('text/'):
                is_text = True
            elif file_extension in self.allowed_extensions:
                is_text = True
            
            content = None
            if is_text:
                # Check file size before reading
                if file_size > self.max_text_size_bytes:
                    logger.warning(f"Text file too large to read fully: {file_size/1024/1024:.1f} MB")
                    return {
                        "filename": filename,
                        "filepath": filepath,
                        "mime_type": mime_type or "application/octet-stream",
                        "size": file_size,
                        "is_text": is_text,
                        "content": f"File too large to display ({file_size/1024/1024:.1f} MB)",
                        "extension": file_extension,
                        "warning": "File too large to read fully"
                    }
                
                # Try multiple encodings
                encodings = ['utf-8', 'latin-1', 'cp1252']
                for encoding in encodings:
                    try:
                        with open(filepath, 'r', encoding=encoding) as f:
                            content = f.read()
                        logger.debug(f"Successfully read file with encoding: {encoding}")
                        break
                    except UnicodeDecodeError:
                        continue
                    except Exception as e:
                        logger.error(f"Error reading file: {str(e)}")
                        return {"error": f"Error reading file: {str(e)}", "filename": filename}
                
                if content is None:
                    logger.warning(f"Could not decode file with any standard encoding")
                    return {"error": "Could not decode file with any standard encoding", "filename": filename}
            
            result = {
                "filename": filename,
                "filepath": filepath,
                "mime_type": mime_type or "application/octet-stream",
                "size": file_size,
                "is_text": is_text,
                "content": content,
                "extension": file_extension
            }
            return result
            
        except Exception as e:
            filename = getattr(file, "name", str(file)) if hasattr(file, "name") else "unknown file"
            logger.error(f"Unexpected error processing file {filename}: {str(e)}")
            return {"error": f"Unexpected error processing file: {str(e)}", "filename": filename}
    
    def format_files_for_llm(self, files: List[Dict[str, Any]]) -> str:
        """Format file information in a way suitable for LLM context.
        
        Args:
            files: List of file dictionaries from process_file/process_folder
            
        Returns:
            Formatted string describing files
        """
        formatted_text = "FILES PROVIDED:\n\n"
        
        for i, file in enumerate(files, 1):
            if "error" in file:
                formatted_text += f"File {i}: ERROR - {file.get('error')}\n\n"
                continue
            elif "warning" in file:
                formatted_text += f"File {i}: WARNING - {file.get('warning')}\n\n"
                continue
            elif "info" in file:
                formatted_text += f"Info: {file.get('info')}\n\n"
                continue
                
            formatted_text += f"File {i}: {file.get('filename')}\n"
            
            if "relative_path" in file:
                formatted_text += f"Path: {file.get('relative_path')}\n"
                
            formatted_text += f"Type: {file.get('mime_type')}\n"
            formatted_text += f"Size: {file.get('size')/1024:.1f} KB\n"
            
            if file.get("is_text") and file.get("content"):
                formatted_text += "Content:\n"
                formatted_text += "```"
                if file.get("extension"):
                    formatted_text += file.get("extension").lstrip(".")
                formatted_text += "\n"
                formatted_text += file.get("content", "")
                formatted_text += "\n```\n\n"
            else:
                formatted_text += "[Binary file - content not shown]\n\n"
        
        return formatted_text
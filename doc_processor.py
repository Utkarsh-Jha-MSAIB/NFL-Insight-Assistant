import os
from PyPDF2 import PdfReader
import docx
import json
import csv
import re

class DocumentProcessor:
    def __init__(self, docs_dir=None):
        # Use environment variable if available, otherwise use default
        self.docs_dir = docs_dir or os.getenv('DOCUMENTS_DIR', 'documents')
        self.knowledge_base = {}
        
        print("\n=== Initializing Document Processor ===")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Documents directory: {os.path.abspath(self.docs_dir)}")
        
        # Create documents directory if it doesn't exist
        if not os.path.exists(self.docs_dir):
            try:
                os.makedirs(self.docs_dir)
                print(f"Created documents directory: {self.docs_dir}")
            except Exception as e:
                print(f"Error creating documents directory: {str(e)}")
                print("Full traceback:")
                import traceback
                print(traceback.format_exc())
                return
        
        # Initialize the knowledge base
        self.load_all_documents()
        
        # Print summary
        print("\n=== Document Processor Summary ===")
        print(f"Total documents loaded: {len(self.knowledge_base)}")
        for doc_name, content in self.knowledge_base.items():
            if isinstance(content, str):
                print(f"- {doc_name}: {len(content)} characters")
            else:
                print(f"- {doc_name}: {type(content).__name__}")
        print("=== End Summary ===\n")
    
    def load_all_documents(self):
        """Load all documents from the documents directory"""
        print("\n=== Loading Documents ===")
        print(f"Documents directory: {os.path.abspath(self.docs_dir)}")
        
        if not os.path.exists(self.docs_dir):
            print(f"Error: Documents directory not found at {self.docs_dir}")
            return
            
        files = os.listdir(self.docs_dir)
        print(f"Found {len(files)} files in documents directory:")
        
        for filename in files:
            filepath = os.path.join(self.docs_dir, filename)
            try:
                print(f"\nProcessing file: {filename}")
                if filename.endswith('.pdf'):
                    self.load_pdf(filepath)
                elif filename.endswith('.docx'):
                    self.load_docx(filepath)
                elif filename.endswith('.txt'):
                    self.load_text(filepath)
                elif filename.endswith('.csv'):
                    self.load_csv(filepath)
                elif filename.endswith('.json'):
                    self.load_json(filepath)
                else:
                    print(f"Unsupported file type: {filename}")
            except Exception as e:
                print(f"Error loading {filename}: {str(e)}")
                import traceback
                print(traceback.format_exc())
        
        print(f"\nLoaded {len(self.knowledge_base)} documents into knowledge base")
        for doc_name in self.knowledge_base:
            content = self.knowledge_base[doc_name]
            if isinstance(content, str):
                print(f"- {doc_name}: {len(content)} characters")
            else:
                print(f"- {doc_name}: {type(content).__name__}")
    
    def extract_structured_content(self, text):
        """Extract and structure content from text"""
        content_blocks = []
        
        # Split text into paragraphs
        paragraphs = text.split('\n\n')
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            # Clean up the text
            paragraph = ' '.join(paragraph.split())  # Remove extra whitespace
            
            # Initialize metadata with default values
            metadata = {
                'dates': [],  # Empty list for dates
                'keywords': [],  # Empty list for keywords
                'type': 'paragraph'  # Default content type
            }
            
            content_blocks.append({
                'text': paragraph,
                'metadata': metadata
            })
        
        return content_blocks

    def load_pdf(self, filepath):
        """Extract text from PDF file"""
        try:
            filepath = os.path.normpath(filepath)
            print(f"\nProcessing PDF file: {filepath}")
            
            if not os.path.exists(filepath):
                print(f"Error: File not found at {filepath}")
                return
                
            print(f"File size: {os.path.getsize(filepath)} bytes")
            
            # Create a debug file with a safe name
            debug_filename = os.path.basename(filepath).replace(' ', '_') + '_debug.txt'
            debug_file = os.path.join(os.path.dirname(filepath), debug_filename)
            
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(f"=== PDF Processing Debug Log ===\n")
                f.write(f"File: {filepath}\n")
                f.write(f"Size: {os.path.getsize(filepath)} bytes\n\n")
            
            reader = PdfReader(filepath)
            print(f"Number of pages: {len(reader.pages)}")
            
            text = ""
            structured_content = []
            
            for i, page in enumerate(reader.pages, 1):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        # Clean up the text
                        page_text = ' '.join(page_text.split())  # Remove extra whitespace
                        text += page_text + "\n\n"
                        
                        # Extract structured content from this page
                        page_content = self.extract_structured_content(page_text)
                        structured_content.extend(page_content)
                        
                        # Write page content to debug file
                        with open(debug_file, 'a', encoding='utf-8') as f:
                            f.write(f"\n=== Page {i} ===\n")
                            f.write(page_text + "\n")
                            
                            if page_content:
                                f.write("\nStructured content found:\n")
                                for block in page_content:
                                    f.write(f"- {block['text'][:100]}...\n")
                                    # Only write metadata if dates exist
                                    if block['metadata']['dates'] and len(block['metadata']['dates']) > 0:
                                        f.write(f"  Context: {', '.join(block['metadata']['dates'])}\n")
                        
                        print(f"Extracted {len(page_text)} characters from page {i}")
                    else:
                        print(f"Warning: No text extracted from page {i}")
                        with open(debug_file, 'a', encoding='utf-8') as f:
                            f.write(f"\nWarning: No text extracted from page {i}\n")
                except Exception as page_error:
                    error_msg = f"Error extracting text from page {i}: {str(page_error)}"
                    print(error_msg)
                    with open(debug_file, 'a', encoding='utf-8') as f:
                        f.write(f"\n{error_msg}\n")
                    continue
            
            if text:
                # Store both raw text and structured content
                self.knowledge_base[os.path.basename(filepath)] = {
                    'text': text,
                    'structured_content': structured_content
                }
                
                print(f"Successfully loaded PDF: {filepath}")
                print(f"Total extracted text: {len(text)} characters")
                print(f"Content blocks: {len(structured_content)}")
                
                with open(debug_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n=== Summary ===\n")
                    f.write(f"Total text extracted: {len(text)} characters\n")
                    f.write(f"Content blocks: {len(structured_content)}\n")
                
                # Write the full text to a separate file for inspection
                text_file = os.path.join(os.path.dirname(filepath), os.path.basename(filepath).replace('.pdf', '_text.txt'))
                with open(text_file, 'w', encoding='utf-8') as f:
                    f.write(text)
                print(f"Full text saved to: {text_file}")
            else:
                error_msg = f"Warning: No text was extracted from PDF: {filepath}"
                print(error_msg)
                with open(debug_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n{error_msg}\n")
                
        except Exception as e:
            error_msg = f"Error loading PDF {filepath}: {str(e)}"
            print(error_msg)
            print("Full traceback:")
            import traceback
            print(traceback.format_exc())
            with open(debug_file, 'a', encoding='utf-8') as f:
                f.write(f"\n=== Error ===\n")
                f.write(error_msg + "\n")
                f.write(traceback.format_exc())
            raise
    
    def load_docx(self, filepath):
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(filepath)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            self.knowledge_base[os.path.basename(filepath)] = text
            print(f"Successfully loaded DOCX: {filepath}")
            print(f"Extracted {len(text)} characters")
        except Exception as e:
            print(f"Error loading DOCX {filepath}: {str(e)}")
            raise
    
    def load_text(self, filepath):
        """Load text file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                text = file.read()
                self.knowledge_base[os.path.basename(filepath)] = text
                print(f"Successfully loaded text file: {filepath}")
                print(f"Loaded {len(text)} characters")
        except Exception as e:
            print(f"Error loading text file {filepath}: {str(e)}")
            raise
    
    def load_csv(self, filepath):
        """Load CSV file as list of dictionaries"""
        try:
            data = []
            with open(filepath, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    data.append(row)
            self.knowledge_base[os.path.basename(filepath)] = data
            print(f"Successfully loaded CSV: {filepath}")
            print(f"Loaded {len(data)} rows")
        except Exception as e:
            print(f"Error loading CSV {filepath}: {str(e)}")
            raise
    
    def load_json(self, filepath):
        """Load JSON file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                data = json.load(file)
                self.knowledge_base[os.path.basename(filepath)] = data
                print(f"Successfully loaded JSON: {filepath}")
                print(f"Loaded {type(data).__name__} with {len(str(data))} characters")
        except Exception as e:
            print(f"Error loading JSON {filepath}: {str(e)}")
            raise
    
    def search_knowledge_base(self, query):
        """Search the knowledge base for relevant information"""
        query = query.lower()
        best_matches = []
        
        for doc_id, content in self.knowledge_base.items():
            # Handle both string content and structured content
            if isinstance(content, dict) and 'text' in content:
                text = content['text']
            else:
                text = str(content)
            
            # Split into sentences
            sentences = re.split(r'[.!?]+', text)
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                    
                sentence_lower = sentence.lower()
                
                # Simple relevance scoring based on term matching
                query_terms = query.split()
                matched_terms = sum(1 for term in query_terms if term in sentence_lower)
                
                if matched_terms > 0:
                    relevance = matched_terms / len(query_terms)
                    best_matches.append((relevance, sentence))
        
        # Sort by relevance score
        best_matches.sort(reverse=True, key=lambda x: x[0])
        
        # Return the most relevant sentences
        return [match[1] for match in best_matches[:500]]
    
    def get_document_context(self, query):
        """Get relevant context from documents for a given query"""
        relevant_info = self.search_knowledge_base(query)
        if not relevant_info:
            print("No relevant information found in documents")
            return ""
        
        context = "Based on our documents:\n"
        for info in relevant_info:
            context += f"\n{info}\n"
        
        print(f"Generated context with {len(context)} characters")
        return context 
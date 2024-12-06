from langchain_community.document_loaders import TextLoader, WebBaseLoader, PyPDFLoader
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.vectorstores import InMemoryVectorStore
from langchain_openai import OpenAIEmbeddings
import json
import chromadb
from chromadb.utils import embedding_functions

class VectorStore:
        
    def __init__(self):
                
        self.persistent_client = chromadb.PersistentClient(path="/home/appuser/database")
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size = 700,
            chunk_overlap = 30
        )          
        
        self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="paraphrase-multilingual-mpnet-base-v2")   
    
    def create_or_update_document(self, course_id, content_name, object_id, content, content_type, action):
        
        filepath = '' 
        if content_type == 'application/pdf':
            # Write the PDF content to output.pdf
            filepath += 'output.pdf'
            with open('output.pdf', 'wb') as f:
                f.write(content)
            loaders = [PyPDFLoader(filepath)]  
            content_type = 'resource'  
            
        elif content_type == 'text/plain':
            filepath += 'output.txt'
            # Write the text content to output.txt
            with open('output.txt', 'w') as f:
                f.write(content)
            loaders = [PyPDFLoader(filepath)]
            content_type = 'resource'  
            
        elif content_type == 'url':
            
            loaders = [WebBaseLoader(web_paths=[content])]
        else:
            raise ValueError("Unsupported content_type: " + content_type)
        
        docs = []

        for loader in loaders:
            docs.extend(loader.load())

        splits = self.text_splitter.split_documents(docs)
        
        collection = self.persistent_client.get_or_create_collection(name=str(course_id), embedding_function=self.emb_fn) 
        
        page_contents = [split.page_content for split in splits]
        metadatas = [{'object_id': str(object_id), 'content_name': content_name, 'content_type': content_type} for _ in splits]
        ids = [str(collection.count() + i) for i in range(1, len(splits) + 1)]
        
        if action == 1:
            collection.delete(
                where={"object_id": str(object_id)}
            )  
        
        collection.add(
            documents=page_contents,
            metadatas=metadatas,
            ids=ids
        )
        
        print("File was saved successfully")
        
        
    def delete_document(self, course_id, object_id):
        print("course_id to be deleted: ", course_id)
        collection = self.persistent_client.get_or_create_collection(name=str(course_id), embedding_function=self.emb_fn) 
        collection.delete(
            where={"object_id": str(object_id)}
        )
        
        print("File was deleted successfully")

        
    
    def retrieve(self, course_id, query, type_filter):
        
        collection = self.persistent_client.get_or_create_collection(name=str(course_id), embedding_function=self.emb_fn) 

        docs = collection.query(
            query_texts=[str(query)],
            n_results=2,
            where={
                "content_type": {
                    "$in": type_filter
                }
            }
        )
        print("docs length : ", len(docs['ids'][0]))
                
        if len(docs['ids'][0]) == 0:
            return None
        
        concatenated_docs = ''.join(doc for doc in docs['documents'][0])
        
        return concatenated_docs
         



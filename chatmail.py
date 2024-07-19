import os 
import time 
import inmail 
import outmail 
import subprocess 
from langchain_community.llms import CTransformers 
from langchain_community.document_loaders.text import TextLoader 
from langchain_community.embeddings import HuggingFaceEmbeddings 
from langchain_community.vectorstores import FAISS
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.runnables import RunnablePassthrough
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain


modelsdir = '/home/mtim.jones/chatmail/models/'

def load_llm( model ):

    config = { 'max_new_tokens': 512, 'temperature': 0.7, 'threads': 4 }

    # Create an LLM and query it.
    llm = CTransformers( model=modelsdir+model, model_type='llama', config=config )

    return llm


def inference( model, body ):

    system = 'You are a helpful AI assistant. ' \
             'Please answer the following question in a clear and factual manner.'

    print( model )

    # Llama-2 chat prompt
    prompt = '[INST] <<SYS>\n' + system + '\n<</SYS>>\n{' + body.rstrip() + '}[/INST]'

    print(prompt)

    llm = load_llm( model )

    cmd_resp = llm( prompt )

    return cmd_resp


def rag( model, filename, body ):

    template = (
        "Use the following pieces of context to answer the question at the end. "
        "If you don't know the answer, just say that you don't know and don't try to make up an "
        "answer.  Use three sentences maximum and keep the answer as concise as possible."
        "\n\n"
        "{context}"
    )

    loader = TextLoader( filename )

    docs = loader.load( )

    splitter = RecursiveCharacterTextSplitter( chunk_size=256, chunk_overlap=26 )

    texts = splitter.split_documents( docs )

    embeddings = HuggingFaceEmbeddings( model_name='sentence-transformers/all-MiniLM-L6-v2' )

    db = FAISS.from_documents( texts, embeddings )

    print("Loaded documents\n")

    retriever = db.as_retriever( search_kwargs={'k': 3} )

    print("Created retriever\n")

    config = { 'max_new_tokens': 512, 'temperature': 0.7, 'threads': 4, 'context_length': 2048 }

    llm = CTransformers( model = modelsdir+model, model_type = 'llama', config = config )

    print("Created LLM\n")

    custom_rag_prompt = ChatPromptTemplate.from_messages( [ ( "system", template ), ( "human", "{input}" ), ] )

    print("Created template\n")

    qa_chain = create_stuff_documents_chain( llm, custom_rag_prompt )
    rag_chain = create_retrieval_chain( retriever, qa_chain )

    cmd_resp = rag_chain.invoke( { "input": body } )

    print( cmd_resp["answer"] )

    return cmd_resp["answer"]


def list_models( ):

    models = ''
    path = os.path.join( './', 'models' )

    for r, d, f in os.walk( path ):
        for file in f:
            models = models + file + '\n'

    return models


def help( ):

    return 'Chatmail\n\n' \
           'Commands (subject) = [ chat | chat <model> | models | help ]\n\n'


def chatmail( ):

    resp = ''

    print( "Running..." )

    while True:

        try:

            # Establish a connection to the POP3 server and get a message
            pop3 = inmail.InMail( )
            pop3.login( )
            sender, subject, body, filename = pop3.get_email( )
            pop3.logout( )

            # If an email was received, process it.
            if sender is not None:

                arguments = list( subject.split( ' ' ) )
                if len( arguments ) == 0:
                    command = "empty"
                else:
                    command = arguments[0].lower()

                    if len( arguments ) > 1:
                        model = arguments[1]
                    else:
                        model = 'Meta-Llama-3-8B-Q4_5_M.gguf'

                if command == 'chat':
                    resp = inference( model, body )
                elif command == 'ragchat':
                    print( f'ragchat {filename}' )
                    resp = rag( model, filename, body )
                elif command == 'models':
                    resp = list_models( )
                elif command == 'help':
                    resp = help( )
                else:
                    print( f"Unknown command {command}." )
                    continue

                # Establish a connection with the SMTP server and send the response in the body.
                smtp = outmail.OutMail( )
                smtp.login( )
                smtp.send_response( sender, subject, resp )
                smtp.logout( )

        except Exception as e:

            print( e )

        time.sleep( 10 )


if __name__ == "__main__":
    chatmail()


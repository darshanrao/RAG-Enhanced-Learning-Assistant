from flask import Flask, request, jsonify
import pyarrow.fs
import sycamore
import json
import os
import shutil
from pinecone import Pinecone
from sycamore.functions.tokenizer import HuggingFaceTokenizer
from sycamore.llms import OpenAIModels, OpenAI
from sycamore.transforms import COALESCE_WHITESPACE
from sycamore.transforms.merge_elements import GreedySectionMerger
from sycamore.transforms.partition import ArynPartitioner
from sycamore.transforms.embed import SentenceTransformerEmbedder
from sycamore.materialize_config import MaterializeSourceMode
from sycamore.utils.pdf_utils import show_pages
from sycamore.transforms.summarize_images import SummarizeImages
from sycamore.context import ExecMode
from pinecone import ServerlessSpec
from dotenv import load_dotenv
from verifier import verify_short_answer
from mcq_gen import generate_mcq
from shortq_gen import generate_shortq
from pinecone_fetch import pinecone_retrieval
from sentence_transformers import SentenceTransformer
from handout_gen import generate_handout
from upload import download_and_upload_video
from marengo_search import *
from sycamore.transforms.regex_replace import COALESCE_WHITESPACE
from sycamore.transforms.extract_schema import OpenAIPropertyExtractor
from sycamore.llms import OpenAI, OpenAIModels
from transformers import AutoTokenizer
from sycamore.transforms.merge_elements import MarkedMerger
import pinecone

# Load environment variables
load_dotenv()
ARYN_API_KEY = os.getenv("ARYN_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

app = Flask(__name__)
hf_tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")

@app.route('/upload-embedding', methods=['POST'])
def upload_embedding():
    try:
        # Parse request data
        data = request.get_json()
        if not data or 'file_name' not in data or 'type_of_question' not in data or 'number_of_questions' not in data or 'user_prompt_text' not in data:
            return jsonify({"error": "Invalid input. 'file_name', 'type_of_question', 'number_of_questions', and 'user_prompt_text' are required."}), 400

        file_name = data['file_name']
        type_of_question = data['type_of_question']
        number_of_questions = data['number_of_questions']
        user_prompt_text = data['user_prompt_text']

        # Access the file from the specified path
        file_path = os.path.join("/tmp", file_name)
        file_path = file_name
        print(file_path)
        if not os.path.exists(file_path):
            return jsonify({"error": f"File {file_name} does not exist at the specified path."}), 404

        # Initialize the Sycamore context
        ctx = sycamore.init(ExecMode.LOCAL)
        # print("Print 1")
        # initial_docset = ctx.read.binary(paths = file_path, binary_format = "pdf")
        
        # try:
        #     shutil.rmtree("./pc-tutorial/partitioned", ignore_errors=True)
        # except:
        #     a=1
        # # Set your Aryn API key. See https://sycamore.readthedocs.io/en/stable/aryn_cloud/accessing_the_partitioning_service.html#using-sycamore-s-partition-transform

        # partitioned_docset = (
        #         initial_docset.partition(partitioner=ArynPartitioner(extract_images=False,  extract_table_structure=True, use_ocr=True))
        #         .materialize(path="./pc-tutorial/partitioned", source_mode=sycamore.materialize_config.MaterializeSourceMode.IF_PRESENT)
        # )
        # partitioned_docset.execute()
        
        # regex_docset = partitioned_docset.regex_replace(COALESCE_WHITESPACE)
        
        # llm = OpenAI(OpenAIModels.GPT_4O.value, api_key=os.environ["OPENAI_API_KEY"])

        # enriched_docset = (regex_docset
        #     .with_property('_schema_class', lambda d: 'LectureSlides')
        #     .with_property('_schema', lambda d: {
        #             'type': 'object',
        #     'properties': {
        #         'topicName': {'type': 'string'},
        #         'keyConcepts': {'type': 'string'}
        #     },
        #     'required': ['keyConcepts']}
        #                 )
        #     .extract_properties(property_extractor=OpenAIPropertyExtractor(llm=llm, num_of_elements=35))
        # )
        

        # # Step 2: Define a custom tokenizer class
        # class CustomTokenizer:
        #     def __init__(self, tokenizer, max_tokens):
        #         self.tokenizer = tokenizer
        #         self.max_tokens = max_tokens

        #     def tokenize(self, text):
        #         # Tokenize the input text using Hugging Face tokenizer
        #         tokens = self.tokenizer.tokenize(text)
        #         return tokens

        #     def token_count(self, text):
        #         # Count tokens for the given text
        #         return len(self.tokenize(text))

        #     def truncate(self, text):
        #         # Truncate the text to fit within max tokens
        #         tokens = self.tokenize(text)
        #         if len(tokens) > self.max_tokens:
        #             tokens = tokens[:self.max_tokens]
        #         return self.tokenizer.convert_tokens_to_string(tokens)

        # # Step 3: Initialize the custom tokenizer
        # max_tokens = 8192
        # tokenizer = CustomTokenizer(tokenizer=hf_tokenizer, max_tokens=max_tokens)

        # chunked_docset = (enriched_docset
        #     .mark_bbox_preset(tokenizer=tokenizer, token_limit=max_tokens)
        #     .merge(merger=MarkedMerger())
        #     .split_elements(tokenizer=tokenizer, max_tokens=max_tokens)
        # )
        # exploded_docset = chunked_docset.spread_properties(["path", "entity"]).explode()
        # model_name = "sentence-transformers/all-MiniLM-L6-v2"

        # embedded_ds = (
        #     exploded_docset
        #     # Embed each Document. You can change the embedding model. Make your target vector index matches this number of dimensions.
        #     .embed(embedder=SentenceTransformerEmbedder(model_name=model_name))
        # )
        
        # embedding_dim = 384

        # embedded_ds.write.pinecone(
        #     index_name="sbhacks",
        #     index_spec=pinecone.ServerlessSpec(cloud="aws", region="us-east-1"),
        #     dimensions=embedding_dim,
        #     distance_metric="cosine",
        # )

        # Set the embedding model and its parameters
        # model_name = "sentence-transformers/all-MiniLM-L6-v2"
        # max_tokens = 512
        # dimensions = 384

        # # Initialize the tokenizer
        # tokenizer = HuggingFaceTokenizer(model_name)
        # print("Print 2")
        # # Process the document
        # ds = (
        #     ctx.read.binary(file_path, binary_format="pdf")
        #     .partition(partitioner=ArynPartitioner(
        #         threshold="auto",
        #         use_ocr=True,
        #         extract_table_structure=True,
        #         extract_images=True
        #     ))
        #     .materialize(path="/tmp/materialize/partitioned", source_mode=MaterializeSourceMode.RECOMPUTE)
        #     .merge(merger=GreedySectionMerger(
        #         tokenizer=tokenizer, max_tokens=max_tokens, merge_across_pages=False
        #     ))
        #     .split_elements(tokenizer=tokenizer, max_tokens=max_tokens)
        # )

        # ds.execute()
        # print("Print 3")
        # # Embed the processed document
        # embedded_ds = (
        #     ds.spread_properties(["path", "entity"])
        #     .explode()
        #     .embed(embedder=SentenceTransformerEmbedder(model_name=model_name))
        # )

        # # Create Pinecone index spec
        # spec = ServerlessSpec(cloud="aws", region="us-east-1")
        # index_name = "sbhacks"

        # # Write embeddings to Pinecone
        # embedded_ds.write.pinecone(
        #     index_name=index_name,
        #     dimensions=dimensions,
        #     distance_metric="cosine",
        #     index_spec=spec
        # )
        # print("Print 4")
        # Load the same embedding model
        model_name = "all-MiniLM-L6-v2"
        embedder = SentenceTransformer(model_name)
        
        pinecone_context = pinecone_retrieval(user_prompt_text, ctx, embedder)
        if type_of_question=="mcq":
            questions = generate_mcq(pinecone_context, number_of_questions)
        elif type_of_question=="short":
            questions = generate_shortq(pinecone_context, number_of_questions)
        # if type_of_question=="mcq":
        #     questions = generate_mcq(user_prompt_text, number_of_questions)
        # elif type_of_question=="short":
        #     questions = generate_shortq(user_prompt_text, number_of_questions)
        
        return questions

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    

@app.route('/verify-short', methods=['POST'])
def verify():
    try:
        # Parse request data
        data = request.get_json()
        if not data or 'question' not in data or 'answer' not in data:
            return jsonify({"error": "Invalid input. 'question' and 'answer' are required."}), 400

        question = data['question']
        llm_answer = data['llm_answer']
        user_answer = data['answer']

        # Verify the answer using verifier.py
        result = verify_short_answer(question, user_answer, llm_answer)

        if not result:
            return jsonify({"error": "Verification failed."}), 500

        # Return the correct answer and explanation
        return jsonify({"correct_answer": result[0], "explanation": result[1]}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generate-handout', methods=['POST'])
def generate_handout_endpoint():
    try:
        # Call the generate_handout function
        data = request.get_json()
        ctx = data['context']
        handout_paragraph = generate_handout(ctx)

        # Return the generated handout paragraph
        return jsonify({"handout": handout_paragraph}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/upload-video', methods=['POST'])
def upload_video():
    try:
        data = request.get_json()
        youtube_url = data['youtube_url']
        download_and_upload_video(youtube_url=youtube_url)

        return 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/query-video', methods=['POST'])
def query_video():
    try:
        data = request.get_json()
        query = data['query']
        
        output_path, start_time = search_video(query)
        return jsonify({"output_path": output_path, "start_time": start_time}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False)
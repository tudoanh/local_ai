from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter
from llama_index.embeddings.llamafile import LlamafileEmbedding
from django.db import transaction
from django.conf import settings
from langchain_community.document_loaders import PyPDFLoader
from rag.models import Knowledge, KnowledgeEmbedding, UploadFile

embedding = LlamafileEmbedding(
    base_url=settings.EMBEDDING_SERVICE_URL,
)


def create_embedding(texts: List[str]):
    return embedding.get_text_embedding_batch(texts)


def get_query_embedding(text: str):
    return embedding.get_query_embedding(text)


def process_file(file_instance):
    """
    Processes the file and creates Knowledge instances.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len,
        separators=[
            "\n\n",
            "\n",
            " ",
            ".",
            ",",
            "\u200b",  # Zero-width space
            "\uff0c",  # Fullwidth comma
            "\u3001",  # Ideographic comma
            "\uff0e",  # Fullwidth full stop
            "\u3002",  # Ideographic full stop
            "",
        ],
    )
    if file_instance.file.name.endswith('.pdf'):
        loader = PyPDFLoader(file_instance.file.path)
        pages = []
        for page in loader.load():
            pages.append(page)
        texts = splitter.split_documents(pages)
    elif file_instance.file.name.endswith('.txt'):
        with file_instance.file.open() as f:
            content = f.read()
            texts = splitter.create_documents([content])

    embeddings = create_embedding([text.page_content for text in texts])


    for ct, em in zip(texts, embeddings):
        create_knowledge(file_instance, ct.page_content, {"file_name": file_instance.file.name}, em)
    file_instance.processed = True
    file_instance.save()


def create_knowledge(file_instance, content, metadata, embedding):
    """
    Creates a Knowledge instance along with its embedding.
    """
    if len(embedding) != settings.EMBEDDING_SIZE:
        raise ValueError("Embedding must be a list of 512 floats.")

    serialized_embedding = KnowledgeEmbedding.serialize_f32(embedding)
    print(content)

    with transaction.atomic():
        knowledge = Knowledge.objects.create(
            file=file_instance,
            content=content,
            metadata=metadata
        )
        KnowledgeEmbedding.objects.create(
            knowledge=knowledge,
            embedding=serialized_embedding
        )

    return knowledge


def update_embedding(knowledge, new_embedding):
    """
    Updates the embedding for an existing Knowledge instance.
    """
    if len(new_embedding) != settings.EMBEDDING_SIZE:
        raise ValueError("Embedding must be a list of 1024 floats.")

    serialized_embedding = KnowledgeEmbedding.serialize_f32(new_embedding)

    with transaction.atomic():
        embedding_instance, created = KnowledgeEmbedding.objects.get_or_create(
            knowledge=knowledge,
            defaults={'embedding': serialized_embedding}
        )
        if not created:
            embedding_instance.embedding = serialized_embedding
            embedding_instance.save()


def search_similar_knowledge(query_embedding, file_ids=[], limit=3):
    """
    Searches for similar Knowledge entries based on the query_embedding.
    """
    if file_ids:
        return KnowledgeEmbedding.search_similar(query_embedding, file_ids, limit=limit)
    return KnowledgeEmbedding.search_similar(query_embedding, limit=limit)

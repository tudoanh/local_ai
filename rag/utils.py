import json
from rag.models import Knowledge, KnowledgeEmbedding, UploadFile
from django.db import transaction


def create_knowledge(file_instance, content, metadata, embedding):
    """
    Creates a Knowledge instance along with its embedding.
    """
    if len(embedding) != 512:
        raise ValueError("Embedding must be a list of 512 floats.")

    serialized_embedding = KnowledgeEmbedding.serialize_f32(embedding)

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
    if len(new_embedding) != 512:
        raise ValueError("Embedding must be a list of 512 floats.")

    serialized_embedding = KnowledgeEmbedding.serialize_f32(new_embedding)

    with transaction.atomic():
        embedding_instance, created = KnowledgeEmbedding.objects.get_or_create(
            knowledge=knowledge,
            defaults={'embedding': serialized_embedding}
        )
        if not created:
            embedding_instance.embedding = serialized_embedding
            embedding_instance.save()


def search_similar_knowledge(query_embedding, limit=3):
    """
    Searches for similar Knowledge entries based on the query_embedding.
    """
    return KnowledgeEmbedding.search_similar(query_embedding, limit=limit)

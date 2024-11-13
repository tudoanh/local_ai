import struct
from typing import List
from django.db import models
from django_extensions.db.models import TimeStampedModel
from django.core.exceptions import ValidationError
import json


def serialize_f32(vector: List[float]) -> bytes:
    """Serializes a list of floats into a compact 'raw bytes' format"""
    return struct.pack(f"{len(vector)}f", *vector)


def deserialize_f32(binary_data: bytes) -> List[float]:
    """Deserializes bytes back into a list of floats"""
    return list(struct.unpack(f"{len(binary_data)//4}f", binary_data))


class UploadFile(TimeStampedModel):
    file = models.FileField(upload_to="uploads/")
    processed = models.BooleanField(default=False)

    def __str__(self):
        return f"UploadFile {self.id} - {self.file.name}"


class Knowledge(TimeStampedModel):
    file = models.ForeignKey(UploadFile, on_delete=models.CASCADE)
    content = models.TextField()
    metadata = models.JSONField()

    class Meta:
        db_table = "knowledge"
        managed = True  # Let Django manage this table

    def __str__(self):
        return f"Knowledge {self.id} - {self.content[:50]}"


class KnowledgeEmbedding(models.Model):
    """
    This model represents the embeddings and links to Knowledge via rowid.
    It uses a OneToOneField to ensure a direct association.
    """

    knowledge = models.OneToOneField(
        Knowledge, on_delete=models.CASCADE, primary_key=True
    )
    embedding = models.BinaryField()

    class Meta:
        db_table = "vec_knowledge"
        managed = False  # Managed externally via virtual table

    @classmethod
    def serialize_f32(cls, vector: List[float]) -> bytes:
        if len(vector) != 512:
            raise ValueError("Embedding must be a list of 512 floats.")
        return serialize_f32(vector)

    @classmethod
    def deserialize_f32(cls, binary_data: bytes) -> List[float]:
        return deserialize_f32(binary_data)

    @classmethod
    def search_similar(cls, query_embedding: List[float], limit: int = 3):
        """Search for similar knowledge entries using vector similarity"""
        from django.db import connection

        serialized_embedding = cls.serialize_f32(query_embedding)

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    vec_knowledge.rowid,
                    knowledge.id,
                    knowledge.file_id,
                    knowledge.content,
                    knowledge.metadata,
                    vec_cosine_similarity(vec_knowledge.embedding, ?) AS similarity
                FROM vec_knowledge
                JOIN knowledge ON knowledge.id = vec_knowledge.rowid
                ORDER BY similarity DESC
                LIMIT ?
                """,
                [serialized_embedding, limit],
            )

            return [
                {
                    "rowid": row[0],
                    "knowledge_id": row[1],
                    "file_id": row[2],
                    "content": row[3],
                    "metadata": row[4],
                    "similarity": row[5],
                }
                for row in cursor.fetchall()
            ]

    def save_with_embedding(self, embedding: List[float], *args, **kwargs):
        """Save the embedding alongside the Knowledge instance"""
        if len(embedding) != 512:
            raise ValueError("Embedding must be a list of 512 floats.")
        self.embedding = self.serialize_f32(embedding)
        # No need to call super().save() here since it's managed by the virtual table

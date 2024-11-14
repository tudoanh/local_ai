import os
import struct
from typing import List
from django.db import models
from django.conf import settings
from django_extensions.db.models import TimeStampedModel


def serialize_f32(vector: List[float]) -> bytes:
    """Serializes a list of floats into a compact 'raw bytes' format"""
    return struct.pack(f"{len(vector)}f", *vector)


def deserialize_f32(binary_data: bytes) -> List[float]:
    """Deserializes bytes back into a list of floats"""
    return list(struct.unpack(f"{len(binary_data)//4}f", binary_data))


class UploadFile(TimeStampedModel):
    file = models.FileField(upload_to="uploads/")
    processed = models.BooleanField(default=False)

    def filename(self):
        return os.path.basename(self.file.name)

    def __str__(self):
        return f"UploadFile {self.id} - {self.file.name}"


class Knowledge(TimeStampedModel):
    file = models.ForeignKey(UploadFile, on_delete=models.CASCADE, null=True)
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
        Knowledge, on_delete=models.CASCADE, primary_key=True,
        db_column='rowid', related_name='embedding'
    )
    embedding = models.BinaryField()

    class Meta:
        db_table = "vec_knowledge"
        managed = False  # Managed externally via virtual table

    @classmethod
    def serialize_f32(cls, vector: List[float]) -> bytes:
        if len(vector) != settings.EMBEDDING_SIZE:
            raise ValueError(f"Embedding must be a list of {settings.EMBEDDING_SIZE} floats.")
        return serialize_f32(vector)

    @classmethod
    def deserialize_f32(cls, binary_data: bytes) -> List[float]:
        return deserialize_f32(binary_data)

    @classmethod
    def search_similar(cls, query_embedding: List[float], file_ids: List[int] = None, limit: int = 3):
        from django.db import connection
        from string import Template

        # Serialize the embedding
        serialized_embedding = cls.serialize_f32(query_embedding)
        
        # Initialize parameters dictionary
        params = {
            'embedding': serialized_embedding,
            'limit': limit
        }

        # Build file_id placeholders and update params
        file_filter = ""
        if file_ids:
            placeholders = ', '.join([f":file_id_{i}" for i in range(len(file_ids))])
            file_filter = f"AND knowledge.file_id IN ({placeholders})"
            for i, file_id in enumerate(file_ids):
                params[f'file_id_{i}'] = file_id

        # Construct the SQL query with named placeholders
        sql = f"""
            SELECT
                vec_knowledge.rowid,
                knowledge.id,
                knowledge.file_id,
                knowledge.content,
                knowledge.metadata,
                vec_distance_L2(vec_knowledge.embedding, :embedding) AS similarity
            FROM vec_knowledge
            JOIN knowledge ON knowledge.id = vec_knowledge.rowid
            WHERE 1=1 {file_filter}
            ORDER BY similarity ASC
            LIMIT :limit
        """
        print("SQL Query:", sql)
        print("Parameters:", params)

        with connection.cursor() as cursor:
            cursor.execute(sql, params)

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
        if len(embedding) != settings.EMBEDDING_SIZE:
            raise ValueError(f"Embedding must be a list of {settings.EMBEDDING_SIZE} floats.")
        self.embedding = self.serialize_f32(embedding)
        # No need to call super().save() here since it's managed by the virtual table

from django.db.models.signals import pre_delete
from django.dispatch import receiver
from rag.models import UploadFile, Knowledge

# Add this after your model definitions:

@receiver(pre_delete, sender=UploadFile)
def cleanup_file_relations(sender, instance, **kwargs):
    """Ensure all related Knowledge and KnowledgeEmbedding records are deleted when a File is deleted"""
    # Get related Knowledge records
    knowledge_records = Knowledge.objects.filter(file=instance)
    
    # Delete related Knowledge records (this will cascade to KnowledgeEmbedding due to OneToOneField)
    knowledge_records.delete()

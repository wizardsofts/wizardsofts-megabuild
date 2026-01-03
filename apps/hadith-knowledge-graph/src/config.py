"""
Configuration Management for Hadith Knowledge Graph
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment"""

    # Neo4j Configuration
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "hadithknowledge2025"

    # ChromaDB Configuration
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    chroma_collection_name: str = "hadith_embeddings"

    # Ollama Configuration
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b-instruct-q4_K_M"
    ollama_embedding_model: str = "nomic-embed-text"

    # OpenAI Configuration
    openai_api_key: str = ""
    openai_model: str = "gpt-4"
    openai_embedding_model: str = "text-embedding-3-large"

    # PostgreSQL Configuration
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = ""
    postgres_password: str = ""
    postgres_db: str = "dailydeenguide"

    # Redis Configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = "hadithredis2025"
    redis_url: str = "redis://:hadithredis2025@localhost:6379/0"

    # Ray Configuration
    ray_address: str = "auto"
    ray_namespace: str = "hadith-extraction"

    # Celery Configuration
    celery_broker_url: str = "redis://:hadithredis2025@localhost:6379/0"
    celery_result_backend: str = "redis://:hadithredis2025@localhost:6379/0"

    # Application Configuration
    log_level: str = "INFO"
    confidence_threshold: float = 0.8
    batch_size: int = 10
    max_workers: int = 4

    # Extraction Configuration
    enable_entity_extraction: bool = True
    enable_relationship_extraction: bool = True
    enable_topic_classification: bool = True
    enable_isnad_parsing: bool = True

    # RAG Configuration
    rag_top_k: int = 5
    rag_similarity_threshold: float = 0.7
    rag_use_reranker: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    @property
    def postgres_url(self) -> str:
        """Build PostgreSQL connection URL"""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def chroma_url(self) -> str:
        """Build ChromaDB URL"""
        return f"http://{self.chroma_host}:{self.chroma_port}"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

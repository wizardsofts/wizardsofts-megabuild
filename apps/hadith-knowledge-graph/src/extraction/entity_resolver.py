"""
Entity resolution and deduplication using fuzzy matching
"""

from uuid import UUID, uuid4
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from loguru import logger

from src.models.entities import PersonEntity, PlaceEntity, EventEntity, TopicEntity
from src.utils.text_processing import (
    normalize_name,
    get_phonetic_key,
    calculate_similarity,
    fuzzy_match
)
from src.config import get_settings

settings = get_settings()


class EntityResolver:
    """Resolve and deduplicate entities using fuzzy matching"""

    def __init__(self, db_session: Session, confidence_threshold: float = None):
        self.db = db_session
        self.threshold = confidence_threshold or settings.confidence_threshold

    def resolve_person(self, extracted: Dict[str, Any]) -> UUID:
        """
        Resolve person entity to existing or create new.

        Args:
            extracted: Extracted person data from LLM

        Returns:
            UUID of matched or newly created entity
        """
        canonical_name = extracted.get("canonical_name_en", "")
        if not canonical_name:
            logger.warning("Person entity missing canonical_name_en")
            return self._create_person(extracted)

        # Generate keys for matching
        norm_key = normalize_name(canonical_name)
        phonetic_key = get_phonetic_key(canonical_name)

        # 1. Try exact normalization match
        existing = self.db.query(PersonEntity).filter(
            PersonEntity.normalization_key == norm_key
        ).first()

        if existing:
            logger.info(f"Exact match found: {existing.canonical_name_en} (ID: {existing.id})")
            # Add new variant if not already present
            self._add_variant(existing, canonical_name)
            return existing.id

        # 2. Try phonetic + similarity match
        if phonetic_key:
            candidates = self.db.query(PersonEntity).filter(
                PersonEntity.phonetic_key == phonetic_key
            ).all()

            for candidate in candidates:
                similarity = calculate_similarity(canonical_name, candidate.canonical_name_en)
                if similarity >= self.threshold * 0.95:  # 95% of threshold for phonetic
                    logger.info(
                        f"Phonetic match found: {candidate.canonical_name_en} "
                        f"(similarity: {similarity:.2f}, ID: {candidate.id})"
                    )
                    self._add_variant(candidate, canonical_name)
                    return candidate.id

        # 3. Try fuzzy string match
        all_people = self.db.query(PersonEntity).limit(1000).all()  # Limit for performance
        existing_names = [p.canonical_name_en for p in all_people]

        matches = fuzzy_match(canonical_name, existing_names, threshold=self.threshold)

        if matches:
            # Get best match
            best_match_name, similarity = matches[0]
            matched_entity = next(p for p in all_people if p.canonical_name_en == best_match_name)

            logger.info(
                f"Fuzzy match found: {matched_entity.canonical_name_en} "
                f"(similarity: {similarity:.2f}, ID: {matched_entity.id})"
            )
            self._add_variant(matched_entity, canonical_name)
            return matched_entity.id

        # 4. No match found - create new entity
        logger.info(f"No match found for '{canonical_name}', creating new entity")
        return self._create_person(extracted)

    def _create_person(self, extracted: Dict[str, Any]) -> UUID:
        """Create new person entity."""
        canonical_name = extracted.get("canonical_name_en", "Unknown")
        variants = extracted.get("variants", [])

        # Ensure canonical name is in variants
        if canonical_name not in variants:
            variants.insert(0, canonical_name)

        entity = PersonEntity(
            canonical_name_en=canonical_name,
            canonical_name_ar=extracted.get("canonical_name_ar"),
            normalization_key=normalize_name(canonical_name),
            phonetic_key=get_phonetic_key(canonical_name),
            name_variants=variants,
            person_type=extracted.get("person_type"),
            reliability_grade=extracted.get("reliability_grade"),
            attributes={
                "context": extracted.get("context"),
                "text_span": extracted.get("text_span")
            },
            confidence_score=extracted.get("confidence", 0.8)
        )

        self.db.add(entity)
        self.db.flush()  # Get ID without committing

        logger.info(f"Created new person: {canonical_name} (ID: {entity.id})")
        return entity.id

    def _add_variant(self, entity: PersonEntity, new_variant: str):
        """Add new name variant to existing entity if not present."""
        if new_variant not in entity.name_variants:
            entity.name_variants.append(new_variant)
            self.db.flush()
            logger.debug(f"Added variant '{new_variant}' to {entity.canonical_name_en}")

    def resolve_place(self, extracted: Dict[str, Any]) -> UUID:
        """Resolve place entity to existing or create new."""
        canonical_name = extracted.get("canonical_name_en", "")
        if not canonical_name:
            return self._create_place(extracted)

        norm_key = normalize_name(canonical_name)

        # Try exact match
        existing = self.db.query(PlaceEntity).filter(
            PlaceEntity.normalization_key == norm_key
        ).first()

        if existing:
            logger.info(f"Place match found: {existing.canonical_name_en}")
            return existing.id

        # Try fuzzy match
        all_places = self.db.query(PlaceEntity).limit(500).all()
        existing_names = [p.canonical_name_en for p in all_places]
        matches = fuzzy_match(canonical_name, existing_names, threshold=self.threshold)

        if matches:
            best_match_name, _ = matches[0]
            matched = next(p for p in all_places if p.canonical_name_en == best_match_name)
            return matched.id

        return self._create_place(extracted)

    def _create_place(self, extracted: Dict[str, Any]) -> UUID:
        """Create new place entity."""
        canonical_name = extracted.get("canonical_name_en", "Unknown")

        entity = PlaceEntity(
            canonical_name_en=canonical_name,
            canonical_name_ar=extracted.get("canonical_name_ar"),
            normalization_key=normalize_name(canonical_name),
            name_variants=extracted.get("variants", [canonical_name]),
            place_type=extracted.get("place_type"),
            attributes={"context": extracted.get("context")},
            confidence_score=extracted.get("confidence", 0.8),
            data_sources=["llm_extraction"]
        )

        self.db.add(entity)
        self.db.flush()

        logger.info(f"Created new place: {canonical_name} (ID: {entity.id})")
        return entity.id

    def resolve_event(self, extracted: Dict[str, Any]) -> UUID:
        """Resolve event entity to existing or create new."""
        canonical_name = extracted.get("canonical_name_en", "")
        if not canonical_name:
            return self._create_event(extracted)

        norm_key = normalize_name(canonical_name)

        existing = self.db.query(EventEntity).filter(
            EventEntity.normalization_key == norm_key
        ).first()

        if existing:
            return existing.id

        return self._create_event(extracted)

    def _create_event(self, extracted: Dict[str, Any]) -> UUID:
        """Create new event entity."""
        canonical_name = extracted.get("canonical_name_en", "Unknown")

        # Handle empty strings for integer fields
        date_hijri_year = extracted.get("date_hijri_year")
        if date_hijri_year == "" or date_hijri_year is None:
            date_hijri_year = None
        elif isinstance(date_hijri_year, str):
            try:
                date_hijri_year = int(date_hijri_year)
            except ValueError:
                date_hijri_year = None

        entity = EventEntity(
            canonical_name_en=canonical_name,
            canonical_name_ar=extracted.get("canonical_name_ar"),
            normalization_key=normalize_name(canonical_name),
            name_variants=extracted.get("variants", [canonical_name]),
            event_type=extracted.get("event_type") or None,
            date_hijri_year=date_hijri_year,
            attributes={"context": extracted.get("context")},
            confidence_score=extracted.get("confidence", 0.8)
        )

        self.db.add(entity)
        self.db.flush()

        logger.info(f"Created new event: {canonical_name} (ID: {entity.id})")
        return entity.id

    def resolve_topic(self, extracted: Dict[str, Any]) -> UUID:
        """Resolve topic entity to existing or create new."""
        canonical_name = extracted.get("canonical_name_en", "")
        if not canonical_name:
            return self._create_topic(extracted)

        norm_key = normalize_name(canonical_name)

        existing = self.db.query(TopicEntity).filter(
            TopicEntity.normalization_key == norm_key
        ).first()

        if existing:
            return existing.id

        return self._create_topic(extracted)

    def _create_topic(self, extracted: Dict[str, Any]) -> UUID:
        """Create new topic entity."""
        canonical_name = extracted.get("canonical_name_en", "Unknown")

        entity = TopicEntity(
            canonical_name_en=canonical_name,
            canonical_name_ar=extracted.get("canonical_name_ar"),
            normalization_key=normalize_name(canonical_name),
            name_variants=extracted.get("variants", [canonical_name]),
            topic_type=extracted.get("topic_type"),
            category=extracted.get("category"),
            attributes={"context": extracted.get("context")},
            confidence_score=extracted.get("confidence", 0.8),
            data_sources=["llm_extraction"]
        )

        self.db.add(entity)
        self.db.flush()

        logger.info(f"Created new topic: {canonical_name} (ID: {entity.id})")
        return entity.id

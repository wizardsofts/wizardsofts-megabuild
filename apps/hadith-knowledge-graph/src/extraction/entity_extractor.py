"""
Entity extraction using Ollama with JSON mode for structured output
"""

import json
import httpx
from typing import List, Dict, Any
from loguru import logger

from src.models.schemas import ExtractedPerson, ExtractedPlace, ExtractedEvent, ExtractedTopic
from src.config import get_settings

settings = get_settings()


class EntityExtractor:
    """Extract entities from Hadith text using Ollama LLM with JSON mode"""

    def __init__(self, model: str = None):
        self.model = model or settings.ollama_model
        self.base_url = settings.ollama_base_url

    def _call_ollama(self, prompt: str, system: str = None) -> Dict[str, Any]:
        """
        Call Ollama API with JSON format mode.

        Args:
            prompt: User prompt
            system: System prompt

        Returns:
            Parsed JSON response

        Raises:
            Exception if API call fails
        """
        try:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "system": system,
                    "format": "json",  # Force JSON output
                    "stream": False,
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistency
                        "top_p": 0.9
                    }
                },
                timeout=60.0
            )
            response.raise_for_status()

            data = response.json()
            response_text = data.get("response", "{}")

            # Parse JSON response
            try:
                return json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {response_text}")
                raise ValueError(f"Invalid JSON from LLM: {e}")

        except Exception as e:
            logger.error(f"Ollama API call failed: {e}")
            raise

    def extract_people(self, hadith_text: str) -> List[Dict[str, Any]]:
        """
        Extract person entities from Hadith text.

        Args:
            hadith_text: Hadith text in English

        Returns:
            List of extracted person entities
        """
        system = """You are an expert in Islamic hadith analysis. Extract all person entities mentioned in the hadith text.

For each person, identify:
- canonical_name_en: Full name in English
- variants: Alternative spellings
- person_type: prophet, companion, narrator, scholar, etc.
- reliability_grade: If mentioned (trustworthy, weak, etc.)
- context: How they appear in the text

Return ONLY valid JSON array of objects. No explanation."""

        prompt = f"""Extract all person entities from this hadith:

"{hadith_text}"

Return JSON array:
[
  {{
    "canonical_name_en": "Abu Hurairah",
    "variants": ["Abu Hurayrah", "Abi Huraira"],
    "person_type": "narrator",
    "reliability_grade": "trustworthy",
    "context": "primary narrator",
    "text_span": "Abu Hurairah narrated"
  }}
]"""

        try:
            result = self._call_ollama(prompt, system)

            # Handle various response formats
            if isinstance(result, list):
                return result
            elif isinstance(result, dict):
                # Check for wrapped arrays
                if "people" in result:
                    return result["people"]
                elif "entities" in result:
                    return result["entities"]
                elif "result" in result and isinstance(result["result"], list):
                    return result["result"]
                elif "results" in result and isinstance(result["results"], list):
                    return result["results"]
                elif "data" in result and isinstance(result["data"], list):
                    return result["data"]
                elif "canonical_name_en" in result:
                    # Single person object returned instead of array
                    logger.debug(f"Wrapped single person object in array")
                    return [result]
                else:
                    logger.warning(f"Unexpected response format: {result}")
                    return []
            else:
                logger.warning(f"Unexpected response type: {type(result)}")
                return []

        except Exception as e:
            logger.error(f"Failed to extract people: {e}")
            return []

    def extract_places(self, hadith_text: str) -> List[Dict[str, Any]]:
        """Extract place entities from Hadith text."""

        system = """Extract all place entities (cities, regions, mosques, battlefields, etc.) from the hadith text.

Return ONLY valid JSON array. No explanation."""

        prompt = f"""Extract all place entities from this hadith:

"{hadith_text}"

Return JSON array:
[
  {{
    "canonical_name_en": "Medina",
    "variants": ["Al-Madinah", "Madinah", "Yathrib"],
    "place_type": "city",
    "context": "location of event",
    "text_span": "in Medina"
  }}
]"""

        try:
            result = self._call_ollama(prompt, system)

            if isinstance(result, list):
                return result
            elif isinstance(result, dict):
                if "places" in result:
                    return result["places"]
                elif "result" in result and isinstance(result["result"], list):
                    return result["result"]
                elif "results" in result and isinstance(result["results"], list):
                    return result["results"]
                elif "data" in result and isinstance(result["data"], list):
                    return result["data"]
                elif "canonical_name_en" in result:
                    return [result]
                else:
                    return []
            else:
                return []

        except Exception as e:
            logger.error(f"Failed to extract places: {e}")
            return []

    def extract_events(self, hadith_text: str) -> List[Dict[str, Any]]:
        """Extract event entities from Hadith text."""

        system = """Extract all historical events (battles, migrations, treaties, revelations, etc.) from the hadith text.

Return ONLY valid JSON array. No explanation."""

        prompt = f"""Extract all event entities from this hadith:

"{hadith_text}"

Return JSON array:
[
  {{
    "canonical_name_en": "Battle of Badr",
    "variants": ["Badr", "Ghazwat Badr"],
    "event_type": "battle",
    "date_hijri_year": 2,
    "context": "mentioned event",
    "text_span": "during the Battle of Badr"
  }}
]"""

        try:
            result = self._call_ollama(prompt, system)

            if isinstance(result, list):
                return result
            elif isinstance(result, dict):
                if "events" in result:
                    return result["events"]
                elif "result" in result and isinstance(result["result"], list):
                    return result["result"]
                elif "results" in result and isinstance(result["results"], list):
                    return result["results"]
                elif "data" in result and isinstance(result["data"], list):
                    return result["data"]
                elif "canonical_name_en" in result:
                    return [result]
                else:
                    return []
            else:
                return []

        except Exception as e:
            logger.error(f"Failed to extract events: {e}")
            return []

    def extract_topics(self, hadith_text: str) -> List[Dict[str, Any]]:
        """Extract topic/concept entities from Hadith text."""

        system = """Extract main topics and concepts from the hadith text.

Topics include: prayer (Salah), fasting (Sawm), charity (Zakat), pilgrimage (Hajj), faith (Iman), purification, marriage, business, etc.

Return ONLY valid JSON array. No explanation."""

        prompt = f"""Extract all topic entities from this hadith:

"{hadith_text}"

Return JSON array:
[
  {{
    "canonical_name_en": "Prayer Times",
    "variants": ["Salah Times", "Times of Prayer"],
    "category": "Salah",
    "topic_type": "legal",
    "context": "main subject",
    "confidence": 0.95
  }}
]"""

        try:
            result = self._call_ollama(prompt, system)

            if isinstance(result, list):
                return result
            elif isinstance(result, dict):
                if "topics" in result:
                    return result["topics"]
                elif "result" in result and isinstance(result["result"], list):
                    return result["result"]
                elif "results" in result and isinstance(result["results"], list):
                    return result["results"]
                elif "data" in result and isinstance(result["data"], list):
                    return result["data"]
                elif "canonical_name_en" in result:
                    return [result]
                else:
                    logger.debug(f"No topics extracted from response: {result}")
                    return []
            else:
                return []

        except Exception as e:
            logger.error(f"Failed to extract topics: {e}")
            return []

    def extract_all(self, hadith_text: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extract all entity types from Hadith text.

        Args:
            hadith_text: Hadith text in English

        Returns:
            Dictionary with extracted entities by type
        """
        logger.info(f"Extracting entities from text (length: {len(hadith_text)})")

        return {
            "people": self.extract_people(hadith_text),
            "places": self.extract_places(hadith_text),
            "events": self.extract_events(hadith_text),
            "topics": self.extract_topics(hadith_text)
        }

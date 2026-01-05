"""
Text processing utilities for entity name normalization and matching
"""

import re
from typing import List
from unidecode import unidecode
from phonetics import metaphone
from Levenshtein import ratio as levenshtein_ratio
from loguru import logger


# Common Arabic prefixes to remove during normalization
ARABIC_PREFIXES = ['al-', 'ibn', 'bin', 'bint', 'abu', 'abi', 'umm']


def normalize_name(name: str) -> str:
    """
    Normalize name for deduplication matching.

    Steps:
    1. Convert to lowercase
    2. Remove diacritics/accents
    3. Remove common prefixes (al-, ibn, bin, etc.)
    4. Remove all non-alphanumeric characters
    5. Strip whitespace

    Args:
        name: Original name

    Returns:
        Normalized name for matching

    Examples:
        >>> normalize_name("Abu Hurairah")
        'hurairah'
        >>> normalize_name("Al-Bukhārī")
        'bukhari'
        >>> normalize_name("Ibn Mas'ud")
        'masud'
    """
    if not name:
        return ""

    # Convert to lowercase
    normalized = name.lower()

    # Remove diacritics
    normalized = unidecode(normalized)

    # Remove common prefixes
    for prefix in ARABIC_PREFIXES:
        # Remove from beginning
        if normalized.startswith(prefix + ' '):
            normalized = normalized[len(prefix) + 1:]
        elif normalized.startswith(prefix):
            normalized = normalized[len(prefix):]

    # Remove all non-alphanumeric characters
    normalized = re.sub(r'[^a-z0-9]', '', normalized)

    return normalized.strip()


def get_phonetic_key(name: str) -> str:
    """
    Get phonetic key for fuzzy matching across transliterations.

    Uses Metaphone algorithm which groups similar-sounding names.

    Args:
        name: Name to encode

    Returns:
        Phonetic key (uppercase)

    Examples:
        >>> get_phonetic_key("Abu Hurairah")
        'ABHRR'
        >>> get_phonetic_key("Abu Hurayrah")
        'ABHRR'  # Same phonetic key!
    """
    if not name:
        return ""

    # Normalize first
    normalized = normalize_name(name)

    if not normalized:
        return ""

    # Get metaphone encoding
    try:
        phonetic = metaphone(normalized)
        return phonetic.upper() if phonetic else ""
    except Exception as e:
        logger.warning(f"Phonetic encoding failed for '{name}': {e}")
        return ""


def calculate_similarity(s1: str, s2: str) -> float:
    """
    Calculate similarity between two strings using Levenshtein ratio.

    Args:
        s1: First string
        s2: Second string

    Returns:
        Similarity score between 0.0 (completely different) and 1.0 (identical)

    Examples:
        >>> calculate_similarity("Abu Hurairah", "Abu Hurayrah")
        0.92
        >>> calculate_similarity("Malik", "Maalik")
        0.83
    """
    if not s1 or not s2:
        return 0.0

    # Normalize both strings
    norm1 = normalize_name(s1)
    norm2 = normalize_name(s2)

    if not norm1 or not norm2:
        return 0.0

    # Calculate Levenshtein ratio
    return levenshtein_ratio(norm1, norm2)


def fuzzy_match(
    candidate: str,
    existing_names: List[str],
    threshold: float = 0.85
) -> List[tuple[str, float]]:
    """
    Find fuzzy matches for a candidate name against existing names.

    Args:
        candidate: Name to match
        existing_names: List of existing names to compare against
        threshold: Minimum similarity score (0.0-1.0)

    Returns:
        List of (name, similarity_score) tuples sorted by score (descending)

    Examples:
        >>> existing = ["Abu Hurairah", "Malik ibn Anas", "Aisha"]
        >>> fuzzy_match("Abu Hurayrah", existing, threshold=0.80)
        [("Abu Hurairah", 0.92)]
    """
    matches = []

    candidate_norm = normalize_name(candidate)
    candidate_phonetic = get_phonetic_key(candidate)

    for existing in existing_names:
        existing_norm = normalize_name(existing)

        # Exact normalization match
        if candidate_norm == existing_norm:
            matches.append((existing, 1.0))
            continue

        # Phonetic match
        existing_phonetic = get_phonetic_key(existing)
        if candidate_phonetic and candidate_phonetic == existing_phonetic:
            # Phonetic match gets high score but not perfect
            similarity = calculate_similarity(candidate, existing)
            if similarity >= threshold * 0.95:  # Slightly lower threshold for phonetic
                matches.append((existing, similarity))
            continue

        # String similarity match
        similarity = calculate_similarity(candidate, existing)
        if similarity >= threshold:
            matches.append((existing, similarity))

    # Sort by similarity (descending)
    matches.sort(key=lambda x: x[1], reverse=True)

    return matches


def extract_generation(text: str) -> int | None:
    """
    Extract narrator generation from context.

    Generations:
    - Sahaba (companions) = 1
    - Tabi'un (followers) = 2
    - Tabi' al-Tabi'in = 3
    - Later generations = 4+

    Args:
        text: Text containing generation info

    Returns:
        Generation number or None

    Examples:
        >>> extract_generation("He was a Sahabi companion")
        1
        >>> extract_generation("Among the Tabi'un scholars")
        2
    """
    text_lower = text.lower()

    if any(term in text_lower for term in ['sahaba', 'sahabi', 'companion', 'صحابي']):
        return 1
    elif any(term in text_lower for term in ["tabi'un", 'tabi', 'follower', 'تابعي']):
        return 2
    elif "tabi' al-tabi'in" in text_lower:
        return 3

    return None


def clean_arabic_text(text: str) -> str:
    """
    Clean Arabic text by removing diacritics and normalizing.

    Args:
        text: Arabic text

    Returns:
        Cleaned text

    Examples:
        >>> clean_arabic_text("قَالَ النَّبِيُّ")
        'قال النبي'
    """
    if not text:
        return ""

    # Remove Arabic diacritics (Tashkeel)
    diacritics = re.compile(r'[\u0617-\u061A\u064B-\u0652]')
    text = diacritics.sub('', text)

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def extract_person_role(text: str) -> str | None:
    """
    Extract person's role from context.

    Args:
        text: Text containing role information

    Returns:
        Role string or None

    Examples:
        >>> extract_person_role("Bukhari narrated from Malik")
        'narrator'
        >>> extract_person_role("The Prophet said")
        'prophet'
    """
    text_lower = text.lower()

    if any(term in text_lower for term in ['prophet', 'messenger', 'rasul', 'نبي']):
        return 'prophet'
    elif any(term in text_lower for term in ['narrat', 'report', 'transmit', 'روى']):
        return 'narrator'
    elif any(term in text_lower for term in ['scholar', 'imam', 'sheikh', 'عالم']):
        return 'scholar'
    elif any(term in text_lower for term in ['companion', 'sahabi', 'صحابي']):
        return 'companion'

    return None

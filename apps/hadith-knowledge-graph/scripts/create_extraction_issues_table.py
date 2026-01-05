#!/usr/bin/env python3
"""Create extraction_issues table"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.entities import Base, ExtractionIssue
from src.utils.database import engine

def main():
    """Create extraction_issues table"""
    
    # Create only the extraction_issues table
    ExtractionIssue.__table__.create(engine, checkfirst=True)
    
    print("✅ extraction_issues table created successfully")

if __name__ == "__main__":
    main()

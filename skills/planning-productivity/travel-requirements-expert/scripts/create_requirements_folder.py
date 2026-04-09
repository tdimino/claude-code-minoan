#!/usr/bin/env python3
"""
Create timestamped requirements folder structure for travel itinerary planning.
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path


def slugify(text):
    """Convert text to URL-friendly slug."""
    # Simple slugify - lowercase, replace spaces with hyphens, remove special chars
    slug = text.lower()
    slug = ''.join(c if c.isalnum() or c.isspace() else '' for c in slug)
    slug = '-'.join(slug.split())
    return slug[:50]  # Limit length


def create_requirements_folder(user_request, base_path="requirements"):
    """
    Create requirements folder structure with timestamped name.

    Args:
        user_request: The user's trip request (for creating slug)
        base_path: Base directory for requirements folders

    Returns:
        Path to created folder
    """
    # Create timestamp and slug
    timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")
    slug = slugify(user_request)

    folder_name = f"{timestamp}-{slug}"
    folder_path = Path(base_path) / folder_name

    # Create folder structure
    folder_path.mkdir(parents=True, exist_ok=True)

    # Create initial files

    # 00-initial-request.md
    initial_request = f"""# Initial Request

**Date**: {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Request**: {user_request}

## Key Elements to Identify

- Logistical constraints (dates, accommodations, budget)
- Previous experience and capabilities
- Specific destination requests
- Cultural/spiritual/activity intentions
- Dietary restrictions or preferences
- Physical capability and comfort levels

## Questions to Explore

(To be filled during discovery phase)
"""
    (folder_path / "00-initial-request.md").write_text(initial_request)

    # metadata.json
    metadata = {
        "id": slug,
        "started": datetime.now().isoformat(),
        "lastUpdated": datetime.now().isoformat(),
        "status": "active",
        "phase": "discovery",
        "progress": {
            "discovery": {
                "answered": 0,
                "total": 5
            },
            "detail": {
                "answered": 0,
                "total": 0
            }
        },
        "contextFiles": [],
        "relatedTopics": []
    }
    (folder_path / "metadata.json").write_text(json.dumps(metadata, indent=2))

    # .current-requirement file in base path
    current_file = Path(base_path) / ".current-requirement"
    current_file.write_text(folder_name)

    print(f"✅ Created requirements folder: {folder_path}")
    print(f"✅ Folder name: {folder_name}")

    return str(folder_path)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python create_requirements_folder.py '<user request>' [base_path]")
        print("Example: python create_requirements_folder.py 'Planning trip to Japan for cherry blossoms'")
        sys.exit(1)

    user_request = sys.argv[1]
    base_path = sys.argv[2] if len(sys.argv) > 2 else "requirements"

    folder_path = create_requirements_folder(user_request, base_path)
    print(f"\nNext steps:")
    print(f"1. Begin Phase 2: Discovery questions (5 yes/no questions with smart defaults)")
    print(f"2. Use MCP servers for context research")
    print(f"3. Move through detail questions and final specification")

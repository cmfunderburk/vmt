#!/usr/bin/env python3
"""Test script to verify sprite loading and display."""

from pathlib import Path
import pygame

def test_sprite_loading():
    """Test that sprites can be loaded from the expected location."""
    # Get project root
    current_file = Path(__file__)
    project_root = current_file.parent.parent  # scripts/ -> root/
    sprites_dir = project_root / "vmt_sprites_pack_1"
    
    print(f"Looking for sprites in: {sprites_dir}")
    print(f"Sprites directory exists: {sprites_dir.exists()}")
    
    if not sprites_dir.exists():
        print("ERROR: Sprites directory not found!")
        return False
    
    # Initialize pygame to test loading
    pygame.init()
    
    sprites_to_test = [
        ("agent_blue_64.png", "Agent sprite"),
        ("resource_food_64.png", "Food resource sprite (good1/A)"),
        ("resource_stone_64.png", "Stone resource sprite (good2/B)"),
    ]
    
    all_loaded = True
    for filename, description in sprites_to_test:
        sprite_path = sprites_dir / filename
        print(f"\nTesting {description}:")
        print(f"  Path: {sprite_path}")
        print(f"  Exists: {sprite_path.exists()}")
        
        if sprite_path.exists():
            try:
                sprite = pygame.image.load(str(sprite_path))
                print(f"  Loaded successfully: {sprite.get_size()}")
            except Exception as e:
                print(f"  ERROR loading: {e}")
                all_loaded = False
        else:
            print(f"  ERROR: File not found!")
            all_loaded = False
    
    pygame.quit()
    return all_loaded

if __name__ == "__main__":
    success = test_sprite_loading()
    if success:
        print("\n✅ All sprites loaded successfully!")
    else:
        print("\n❌ Some sprites failed to load!")
        exit(1)
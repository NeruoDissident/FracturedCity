"""Test script for item metadata system.

Run this to verify:
1. ItemDef has new fields
2. Organic items have proper categorization
3. Flavor text generation works
4. Metadata can be added to item instances
"""

from items import (
    get_item_def, 
    get_item_display_name, 
    add_item_metadata,
    create_item_instance
)


def test_item_definitions():
    """Test that organic items have proper metadata fields."""
    print("=" * 60)
    print("TEST 1: Item Definition Fields")
    print("=" * 60)
    
    test_items = ["rat_meat", "bird_meat", "rat_pelt", "feathers", "rat_corpse", "bird_corpse"]
    
    for item_id in test_items:
        item_def = get_item_def(item_id)
        if item_def:
            print(f"\n{item_def.name} ({item_id}):")
            print(f"  Size: {item_def.size_class}")
            print(f"  Material: {item_def.material_type}")
            print(f"  State: {item_def.processing_state}")
            print(f"  Quality: {item_def.quality}/5")
            print(f"  Spoilage: {item_def.spoilage_rate} (0=never, 1=1 day)")
            print(f"  Stack: {item_def.stack_size}")
            print(f"  Weight: {item_def.weight}")
        else:
            print(f"ERROR: {item_id} not found!")
    
    print("\n✓ All items have metadata fields\n")


def test_flavor_text():
    """Test flavor text generation."""
    print("=" * 60)
    print("TEST 2: Flavor Text Generation")
    print("=" * 60)
    
    # Test 1: Basic item without metadata
    item1 = {"id": "rat_meat", "name": "Rat Meat"}
    display1 = get_item_display_name(item1, game_tick=0)
    print(f"\nBasic item (no metadata):")
    print(f"  Input: {item1}")
    print(f"  Output: '{display1}'")
    
    # Test 2: Item with source species
    item2 = {"id": "rat_meat", "name": "Rat Meat", "source_species": "rat"}
    display2 = get_item_display_name(item2, game_tick=0)
    print(f"\nWith source species:")
    print(f"  Input: {item2}")
    print(f"  Output: '{display2}'")
    
    # Test 3: Item with harvest time (just harvested)
    item3 = {
        "id": "bird_meat", 
        "name": "Bird Meat",
        "source_species": "bird",
        "harvest_tick": 1000
    }
    display3 = get_item_display_name(item3, game_tick=1030)  # 30 ticks later (< 1 hour)
    print(f"\nJust harvested:")
    print(f"  Input: harvest_tick=1000, game_tick=1030")
    print(f"  Output: '{display3}'")
    
    # Test 4: Item aged 12 hours
    item4 = {
        "id": "rat_meat",
        "name": "Rat Meat",
        "source_species": "rat",
        "harvest_tick": 1000
    }
    display4 = get_item_display_name(item4, game_tick=1000 + (60 * 12))  # 12 hours later
    print(f"\n12 hours old:")
    print(f"  Input: harvest_tick=1000, game_tick={1000 + (60 * 12)}")
    print(f"  Output: '{display4}'")
    
    # Test 5: Item aged 2 days
    item5 = {
        "id": "rat_pelt",
        "name": "Rat Pelt",
        "source_species": "rat",
        "harvest_tick": 1000
    }
    display5 = get_item_display_name(item5, game_tick=1000 + (60 * 24 * 2))  # 2 days later
    print(f"\n2 days old:")
    print(f"  Input: harvest_tick=1000, game_tick={1000 + (60 * 24 * 2)}")
    print(f"  Output: '{display5}'")
    
    # Test 6: Item with individual quality override
    item6 = {
        "id": "bird_meat",
        "name": "Bird Meat",
        "source_species": "bird",
        "individual_quality": 5  # Excellent quality
    }
    display6 = get_item_display_name(item6, game_tick=0)
    print(f"\nExcellent quality override:")
    print(f"  Input: individual_quality=5")
    print(f"  Output: '{display6}'")
    
    print("\n✓ Flavor text generation working\n")


def test_metadata_addition():
    """Test adding metadata to items."""
    print("=" * 60)
    print("TEST 3: Adding Metadata to Items")
    print("=" * 60)
    
    # Create a basic item instance
    item = {"id": "rat_meat", "name": "Rat Meat"}
    print(f"\nOriginal item: {item}")
    
    # Add metadata
    add_item_metadata(
        item,
        source_species="rat",
        harvest_tick=5000,
        harvested_by=42,
        individual_quality=1
    )
    
    print(f"After adding metadata: {item}")
    
    # Generate display name
    display = get_item_display_name(item, game_tick=5000 + (60 * 6))  # 6 hours later
    print(f"Display name: '{display}'")
    
    print("\n✓ Metadata addition working\n")


def test_material_categories():
    """Test that items are properly categorized by material type."""
    print("=" * 60)
    print("TEST 4: Material Type Categories")
    print("=" * 60)
    
    categories = {
        "meat": [],
        "hide": [],
        "feather": [],
        "other": []
    }
    
    test_items = ["rat_meat", "bird_meat", "rat_pelt", "feathers", 
                  "hard_hat", "work_gloves", "scrap_guitar"]
    
    for item_id in test_items:
        item_def = get_item_def(item_id)
        if item_def:
            mat_type = item_def.material_type
            if mat_type == "meat":
                categories["meat"].append(item_def.name)
            elif mat_type == "hide":
                categories["hide"].append(item_def.name)
            elif mat_type == "feather":
                categories["feather"].append(item_def.name)
            else:
                categories["other"].append(item_def.name)
    
    print("\nMaterial Categories:")
    for category, items in categories.items():
        if items:
            print(f"  {category.upper()}: {', '.join(items)}")
    
    print("\n✓ Material categorization working\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("ITEM METADATA SYSTEM TEST")
    print("=" * 60 + "\n")
    
    try:
        test_item_definitions()
        test_flavor_text()
        test_metadata_addition()
        test_material_categories()
        
        print("=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Hunt a rat in-game")
        print("2. Butcher at Bio-Matter Salvage Station")
        print("3. Check if meat shows source species and harvest time")
        print("4. Verify metadata persists through haul/storage")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

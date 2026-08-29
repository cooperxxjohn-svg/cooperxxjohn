"""
Create train/validation/test splits for CubiCasa5K dataset

Split ratios:
- Train: 80% (4,000 plans)
- Validation: 10% (500 plans)
- Test: 10% (500 plans)
"""

import os
import json
import random
from pathlib import Path
import shutil

def create_splits(data_dir="training_data", train_ratio=0.8, val_ratio=0.1, test_ratio=0.1):
    """
    Create train/val/test splits
    """
    data_dir = Path(data_dir)
    images_dir = data_dir / "images"

    # Get all image files
    image_files = list(images_dir.glob("*.png"))
    total = len(image_files)

    print(f"\n{'='*70}")
    print("CREATING TRAIN/VAL/TEST SPLITS")
    print(f"{'='*70}\n")
    print(f"Total images: {total}")

    # Shuffle
    random.seed(42)  # For reproducibility
    random.shuffle(image_files)

    # Calculate split sizes
    train_size = int(total * train_ratio)
    val_size = int(total * val_ratio)
    test_size = total - train_size - val_size

    # Split
    train_files = image_files[:train_size]
    val_files = image_files[train_size:train_size + val_size]
    test_files = image_files[train_size + val_size:]

    print(f"\nSplit sizes:")
    print(f"  Train: {len(train_files)} ({len(train_files)/total*100:.1f}%)")
    print(f"  Val:   {len(val_files)} ({len(val_files)/total*100:.1f}%)")
    print(f"  Test:  {len(test_files)} ({len(test_files)/total*100:.1f}%)")

    # Create split directories
    for split_name in ['train', 'val', 'test']:
        (data_dir / split_name / "images").mkdir(parents=True, exist_ok=True)
        (data_dir / split_name / "prompts").mkdir(parents=True, exist_ok=True)

    # Copy files to splits
    splits = {
        'train': train_files,
        'val': val_files,
        'test': test_files
    }

    for split_name, files in splits.items():
        print(f"\nCopying {split_name} files...")

        for i, image_path in enumerate(files):
            plan_id = image_path.stem

            # Copy image
            dest_image = data_dir / split_name / "images" / image_path.name
            shutil.copy(image_path, dest_image)

            # Copy prompt
            prompt_src = data_dir / "prompts" / f"{plan_id}.txt"
            if prompt_src.exists():
                dest_prompt = data_dir / split_name / "prompts" / f"{plan_id}.txt"
                shutil.copy(prompt_src, dest_prompt)

            # Copy metadata
            metadata_src = data_dir / "prompts" / f"{plan_id}.json"
            if metadata_src.exists():
                dest_metadata = data_dir / split_name / "prompts" / f"{plan_id}.json"
                shutil.copy(metadata_src, dest_metadata)

            if (i + 1) % 100 == 0:
                print(f"   {i + 1}/{len(files)}...")

        print(f"   ✅ {split_name}: {len(files)} files copied")

    # Create split metadata
    split_info = {
        'total': total,
        'train': len(train_files),
        'val': len(val_files),
        'test': len(test_files),
        'train_ratio': train_ratio,
        'val_ratio': val_ratio,
        'test_ratio': test_ratio,
        'seed': 42
    }

    split_info_file = data_dir / "split_info.json"
    with open(split_info_file, 'w') as f:
        json.dump(split_info, f, indent=2)

    print(f"\n{'='*70}")
    print("✅ SPLITS CREATED SUCCESSFULLY")
    print(f"{'='*70}\n")
    print(f"Split info saved to: {split_info_file}")
    print(f"\nDirectory structure:")
    print(f"  {data_dir}/")
    print(f"    ├── train/")
    print(f"    │   ├── images/ ({len(train_files)} images)")
    print(f"    │   └── prompts/ ({len(train_files)} prompts)")
    print(f"    ├── val/")
    print(f"    │   ├── images/ ({len(val_files)} images)")
    print(f"    │   └── prompts/ ({len(val_files)} prompts)")
    print(f"    └── test/")
    print(f"        ├── images/ ({len(test_files)} images)")
    print(f"        └── prompts/ ({len(test_files)} prompts)")
    print()


if __name__ == "__main__":
    create_splits()

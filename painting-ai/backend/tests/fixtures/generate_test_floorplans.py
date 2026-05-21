"""
Generate simple floor plan images for testing drywall detection
Creates basic architectural-style floor plans with walls, doors, and windows
"""

from PIL import Image, ImageDraw, ImageFont
import os


def create_simple_residential_floorplan(filepath: str):
    """
    Create a simple 30x20 residential floor plan
    One room with a door and two windows
    """
    # Create white canvas
    width, height = 1200, 800
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)

    # Scale: 1/4" = 1'-0" means 30ft = 300 pixels (10px per foot)
    scale = 10  # pixels per foot

    # Room: 30ft x 20ft starting at (100, 100)
    room_x = 100
    room_y = 100
    room_width = 30 * scale  # 300px
    room_height = 20 * scale  # 200px
    wall_thickness = 6  # pixels

    # Draw outer walls (thick black lines)
    # Top wall
    draw.rectangle([room_x, room_y, room_x + room_width, room_y + wall_thickness], fill='black')
    # Right wall
    draw.rectangle([room_x + room_width - wall_thickness, room_y, room_x + room_width, room_y + room_height], fill='black')
    # Bottom wall (with door opening)
    draw.rectangle([room_x, room_y + room_height - wall_thickness, room_x + 100, room_y + room_height], fill='black')
    draw.rectangle([room_x + 130, room_y + room_height - wall_thickness, room_x + room_width, room_y + room_height], fill='black')
    # Left wall (with windows)
    draw.rectangle([room_x, room_y, room_x + wall_thickness, room_y + 60], fill='black')
    draw.rectangle([room_x, room_y + 90, room_x + wall_thickness, room_y + 130], fill='black')
    draw.rectangle([room_x, room_y + 160, room_x + wall_thickness, room_y + room_height], fill='black')

    # Draw door (3ft wide) - arc symbol
    door_x = room_x + 100
    door_y = room_y + room_height - wall_thickness
    door_width = 30  # 3ft * 10px
    draw.arc([door_x, door_y - 30, door_x + door_width, door_y], start=0, end=90, fill='black', width=2)
    draw.line([door_x, door_y, door_x, door_y - 30], fill='black', width=2)

    # Draw windows (4ft wide each)
    # Window 1
    win1_x = room_x
    win1_y = room_y + 60
    win_width = 30  # 3ft
    draw.line([win1_x, win1_y, win1_x, win1_y + win_width], fill='blue', width=4)
    draw.line([win1_x - 3, win1_y + 7, win1_x + 3, win1_y + 7], fill='blue', width=1)
    draw.line([win1_x - 3, win1_y + 22, win1_x + 3, win1_y + 22], fill='blue', width=1)

    # Window 2
    win2_x = room_x
    win2_y = room_y + 130
    draw.line([win2_x, win2_y, win2_x, win2_y + win_width], fill='blue', width=4)
    draw.line([win2_x - 3, win2_y + 7, win2_x + 3, win2_y + 7], fill='blue', width=1)
    draw.line([win2_x - 3, win2_y + 22, win2_x + 3, win2_y + 22], fill='blue', width=1)

    # Add dimensions
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        font = ImageFont.load_default()

    # Room dimensions
    draw.text((room_x + room_width // 2 - 20, room_y - 30), "30'-0\"", fill='black', font=font)
    draw.text((room_x - 50, room_y + room_height // 2), "20'-0\"", fill='black', font=font)

    # Room label
    draw.text((room_x + 120, room_y + 80), "LIVING ROOM", fill='black', font=font)
    draw.text((room_x + 110, room_y + 100), "600 SF", fill='gray', font=font)

    # Scale indicator
    draw.text((50, height - 50), "SCALE: 1/4\" = 1'-0\"", fill='black', font=font)

    # Save
    img.save(filepath)
    print(f"Created: {filepath}")


def create_commercial_floorplan(filepath: str):
    """
    Create a commercial office floor plan
    40x30 open office with multiple doors and windows
    """
    width, height = 1400, 1000
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)

    scale = 10
    wall_thickness = 6

    # Main room: 40ft x 30ft
    room_x = 100
    room_y = 100
    room_width = 40 * scale
    room_height = 30 * scale

    # Outer walls
    draw.rectangle([room_x, room_y, room_x + room_width, room_y + wall_thickness], fill='black')
    draw.rectangle([room_x + room_width - wall_thickness, room_y, room_x + room_width, room_y + room_height], fill='black')
    draw.rectangle([room_x, room_y + room_height - wall_thickness, room_x + room_width, room_y + room_height], fill='black')
    draw.rectangle([room_x, room_y, room_x + wall_thickness, room_y + room_height], fill='black')

    # Interior partition wall (divide into 2 rooms)
    partition_x = room_x + room_width // 2
    draw.rectangle([partition_x - 3, room_y + wall_thickness, partition_x + 3, room_y + 120], fill='black')
    # Door opening in partition
    draw.rectangle([partition_x - 3, room_y + 180, partition_x + 3, room_y + room_height - wall_thickness], fill='black')

    # Draw door in partition
    door_x = partition_x - 15
    door_y = room_y + 120
    draw.arc([door_x, door_y, door_x + 30, door_y + 30], start=0, end=90, fill='black', width=2)

    # Windows on exterior walls
    for i in range(3):
        win_y = room_y + 60 + i * 80
        draw.line([room_x, win_y, room_x, win_y + 40], fill='blue', width=4)

    # Labels
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        font = ImageFont.load_default()

    draw.text((room_x + 60, room_y + 140), "OFFICE A", fill='black', font=font)
    draw.text((room_x + 270, room_y + 140), "OFFICE B", fill='black', font=font)
    draw.text((room_x + room_width // 2 - 20, room_y - 30), "40'-0\"", fill='black', font=font)
    draw.text((50, height - 50), "SCALE: 1/4\" = 1'-0\"", fill='black', font=font)

    img.save(filepath)
    print(f"Created: {filepath}")


def create_multi_room_floorplan(filepath: str):
    """
    Create a multi-room residential floor plan
    Living room, bedroom, bathroom layout
    """
    width, height = 1600, 1000
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)

    scale = 8
    wall_thickness = 6

    # Overall dimensions
    base_x = 100
    base_y = 100

    # Living Room: 20x15
    living_w = 20 * scale
    living_h = 15 * scale
    draw.rectangle([base_x, base_y, base_x + living_w, base_y + wall_thickness], fill='black')
    draw.rectangle([base_x, base_y, base_x + wall_thickness, base_y + living_h], fill='black')

    # Bedroom: 12x14
    bed_x = base_x + living_w
    bed_w = 12 * scale
    bed_h = 14 * scale
    draw.rectangle([bed_x - wall_thickness, base_y, bed_x + bed_w, base_y + wall_thickness], fill='black')
    draw.rectangle([bed_x + bed_w - wall_thickness, base_y, bed_x + bed_w, base_y + bed_h], fill='black')

    # Shared wall between living and bedroom (with door)
    draw.rectangle([base_x + living_w - wall_thickness, base_y, base_x + living_w, base_y + 40], fill='black')
    draw.rectangle([base_x + living_w - wall_thickness, base_y + 70, base_x + living_w, base_y + living_h], fill='black')

    # Bottom walls
    draw.rectangle([base_x, base_y + living_h - wall_thickness, base_x + living_w, base_y + living_h], fill='black')
    draw.rectangle([bed_x, base_y + bed_h - wall_thickness, bed_x + bed_w, base_y + bed_h], fill='black')

    # Windows
    for i in range(2):
        wx = base_x + 40 + i * 60
        draw.line([wx, base_y, wx + 30, base_y], fill='blue', width=4)

    # Labels
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        font = ImageFont.load_default()

    draw.text((base_x + 40, base_y + 60), "LIVING ROOM", fill='black', font=font)
    draw.text((base_x + 50, base_y + 80), "300 SF", fill='gray', font=font)
    draw.text((bed_x + 20, base_y + 60), "BEDROOM", fill='black', font=font)
    draw.text((bed_x + 30, base_y + 80), "168 SF", fill='gray', font=font)
    draw.text((50, height - 50), "SCALE: 1/4\" = 1'-0\"", fill='black', font=font)

    img.save(filepath)
    print(f"Created: {filepath}")


def create_high_ceiling_floorplan(filepath: str):
    """
    Create a floor plan with vaulted/high ceilings indicated
    """
    width, height = 1200, 800
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)

    scale = 10
    wall_thickness = 6

    # Room: 24ft x 20ft
    room_x = 100
    room_y = 100
    room_width = 24 * scale
    room_height = 20 * scale

    # Outer walls
    draw.rectangle([room_x, room_y, room_x + room_width, room_y + wall_thickness], fill='black')
    draw.rectangle([room_x + room_width - wall_thickness, room_y, room_x + room_width, room_y + room_height], fill='black')
    draw.rectangle([room_x, room_y + room_height - wall_thickness, room_x + room_width, room_y + room_height], fill='black')
    draw.rectangle([room_x, room_y, room_x + wall_thickness, room_y + room_height], fill='black')

    # Vaulted ceiling indicator (dashed lines showing roof pitch)
    for i in range(5):
        y = room_y + 40 + i * 25
        draw.line([room_x + room_width // 2, room_y + 30, room_x + 50 + i * 30, y], fill='gray', width=1)
        draw.line([room_x + room_width // 2, room_y + 30, room_x + room_width - 50 - i * 30, y], fill='gray', width=1)

    # Labels
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
    except:
        font = ImageFont.load_default()
        font_large = font

    draw.text((room_x + 60, room_y + 120), "GREAT ROOM", fill='black', font=font_large)
    draw.text((room_x + 50, room_y + 145), "VAULTED CEILING", fill='red', font=font)
    draw.text((room_x + 65, room_y + 165), "14' PEAK HEIGHT", fill='red', font=font)
    draw.text((50, height - 50), "SCALE: 1/4\" = 1'-0\"", fill='black', font=font)

    img.save(filepath)
    print(f"Created: {filepath}")


def create_complex_corners_floorplan(filepath: str):
    """
    Create a floor plan with multiple corners (L-shaped room)
    Tests corner detection
    """
    width, height = 1200, 1000
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)

    scale = 10
    wall_thickness = 6

    # L-shaped room
    # Horizontal part: 30ft x 12ft
    # Vertical part: 12ft x 18ft

    base_x = 100
    base_y = 100

    # Horizontal section
    h_width = 30 * scale
    h_height = 12 * scale

    # Vertical section
    v_width = 12 * scale
    v_height = 18 * scale

    # Draw horizontal section outline
    draw.rectangle([base_x, base_y, base_x + h_width, base_y + wall_thickness], fill='black')  # Top
    draw.rectangle([base_x, base_y, base_x + wall_thickness, base_y + h_height], fill='black')  # Left
    draw.rectangle([base_x, base_y + h_height - wall_thickness, base_x + v_width, base_y + h_height], fill='black')  # Bottom-left

    # Draw vertical section
    draw.rectangle([base_x, base_y + h_height - wall_thickness, base_x + wall_thickness, base_y + h_height + v_height], fill='black')  # Left continuation
    draw.rectangle([base_x, base_y + h_height + v_height - wall_thickness, base_x + v_width, base_y + h_height + v_height], fill='black')  # Bottom
    draw.rectangle([base_x + v_width - wall_thickness, base_y + h_height, base_x + v_width, base_y + h_height + v_height], fill='black')  # Right of vertical

    # Connect horizontal to vertical (inside corner)
    draw.rectangle([base_x + v_width - wall_thickness, base_y + h_height - wall_thickness, base_x + h_width, base_y + h_height], fill='black')  # Bottom-right horizontal
    draw.rectangle([base_x + h_width - wall_thickness, base_y, base_x + h_width, base_y + h_height], fill='black')  # Right of horizontal

    # Mark corners
    # Inside corner
    draw.ellipse([base_x + v_width - 15, base_y + h_height - 15, base_x + v_width + 15, base_y + h_height + 15], outline='red', width=2)

    # Outside corners (4 total)
    corners = [
        (base_x, base_y),  # Top-left
        (base_x + h_width, base_y),  # Top-right
        (base_x, base_y + h_height + v_height),  # Bottom-left
        (base_x + v_width, base_y + h_height + v_height),  # Bottom of vertical
    ]

    for cx, cy in corners:
        draw.ellipse([cx - 10, cy - 10, cx + 10, cy + 10], outline='green', width=2)

    # Labels
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except:
        font = ImageFont.load_default()

    draw.text((base_x + 100, base_y + 40), "L-SHAPED ROOM", fill='black', font=font)
    draw.text((base_x + v_width + 20, base_y + h_height - 10), "1 INSIDE CORNER", fill='red', font=font)
    draw.text((base_x + v_width + 20, base_y + h_height + 10), "4 OUTSIDE CORNERS", fill='green', font=font)
    draw.text((50, height - 50), "SCALE: 1/4\" = 1'-0\"", fill='black', font=font)

    img.save(filepath)
    print(f"Created: {filepath}")


if __name__ == "__main__":
    # Create fixtures directory if it doesn't exist
    script_dir = os.path.dirname(os.path.abspath(__file__))

    print("Generating test floor plan fixtures...")

    # Generate all test floor plans
    create_simple_residential_floorplan(os.path.join(script_dir, "simple_residential.png"))
    create_commercial_floorplan(os.path.join(script_dir, "commercial_office.png"))
    create_multi_room_floorplan(os.path.join(script_dir, "multi_room.png"))
    create_high_ceiling_floorplan(os.path.join(script_dir, "vaulted_ceiling.png"))
    create_complex_corners_floorplan(os.path.join(script_dir, "complex_corners.png"))

    print("\nAll fixtures generated successfully!")
    print("Files created:")
    print("  - simple_residential.png (30x20 room, 1 door, 2 windows)")
    print("  - commercial_office.png (40x30 office, partition wall)")
    print("  - multi_room.png (living room + bedroom)")
    print("  - vaulted_ceiling.png (24x20 with 14ft vaulted ceiling)")
    print("  - complex_corners.png (L-shaped room, multiple corners)")

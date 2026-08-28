from PIL import Image, ImageChops, ImageEnhance
import os
from pathlib import Path

def compute_ela(image_path: Path, quality: int = 90) -> str:
    original_path = str(image_path)
    filename = image_path.name
    temp_path = f"temp_ela_{filename}.jpg"
    
    # We will save uploads inside the VerifyX folder.
    uploads_dir = Path("uploads")
    uploads_dir.mkdir(parents=True, exist_ok=True)
    
    ela_save_path = uploads_dir / f"ela_{filename}.jpg"
    
    try:
        original = Image.open(original_path).convert('RGB')
        original.save(temp_path, 'JPEG', quality=quality)
        temporary = Image.open(temp_path)
        
        diff = ImageChops.difference(original, temporary)
        extrema = diff.getextrema()
        
        max_diff = max([ex[1] for ex in extrema])
        if max_diff == 0:
            max_diff = 1
        scale = 255.0 / max_diff
        
        ela_image = ImageEnhance.Brightness(diff).enhance(scale)
        ela_image.save(ela_save_path, 'JPEG')
        
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
        return str(ela_save_path)
    except Exception as e:
        print(f"ELA Error: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        img = Image.new('RGB', (224, 224))
        img.save(ela_save_path, 'JPEG')
        return str(ela_save_path)

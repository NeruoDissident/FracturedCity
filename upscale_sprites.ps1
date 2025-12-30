# PowerShell Script to Upscale 32x32 Sprites to 64x64
# Uses nearest-neighbor scaling to preserve pixel art style
# Requires Python with Pillow library installed

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found. Please install Python first." -ForegroundColor Red
    exit 1
}

# Check if Pillow is installed
$pillowCheck = python -c "import PIL; print('OK')" 2>&1
if ($pillowCheck -ne "OK") {
    Write-Host "Pillow library not found. Installing..." -ForegroundColor Yellow
    python -m pip install Pillow
}

# Create Python upscaling script
$pythonScript = @"
import os
import sys
from PIL import Image

def upscale_sprite(input_path, output_path):
    """Upscale 32x32 sprite to 64x64 using nearest-neighbor."""
    try:
        # Open image
        img = Image.open(input_path)
        
        # Check if already 64x64
        if img.size == (64, 64):
            print(f"  SKIP: {os.path.basename(input_path)} (already 64x64)")
            return False
        
        # Check if 32x32
        if img.size != (32, 32):
            print(f"  WARN: {os.path.basename(input_path)} is {img.size[0]}x{img.size[1]}, not 32x32")
        
        # Upscale using nearest-neighbor (preserves pixel art)
        upscaled = img.resize((64, 64), Image.NEAREST)
        
        # Save with same format and transparency
        upscaled.save(output_path, format=img.format)
        print(f"  OK: {os.path.basename(input_path)} -> {os.path.basename(output_path)}")
        return True
        
    except Exception as e:
        print(f"  ERROR: {os.path.basename(input_path)} - {str(e)}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python upscale.py <directory>")
        sys.exit(1)
    
    directory = sys.argv[1]
    
    if not os.path.exists(directory):
        print(f"ERROR: Directory not found: {directory}")
        sys.exit(1)
    
    # Find all PNG files recursively
    png_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.lower().endswith('.png'):
                png_files.append(os.path.join(root, file))
    
    if not png_files:
        print(f"No PNG files found in {directory}")
        return
    
    print(f"\nFound {len(png_files)} PNG files")
    print("=" * 60)
    
    upscaled_count = 0
    skipped_count = 0
    error_count = 0
    
    for png_file in png_files:
        result = upscale_sprite(png_file, png_file)
        if result:
            upscaled_count += 1
        elif result is False:
            error_count += 1
        else:
            skipped_count += 1
    
    print("=" * 60)
    print(f"\nResults:")
    print(f"  Upscaled: {upscaled_count}")
    print(f"  Skipped:  {skipped_count}")
    print(f"  Errors:   {error_count}")
    print(f"\nDone!")

if __name__ == "__main__":
    main()
"@

# Save Python script to temp file
$tempPythonScript = Join-Path $env:TEMP "upscale_sprites_temp.py"
$pythonScript | Out-File -FilePath $tempPythonScript -Encoding UTF8

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Sprite Upscaler: 32x32 -> 64x64" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Ask user which directory to process
Write-Host "Select directory to upscale:" -ForegroundColor Yellow
Write-Host "  1. assets/tiles/walls/" -ForegroundColor White
Write-Host "  2. assets/tiles/" -ForegroundColor White
Write-Host "  3. assets/tiles/roads/" -ForegroundColor White
Write-Host "  4. assets/tiles/dirt/" -ForegroundColor White
Write-Host "  5. assets/workstations/" -ForegroundColor White
Write-Host "  6. assets/furniture/" -ForegroundColor White
Write-Host "  7. All assets/ (recursive)" -ForegroundColor White
Write-Host "  8. Custom path" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter choice (1-8)"

switch ($choice) {
    "1" { $targetDir = "assets/tiles/walls" }
    "2" { $targetDir = "assets/tiles" }
    "3" { $targetDir = "assets/tiles/roads" }
    "4" { $targetDir = "assets/tiles/dirt" }
    "5" { $targetDir = "assets/workstations" }
    "6" { $targetDir = "assets/furniture" }
    "7" { $targetDir = "assets" }
    "8" { 
        $targetDir = Read-Host "Enter path (relative or absolute)"
    }
    default {
        Write-Host "Invalid choice. Exiting." -ForegroundColor Red
        Remove-Item $tempPythonScript -ErrorAction SilentlyContinue
        exit 1
    }
}

# Check if directory exists
if (-not (Test-Path $targetDir)) {
    Write-Host "`nERROR: Directory not found: $targetDir" -ForegroundColor Red
    Write-Host "Make sure you're running this from the FracturedCity root folder." -ForegroundColor Yellow
    Remove-Item $tempPythonScript -ErrorAction SilentlyContinue
    exit 1
}

# Confirm before processing
Write-Host "`nTarget directory: $targetDir" -ForegroundColor Green
$confirm = Read-Host "This will OVERWRITE original files. Continue? (y/n)"

if ($confirm -ne "y") {
    Write-Host "Cancelled." -ForegroundColor Yellow
    Remove-Item $tempPythonScript -ErrorAction SilentlyContinue
    exit 0
}

# Run Python script
Write-Host "`nProcessing..." -ForegroundColor Cyan
python $tempPythonScript $targetDir

# Cleanup
Remove-Item $tempPythonScript -ErrorAction SilentlyContinue

Write-Host "`nPress any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

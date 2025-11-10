#!/usr/bin/env python3
"""
CalmCadence White Background Remover
Removes white backgrounds from existing icons to make them transparent
"""

import os
from PIL import Image, ImageChops
import shutil

def remove_white_background(image_path, output_path, threshold=240):
    """
    Remove white background from an image and make it transparent
    
    Args:
        image_path: Path to input image
        output_path: Path to save output image
        threshold: RGB threshold for considering a pixel "white" (0-255)
    """
    try:
        # Open the image
        img = Image.open(image_path)
        
        # Convert to RGBA if not already
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Get image data
        data = img.getdata()
        
        # Create new image data with transparency
        new_data = []
        for item in data:
            # If pixel is close to white, make it transparent
            if (item[0] > threshold and item[1] > threshold and item[2] > threshold):
                # Make transparent (alpha = 0)
                new_data.append((item[0], item[1], item[2], 0))
            else:
                # Keep original pixel with full opacity
                new_data.append(item)
        
        # Update image data
        img.putdata(new_data)
        
        # Save the result
        img.save(output_path, "PNG")
        print(f"✅ Processed: {os.path.basename(output_path)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error processing {image_path}: {e}")
        return False

def create_ico_from_png(png_path, ico_path):
    """Create an ICO file from a PNG with multiple sizes"""
    try:
        img = Image.open(png_path)
        
        # Standard Windows icon sizes
        sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        
        # Create resized versions
        images = []
        for size in sizes:
            resized = img.resize(size, Image.Resampling.LANCZOS)
            images.append(resized)
        
        # Save as ICO
        img.save(ico_path, format='ICO', sizes=sizes)
        print(f"✅ Created ICO: {os.path.basename(ico_path)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating ICO {ico_path}: {e}")
        return False

def process_calmcadence_icons():
    """Process CalmCadence icons to remove white backgrounds"""
    
    # Source and destination paths
    source_dir = "CalmCadence_Branding_Pack"
    output_dir = "CalmCadence_Transparent_Icons"
    assets_dir = "CalmCadence.App/Assets"
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    print("🎨 Processing CalmCadence icons to remove white backgrounds...")
    
    # Process PNG icon
    png_source = os.path.join(source_dir, "CalmCadence_Icon.png")
    png_output = os.path.join(output_dir, "CalmCadence_Icon_Transparent.png")
    
    if os.path.exists(png_source):
        if remove_white_background(png_source, png_output):
            # Create ICO from the transparent PNG
            ico_output = os.path.join(output_dir, "CalmCadence_Icon_Transparent.ico")
            create_ico_from_png(png_output, ico_output)
            
            # Copy to assets directory
            assets_png = os.path.join(assets_dir, "CalmCadence_Icon.png")
            assets_ico = os.path.join(assets_dir, "CalmCadence_Icon.ico")
            
            try:
                shutil.copy2(png_output, assets_png)
                print(f"✅ Updated: {assets_png}")
                
                if os.path.exists(ico_output):
                    shutil.copy2(ico_output, assets_ico)
                    print(f"✅ Updated: {assets_ico}")
                    
            except Exception as e:
                print(f"❌ Error copying to assets: {e}")
    else:
        print(f"❌ Source PNG not found: {png_source}")
    
    # Process SVG (copy as-is since SVGs can have transparent backgrounds)
    svg_source = os.path.join(source_dir, "CalmCadence_HeroLogo.svg")
    svg_output = os.path.join(output_dir, "CalmCadence_HeroLogo.svg")
    svg_assets = os.path.join(assets_dir, "CalmCadence_HeroLogo.svg")
    
    if os.path.exists(svg_source):
        try:
            shutil.copy2(svg_source, svg_output)
            shutil.copy2(svg_source, svg_assets)
            print(f"✅ Copied SVG: {os.path.basename(svg_assets)}")
        except Exception as e:
            print(f"❌ Error copying SVG: {e}")
    
    return output_dir

def create_additional_sizes():
    """Create additional icon sizes needed for Windows app packaging"""
    
    output_dir = "CalmCadence_Transparent_Icons"
    assets_dir = "CalmCadence.App/Assets"
    
    # Base transparent icon
    base_icon = os.path.join(output_dir, "CalmCadence_Icon_Transparent.png")
    
    if not os.path.exists(base_icon):
        print(f"❌ Base transparent icon not found: {base_icon}")
        return
    
    try:
        img = Image.open(base_icon)
        
        # Windows app manifest required sizes
        required_sizes = {
            "Square44x44Logo.scale-200.png": (44, 44),
            "Square44x44Logo.targetsize-24_altform-unplated.png": (24, 24),
            "Square150x150Logo.scale-200.png": (150, 150),
            "Wide310x150Logo.scale-200.png": (310, 150),
            "StoreLogo.png": (50, 50),
            "SplashScreen.scale-200.png": (620, 300),
            "LockScreenLogo.scale-200.png": (24, 24)
        }
        
        for filename, size in required_sizes.items():
            if filename == "Wide310x150Logo.scale-200.png":
                # Create wide logo by centering the square icon
                wide_img = Image.new('RGBA', size, (0, 0, 0, 0))
                square_size = min(size[1], 150)  # Use height as reference
                resized_icon = img.resize((square_size, square_size), Image.Resampling.LANCZOS)
                
                # Center the icon
                x = (size[0] - square_size) // 2
                y = (size[1] - square_size) // 2
                wide_img.paste(resized_icon, (x, y), resized_icon)
                
                output_path = os.path.join(assets_dir, filename)
                wide_img.save(output_path, "PNG")
                
            elif filename == "SplashScreen.scale-200.png":
                # Create splash screen with centered icon
                splash_img = Image.new('RGBA', size, (0, 0, 0, 0))
                icon_size = min(size[1] // 2, 200)  # Reasonable size for splash
                resized_icon = img.resize((icon_size, icon_size), Image.Resampling.LANCZOS)
                
                # Center the icon
                x = (size[0] - icon_size) // 2
                y = (size[1] - icon_size) // 2
                splash_img.paste(resized_icon, (x, y), resized_icon)
                
                output_path = os.path.join(assets_dir, filename)
                splash_img.save(output_path, "PNG")
                
            else:
                # Regular square resize
                resized = img.resize(size, Image.Resampling.LANCZOS)
                output_path = os.path.join(assets_dir, filename)
                resized.save(output_path, "PNG")
            
            print(f"✅ Created: {filename}")
            
    except Exception as e:
        print(f"❌ Error creating additional sizes: {e}")

def main():
    """Main execution function"""
    print("🚀 Starting CalmCadence white background removal...")
    
    output_dir = process_calmcadence_icons()
    
    if output_dir and os.path.exists(output_dir):
        print("\n🎨 Creating additional icon sizes...")
        create_additional_sizes()
        
        print(f"\n🎉 Success! Transparent icons processed!")
        print(f"📁 Output directory: {output_dir}")
        print("📁 Assets updated in: CalmCadence.App/Assets/")
        print("\n📋 What was done:")
        print("✅ Removed white backgrounds from PNG icons")
        print("✅ Created transparent ICO file")
        print("✅ Generated all required Windows app icon sizes")
        print("✅ Updated assets in the app directory")
    else:
        print("\n❌ Failed to process icons. Please check the error messages above.")

if __name__ == "__main__":
    main()
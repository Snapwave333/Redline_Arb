#!/usr/bin/env python3
"""
CalmCadence Transparent Icon Generator
Generates app icons with transparent backgrounds using Gemini API
"""

import os
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO

def generate_transparent_icon():
    """Generate a transparent CalmCadence app icon using Gemini API"""
    
    # Initialize Gemini client
    client = genai.Client(api_key="AIzaSyCKAnXQ9sJENXzWduXOwmt3Vcp4uXQTsyE")
    
    # Craft prompt for transparent icon generation
    prompt = """Create a clean, modern app icon for 'CalmCadence' - a mindfulness and routine management app.
    
    Requirements:
    - TRANSPARENT background (no white background)
    - Minimalist design suitable for Windows app icons
    - Incorporate elements suggesting calm, mindfulness, and routine/scheduling
    - Use soothing colors like soft blues, greens, or purples
    - Simple geometric shapes or subtle gradients
    - Should work well at multiple sizes (16x16 to 512x512)
    - Professional appearance suitable for productivity software
    
    Style: Clean, modern, minimalist icon with transparent background"""
    
    try:
        print("🎨 Generating transparent CalmCadence icon...")
        
        response = client.models.generate_content(
            model="gemini-2.5-flash-image-preview",
            contents=[prompt],
        )
        
        # Process the response
        for part in response.candidates[0].content.parts:
            if part.text is not None:
                print(f"📝 Generation notes: {part.text}")
            elif part.inline_data is not None:
                # Load and process the image
                image = Image.open(BytesIO(part.inline_data.data))
                
                # Convert to RGBA to ensure transparency support
                if image.mode != 'RGBA':
                    image = image.convert('RGBA')
                
                # Create output directory if it doesn't exist
                output_dir = "CalmCadence_Transparent_Icons"
                os.makedirs(output_dir, exist_ok=True)
                
                # Save in multiple formats and sizes
                sizes = [16, 24, 32, 44, 48, 64, 128, 150, 256, 310, 512]
                
                for size in sizes:
                    # Resize with high-quality resampling
                    resized = image.resize((size, size), Image.Resampling.LANCZOS)
                    
                    # Save as PNG (supports transparency)
                    png_path = os.path.join(output_dir, f"CalmCadence_Icon_{size}x{size}.png")
                    resized.save(png_path, "PNG", optimize=True)
                    print(f"✅ Saved: {png_path}")
                
                # Save original size versions
                original_png = os.path.join(output_dir, "CalmCadence_Icon_Original.png")
                image.save(original_png, "PNG", optimize=True)
                print(f"✅ Saved original: {original_png}")
                
                # Create ICO file with multiple sizes
                ico_path = os.path.join(output_dir, "CalmCadence_Icon_Transparent.ico")
                
                # Prepare sizes for ICO (Windows standard sizes)
                ico_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
                ico_images = []
                
                for size in ico_sizes:
                    resized = image.resize(size, Image.Resampling.LANCZOS)
                    ico_images.append(resized)
                
                # Save as ICO
                image.save(ico_path, format='ICO', sizes=ico_sizes)
                print(f"✅ Saved ICO: {ico_path}")
                
                return output_dir
                
    except Exception as e:
        print(f"❌ Error generating icon: {e}")
        return None

def main():
    """Main execution function"""
    print("🚀 Starting CalmCadence transparent icon generation...")
    
    output_dir = generate_transparent_icon()
    
    if output_dir:
        print(f"\n🎉 Success! Transparent icons generated in: {output_dir}")
        print("\n📋 Next steps:")
        print("1. Review the generated icons")
        print("2. Replace the existing icons in CalmCadence.App/Assets/")
        print("3. Update the app manifest if needed")
    else:
        print("\n❌ Failed to generate icons. Please check the error messages above.")

if __name__ == "__main__":
    main()
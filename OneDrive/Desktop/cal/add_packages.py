#!/usr/bin/env python3
"""
Add NuGet packages to CalmCadence projects
"""

import subprocess
import sys

def run_command(cmd):
    """Run a command and return the result"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Warning: {result.stderr}")
        return False
    print("✅ Success")
    return True

def add_packages():
    """Add required NuGet packages to projects"""
    
    packages = [
        # Data project packages
        ("CalmCadence.Data/CalmCadence.Data.csproj", "Microsoft.EntityFrameworkCore.Tools"),
        ("CalmCadence.Data/CalmCadence.Data.csproj", "Microsoft.EntityFrameworkCore.Design"),
        
        # Core project packages
        ("CalmCadence.Core/CalmCadence.Core.csproj", "CommunityToolkit.Mvvm"),
        ("CalmCadence.Core/CalmCadence.Core.csproj", "System.Text.Json"),
        ("CalmCadence.Core/CalmCadence.Core.csproj", "Ical.Net"),
        ("CalmCadence.Core/CalmCadence.Core.csproj", "Microsoft.Extensions.Logging"),
        
        # App project packages
        ("CalmCadence.App/CalmCadence.App.csproj", "CommunityToolkit.Mvvm"),
        ("CalmCadence.App/CalmCadence.App.csproj", "CommunityToolkit.WinUI.UI.Controls"),
        ("CalmCadence.App/CalmCadence.App.csproj", "Microsoft.Extensions.Hosting"),
        ("CalmCadence.App/CalmCadence.App.csproj", "Microsoft.Extensions.DependencyInjection"),
        
        # Test project packages
        ("CalmCadence.Tests/CalmCadence.Tests.csproj", "Moq"),
        ("CalmCadence.Tests/CalmCadence.Tests.csproj", "FluentAssertions"),
        ("CalmCadence.Tests/CalmCadence.Tests.csproj", "Microsoft.EntityFrameworkCore.InMemory"),
    ]
    
    success_count = 0
    for project, package in packages:
        if run_command(f"dotnet add {project} package {package}"):
            success_count += 1
    
    print(f"\n🎉 Added {success_count}/{len(packages)} packages successfully!")
    return True

def main():
    """Main execution function"""
    print("📚 Adding NuGet packages to CalmCadence projects...")
    
    try:
        add_packages()
        print("✅ Package installation completed!")
        return 0
        
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
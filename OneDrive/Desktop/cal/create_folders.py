#!/usr/bin/env python3
"""
Create folder structure for CalmCadence projects
"""

import os
from pathlib import Path

def create_folder_structure():
    """Create the folder structure for each project"""
    
    folders = {
        "CalmCadence.App": [
            "Views", "ViewModels", "Controls", "Converters", 
            "Services", "Helpers", "Styles"
        ],
        "CalmCadence.Core": [
            "Models", "Services", "Interfaces", "Extensions",
            "Enums", "Constants", "Utilities"
        ],
        "CalmCadence.Data": [
            "Models", "Context", "Migrations", "Repositories",
            "Configurations", "Seed"
        ],
        "CalmCadence.Tests": [
            "Unit", "Integration", "Helpers", "Fixtures"
        ]
    }
    
    for project, project_folders in folders.items():
        print(f"📁 Creating folders for {project}...")
        for folder in project_folders:
            folder_path = Path(project) / folder
            folder_path.mkdir(parents=True, exist_ok=True)
            # Create .gitkeep file to ensure folders are tracked
            (folder_path / ".gitkeep").touch()
            print(f"  ✅ {folder}")
    
    return True

def create_gitignore():
    """Create a comprehensive .gitignore file"""
    gitignore_content = """# Build results
[Dd]ebug/
[Dd]ebugPublic/
[Rr]elease/
[Rr]eleases/
x64/
x86/
[Ww][Ii][Nn]32/
[Aa][Rr][Mm]/
[Aa][Rr][Mm]64/
bld/
[Bb]in/
[Oo]bj/
[Ll]og/
[Ll]ogs/

# Visual Studio 2015/2017 cache/options directory
.vs/

# MSTest test Results
[Tt]est[Rr]esult*/
[Bb]uild[Ll]og.*

# NUnit
*.VisualState.xml
TestResult.xml
nunit-*.xml

# .NET Core
project.lock.json
project.fragment.lock.json
artifacts/

# Files built by Visual Studio
*_i.c
*_p.c
*_h.h
*.ilk
*.meta
*.obj
*.iobj
*.pch
*.pdb
*.ipdb
*.pgc
*.pgd
*.rsp
*.sbr
*.tlb
*.tli
*.tlh
*.tmp
*.tmp_proj
*_wpftmp.csproj
*.log
*.vspscc
*.vssscc
.builds
*.pidb
*.svclog
*.scc

# Visual Studio profiler
*.psess
*.vsp
*.vspx
*.sap

# Visual Studio Trace Files
*.e2e

# ReSharper is a .NET coding add-in
_ReSharper*/
*.[Rr]e[Ss]harper
*.DotSettings.user

# Coverlet is a free, cross platform Code Coverage Tool
coverage*.json
coverage*.xml
coverage*.info

# Visual Studio code coverage results
*.coverage
*.coveragexml

# NuGet Packages
*.nupkg
*.snupkg
**/[Pp]ackages/*
!**/[Pp]ackages/build/
*.nuget.props
*.nuget.targets

# Windows Store app package directories and files
AppPackages/
BundleArtifacts/
Package.StoreAssociation.xml
_pkginfo.txt
*.appx
*.appxbundle
*.appxupload

# Visual Studio cache files
*.[Cc]ache
!?*.[Cc]ache/

# Others
ClientBin/
~$*
*~
*.dbmdl
*.dbproj.schemaview
*.jfm
*.pfx
*.publishsettings
orleans.codegen.cs

# SQL Server files
*.mdf
*.ldf
*.ndf

# Node.js Tools for Visual Studio
.ntvs_analysis.dat
node_modules/

# Python Tools for Visual Studio (PTVS)
__pycache__/
*.pyc

# Local History for Visual Studio
.localhistory/

# BeatPulse healthcheck temp database
healthchecksdb

# Fody - auto-generated XML schema
FodyWeavers.xsd

# VS Code files
.vscode/*
!.vscode/settings.json
!.vscode/tasks.json
!.vscode/launch.json
!.vscode/extensions.json
*.code-workspace

# Local History for Visual Studio Code
.history/

# Windows Installer files from build outputs
*.cab
*.msi
*.msix
*.msm
*.msp

# JetBrains Rider
.idea/
*.sln.iml

# CalmCadence specific
*.db
*.db-shm
*.db-wal
appsettings.local.json
"""
    
    with open(".gitignore", "w") as f:
        f.write(gitignore_content)
    
    print("📝 Created .gitignore file")
    return True

def main():
    """Main execution function"""
    print("🏗️ Creating CalmCadence folder structure...")
    
    try:
        if not create_folder_structure():
            print("❌ Failed to create folder structure")
            return 1
        
        if not create_gitignore():
            print("❌ Failed to create .gitignore")
            return 1
        
        print("✅ Folder structure created successfully!")
        print("🎉 CalmCadence solution is ready for development!")
        
        return 0
        
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
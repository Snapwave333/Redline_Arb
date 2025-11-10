#!/usr/bin/env python3
"""
CalmCadence Solution Scaffolding Script
Automates the creation of a .NET 8 WinUI 3 solution with proper MVVM structure
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return the result"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    print(f"Success: {result.stdout}")
    return True

def create_solution_structure():
    """Create the complete CalmCadence solution structure"""
    
    # Create main solution
    print("🚀 Creating CalmCadence solution...")
    if not run_command("dotnet new sln -n CalmCadence"):
        return False
    
    # Create projects in subdirectories
    projects = [
        ("CalmCadence.App", "winui"),
        ("CalmCadence.Core", "classlib"),
        ("CalmCadence.Data", "classlib"),
        ("CalmCadence.Tests", "xunit")
    ]
    
    for project_name, template in projects:
        print(f"📦 Creating {project_name} project...")
        
        # Create project directory
        project_dir = Path(project_name)
        project_dir.mkdir(exist_ok=True)
        
        # Create project in subdirectory
        if not run_command(f"dotnet new {template} -n {project_name}", cwd=str(project_dir)):
            return False
        
        # Add project to solution (specify the .csproj file path)
        csproj_path = project_dir / f"{project_name}.csproj"
        if not run_command(f"dotnet sln add {csproj_path}"):
            return False
    
    # Add project references
    print("🔗 Setting up project references...")
    references = [
        ("CalmCadence.App/CalmCadence.App.csproj", "CalmCadence.Core/CalmCadence.Core.csproj"),
        ("CalmCadence.App/CalmCadence.App.csproj", "CalmCadence.Data/CalmCadence.Data.csproj"),
        ("CalmCadence.Core/CalmCadence.Core.csproj", "CalmCadence.Data/CalmCadence.Data.csproj"),
        ("CalmCadence.Tests/CalmCadence.Tests.csproj", "CalmCadence.Core/CalmCadence.Core.csproj"),
        ("CalmCadence.Tests/CalmCadence.Tests.csproj", "CalmCadence.Data/CalmCadence.Data.csproj"),
        ("CalmCadence.Tests/CalmCadence.Tests.csproj", "CalmCadence.App/CalmCadence.App.csproj")
    ]
    
    for from_proj, to_proj in references:
        if not run_command(f"dotnet add {from_proj} reference {to_proj}"):
            return False
    
    return True

def add_nuget_packages():
    """Add required NuGet packages to projects"""
    
    packages = {
        "CalmCadence.App/CalmCadence.App.csproj": [
            "CommunityToolkit.Mvvm",
            "CommunityToolkit.WinUI.UI.Controls",
            "Microsoft.Extensions.Hosting",
            "Microsoft.Extensions.DependencyInjection"
        ],
        "CalmCadence.Core/CalmCadence.Core.csproj": [
            "CommunityToolkit.Mvvm",
            "System.Text.Json",
            "Ical.Net",
            "Microsoft.Extensions.Logging"
        ],
        "CalmCadence.Data/CalmCadence.Data.csproj": [
            "Microsoft.EntityFrameworkCore.Sqlite",
            "Microsoft.EntityFrameworkCore.Tools",
            "Microsoft.EntityFrameworkCore.Design"
        ],
        "CalmCadence.Tests/CalmCadence.Tests.csproj": [
            "Microsoft.NET.Test.Sdk",
            "xunit",
            "xunit.runner.visualstudio",
            "coverlet.collector",
            "Moq",
            "FluentAssertions",
            "Microsoft.EntityFrameworkCore.InMemory"
        ]
    }
    
    for project, project_packages in packages.items():
        print(f"📚 Adding packages to {project}...")
        for package in project_packages:
            if not run_command(f"dotnet add {project} package {package}"):
                print(f"Warning: Failed to add {package} to {project}")
    
    return True

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
        for folder in project_folders:
            folder_path = Path(project) / folder
            folder_path.mkdir(parents=True, exist_ok=True)
            # Create .gitkeep file to ensure folders are tracked
            (folder_path / ".gitkeep").touch()
    
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

# ASP.NET Scaffolding
ScaffoldingReadMe.txt

# StyleCop
StyleCopReport.xml

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

# Chutzpah Test files
_Chutzpah*

# Visual C++ cache files
ipch/
*.aps
*.ncb
*.opendb
*.opensdf
*.sdf
*.cachefile
*.VC.db
*.VC.VC.opendb

# Visual Studio profiler
*.psess
*.vsp
*.vspx
*.sap

# Visual Studio Trace Files
*.e2e

# TFS 2012 Local Workspace
$tf/

# Guidance Automation Toolkit
*.gpState

# ReSharper is a .NET coding add-in
_ReSharper*/
*.[Rr]e[Ss]harper
*.DotSettings.user

# TeamCity is a build add-in
_TeamCity*

# DotCover is a Code Coverage Tool
*.dotCover

# AxoCover is a Code Coverage Tool
.axoCover/*
!.axoCover/settings.json

# Coverlet is a free, cross platform Code Coverage Tool
coverage*.json
coverage*.xml
coverage*.info

# Visual Studio code coverage results
*.coverage
*.coveragexml

# NCrunch
_NCrunch_*
.*crunch*.local.xml
nCrunchTemp_*

# MightyMoose
*.mm.*
AutoTest.Net/

# Web workbench (sass)
.sass-cache/

# Installshield output folder
[Ee]xpress/

# DocProject is a documentation generator add-in
DocProject/buildhelp/
DocProject/Help/*.HxT
DocProject/Help/*.HxC
DocProject/Help/*.hhc
DocProject/Help/*.hhk
DocProject/Help/*.hhp
DocProject/Help/Html2
DocProject/Help/html

# Click-Once directory
publish/

# Publish Web Output
*.[Pp]ublish.xml
*.azurePubxml
# Note: Comment the next line if you want to checkin your web deploy settings,
# but database connection strings (with potential passwords) will be unencrypted
*.pubxml
*.publishproj

# Microsoft Azure Web App publish settings. Comment the next line if you want to
# checkin your Azure Web App publish settings, but sensitive information contained
# in these files may be visible to others.
*.azurePubxml

# NuGet Packages
*.nupkg
# NuGet Symbol Packages
*.snupkg
# The packages folder can be ignored because of Package Restore
**/[Pp]ackages/*
# except build/, which is used as an MSBuild target.
!**/[Pp]ackages/build/
# Uncomment if necessary however generally it will be regenerated when needed
#!**/[Pp]ackages/repositories.config
# NuGet v3's project.json files produces more ignorable files
*.nuget.props
*.nuget.targets

# Microsoft Azure Build Output
csx/
*.build.csdef

# Microsoft Azure Emulator
ecf/
rcf/

# Windows Store app package directories and files
AppPackages/
BundleArtifacts/
Package.StoreAssociation.xml
_pkginfo.txt
*.appx
*.appxbundle
*.appxupload

# Visual Studio cache files
# files ending in .cache can be ignored
*.[Cc]ache
# but keep track of directories ending in .cache
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

# Including strong name files can present a security risk
# (https://github.com/github/gitignore/pull/2483#issue-259490424)
#*.snk

# Since there are multiple workflows, uncomment next line to ignore bower_components
# (https://github.com/github/gitignore/pull/1529#issuecomment-104372622)
#bower_components/

# RIA/Silverlight projects
Generated_Code/

# Backup & report files from converting an old project file
# to a newer Visual Studio version. Backup files are not needed,
# because we have git ;-)
_UpgradeReport_Files/
Backup*/
UpgradeLog*.XML
UpgradeLog*.htm
CConversionReportFiles/

# SQL Server files
*.mdf
*.ldf
*.ndf

# Business Intelligence projects
*.rdl.data
*.bim.layout
*.bim_*.settings
*.rptproj.rsuser
*- [Bb]ackup.rdl
*- [Bb]ackup ([0-9]).rdl
*- [Bb]ackup ([0-9][0-9]).rdl

# Microsoft Fakes
FakesAssemblies/

# GhostDoc plugin setting file
*.GhostDoc.xml

# Node.js Tools for Visual Studio
.ntvs_analysis.dat
node_modules/

# Visual Studio 6 build log
*.plg

# Visual Studio 6 workspace options file
*.opt

# Visual Studio 6 auto-generated workspace file (contains which files were open etc.)
*.vbw

# Visual Studio LightSwitch build output
**/*.HTMLClient/GeneratedArtifacts
**/*.DesktopClient/GeneratedArtifacts
**/*.DesktopClient/ModelManifest.xml
**/*.Server/GeneratedArtifacts
**/*.Server/ModelManifest.xml
_Pvt_Extensions

# Paket dependency manager
.paket/paket.exe
paket-files/

# FAKE - F# Make
.fake/

# CodeRush personal settings
.cr/personal

# Python Tools for Visual Studio (PTVS)
__pycache__/
*.pyc

# Cake - Uncomment if you are using it
# tools/**
# !tools/packages.config

# Tabs Studio
*.tss

# Telerik's JustMock configuration file
*.jmconfig

# BizTalk build output
*.btp.cs
*.btm.cs
*.odx.cs
*.xsd.cs

# OpenCover UI analysis results
OpenCover/

# Azure Stream Analytics local run output
ASALocalRun/

# MSBuild Binary and Structured Log
*.binlog

# NVidia Nsight GPU debugger configuration file
*.nvuser

# MFractors (Xamarin productivity tool) working folder
.mfractor/

# Local History for Visual Studio
.localhistory/

# BeatPulse healthcheck temp database
healthchecksdb

# Backup folder for Package Reference Convert tool in Visual Studio 2017
MigrationBackup/

# Ionide (cross platform F# VS Code tools) working folder
.ionide/

# Fody - auto-generated XML schema
FodyWeavers.xsd

# VS Code files for those working on multiple tools
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
"""
    
    with open(".gitignore", "w") as f:
        f.write(gitignore_content)
    
    return True

def main():
    """Main execution function"""
    print("🎯 Starting CalmCadence solution scaffolding...")
    
    try:
        if not create_solution_structure():
            print("❌ Failed to create solution structure")
            return 1
        
        if not add_nuget_packages():
            print("⚠️ Some packages failed to install, but continuing...")
        
        if not create_folder_structure():
            print("❌ Failed to create folder structure")
            return 1
        
        if not create_gitignore():
            print("❌ Failed to create .gitignore")
            return 1
        
        print("✅ CalmCadence solution scaffolding completed successfully!")
        print("🎉 Ready to build something amazing!")
        
        return 0
        
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
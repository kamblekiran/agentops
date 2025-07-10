#!/usr/bin/env python3
"""
Script to create a downloadable archive of the Azure AgentOps code
"""

import os
import zipfile
import datetime

def create_archive():
    """Create a ZIP archive of all project files"""
    
    # Get current timestamp for filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"azure_agentops_{timestamp}.zip"
    
    print(f"📦 Creating archive: {archive_name}")
    
    # Files and directories to include
    include_patterns = [
        "*.py",
        "*.txt", 
        "*.md",
        "*.yml",
        "*.yaml",
        "*.json",
        "*.ini",
        "*.env.example",
        "Dockerfile",
        "Makefile",
        ".gitignore"
    ]
    
    # Directories to include
    include_dirs = [
        "agents/",
        "utils/", 
        "sections/",
        "tests/",
        "mock_data/"
    ]
    
    # Files to exclude
    exclude_patterns = [
        "__pycache__/",
        "*.pyc",
        ".env",
        ".git/",
        "*.png",
        "*.jpg",
        "*.jpeg",
        ".DS_Store"
    ]
    
    with zipfile.ZipFile(archive_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        
        # Add root level files
        for file in os.listdir('.'):
            if os.path.isfile(file):
                # Check if file matches include patterns
                include_file = False
                for pattern in include_patterns:
                    if pattern.startswith('*'):
                        if file.endswith(pattern[1:]):
                            include_file = True
                            break
                    elif file == pattern:
                        include_file = True
                        break
                
                # Check if file should be excluded
                exclude_file = False
                for pattern in exclude_patterns:
                    if pattern.startswith('*'):
                        if file.endswith(pattern[1:]):
                            exclude_file = True
                            break
                    elif file == pattern:
                        exclude_file = True
                        break
                
                if include_file and not exclude_file:
                    print(f"  📄 Adding: {file}")
                    zipf.write(file)
        
        # Add directories and their contents
        for dir_name in include_dirs:
            if os.path.exists(dir_name):
                for root, dirs, files in os.walk(dir_name):
                    # Skip excluded directories
                    dirs[:] = [d for d in dirs if not any(d.startswith(pattern.rstrip('/')) for pattern in exclude_patterns)]
                    
                    for file in files:
                        file_path = os.path.join(root, file)
                        
                        # Check if file should be excluded
                        exclude_file = False
                        for pattern in exclude_patterns:
                            if pattern.startswith('*'):
                                if file.endswith(pattern[1:]):
                                    exclude_file = True
                                    break
                            elif file == pattern:
                                exclude_file = True
                                break
                        
                        if not exclude_file:
                            print(f"  📁 Adding: {file_path}")
                            zipf.write(file_path)
    
    file_size = os.path.getsize(archive_name)
    print(f"✅ Archive created successfully!")
    print(f"📦 File: {archive_name}")
    print(f"📏 Size: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
    
    return archive_name

if __name__ == "__main__":
    archive_name = create_archive()
    print(f"\n🎉 Your Azure AgentOps code is ready for download!")
    print(f"📥 Download: {archive_name}")
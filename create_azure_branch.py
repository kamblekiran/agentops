#!/usr/bin/env python3
"""
Script to create Azure branch and commit changes using Python instead of shell commands
"""

import os
import subprocess
import sys

def run_command(cmd, check=True):
    """Run command and handle errors gracefully"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
        print(f"✅ Command succeeded: {cmd}")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {cmd}")
        print(f"Error: {e.stderr}")
        return None

def main():
    print("🚀 Creating Azure branch and committing changes...")
    
    # Check if we're in a git repository
    if not os.path.exists('.git'):
        print("❌ Not in a git repository. Please run this from the project root.")
        return False
    
    # Create and switch to azure branch
    print("📝 Creating azure branch...")
    result = run_command("git checkout -b azure")
    if not result:
        # Branch might already exist, try to switch to it
        print("🔄 Branch might exist, trying to switch...")
        result = run_command("git checkout azure", check=False)
        if not result:
            print("❌ Failed to create or switch to azure branch")
            return False
    
    # Add all changes
    print("📦 Adding all changes...")
    result = run_command("git add .")
    if not result:
        print("❌ Failed to add changes")
        return False
    
    # Commit changes
    print("💾 Committing changes...")
    commit_message = "feat: Complete Azure migration - Replace GCP with Azure services"
    result = run_command(f'git commit -m "{commit_message}"')
    if not result:
        print("⚠️ Commit failed - might be no changes to commit")
    
    # Push to remote
    print("🚀 Pushing to remote...")
    result = run_command("git push -u origin azure")
    if not result:
        print("❌ Failed to push to remote")
        return False
    
    print("✅ Successfully created Azure branch and pushed changes!")
    print("🔗 Check your GitHub repository for the new 'azure' branch")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
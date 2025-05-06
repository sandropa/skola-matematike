#!/usr/bin/env python3

import os
import subprocess
import fnmatch
import sys
from pathlib import Path


# --- Configuration ---
OUTPUT_FILE = "llm_prompt_context.txt"
MAX_FILE_SIZE_KB = 512  # Skip files larger than this (in Kilobytes)
# Use absolute path for the output file to reliably skip it during walk
OUTPUT_FILE_ABS = os.path.abspath(OUTPUT_FILE)

# Define patterns/directories/extensions to EXCLUDE explicitly.
# Uses fnmatch patterns (similar to shell globbing: *, ?, []).
# Add more as needed for your specific project.
# NOTE: These patterns are matched against the *relative* path from the root.
EXCLUDE_PATTERNS = [
    # Version Control System internal directories (matched explicitly)
    ".git/*",
    ".env",
    ".gitignore",
    "create_llm_context.py",
    "frontend/package-lock.json",
    "frontend/package.json",
    "experiments",

    # Common Dependency Directories (often gitignored anyway, but good explicit exclude)
    "node_modules/*",
    "vendor/*",
    "bower_components/*",
    ".venv/*",
    "venv/*",
    "env/*",
    ".env/*",
    "__pycache__/*",
    "target/*",  # Rust/Java build output
    "build/*",
    "dist/*",

    # Common Binary/Non-Code File Extensions
    "*.png", "*.jpg", "*.jpeg", "*.gif", "*.svg", "*.ico",  # Images
    "*.zip", "*.tar", "*.gz", "*.rar", "*.7z",             # Archives
    "*.pdf", "*.doc", "*.docx", "*.xls", "*.xlsx", "*.ppt", "*.pptx", # Documents
    "*.o", "*.a", "*.so", "*.dll", "*.exe", "*.lib",       # Compiled objects/libs/executables
    "*.class", "*.jar",                                   # Java compiled
    "*.pyc", "*.pyo",                                     # Python compiled
    "*.mp3", "*.wav", "*.ogg",                             # Audio
    "*.mp4", "*.avi", "*.mov", "*.webm",                  # Video
    "*.lock",                                             # Lock files
    "*.log",                                              # Log files
    "*.sqlite", "*.db",                                   # Databases

    # Specific Files/Folders to Exclude
    OUTPUT_FILE,                                        # Don't include the output file itself
    ".DS_Store",                                        # macOS metadata
]

# Directories to completely skip during os.walk (more efficient)
# Must be directory names, not patterns
EXCLUDE_DIRS = {
    ".git",
    "node_modules",
    "vendor",
    "bower_components",
    ".venv",
    "venv",
    "env",
    "__pycache__",
    "target",
    "build",
    "dist",
    "data"
}

# --- Helper Functions ---

def is_git_available():
    """Checks if the 'git' command is available."""
    try:
        subprocess.run(['git', '--version'], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def is_likely_text_file(filepath, block_size=512):
    """
    Basic heuristic to check if a file is likely text-based.
    Tries to decode a small chunk using UTF-8. Looks for null bytes.
    """
    try:
        with open(filepath, 'rb') as f:
            block = f.read(block_size)
            if not block:
                return True  # Empty file is considered text
            if b'\x00' in block:
                return False # Contains null byte, likely binary
            # Try decoding a block - this is imperfect but catches some non-UTF8
            try:
                block.decode('utf-8')
                return True
            except UnicodeDecodeError:
                # Could be another text encoding, but for LLM context, UTF-8 is safest
                # Or it could be binary. We'll err on the side of caution.
                 try:
                    # Attempt with another common encoding like latin-1 as a fallback
                    block.decode('latin-1')
                    return True # Still potentially text-like
                 except UnicodeDecodeError:
                    return False # Likely binary if both fail
    except IOError:
        return False # Cannot open file

def matches_exclude_pattern(relative_path, patterns):
    """Checks if the relative path matches any of the exclude patterns."""
    # Normalize path separators for consistent matching
    normalized_path = relative_path.replace(os.sep, '/')
    for pattern in patterns:
        if fnmatch.fnmatch(normalized_path, pattern):
            return True
        # Also check if the pattern matches just the filename part
        if '/' not in pattern and fnmatch.fnmatch(os.path.basename(normalized_path), pattern):
             return True
    return False

def get_git_ignored(file_paths, repo_root="."):
    """
    Uses 'git check-ignore --stdin' for efficiency to check multiple files.
    Returns a set of ignored file paths (relative to repo_root).
    """
    ignored = set()
    if not file_paths:
        return ignored

    # Ensure paths are relative to the repo root for git check-ignore
    relative_paths = [os.path.relpath(p, repo_root) for p in file_paths]

    try:
        # Use --stdin for batch processing, --no-index allows checking outside a repo (though less useful)
        # -q for quiet (only prints ignored files), -z for null-terminated output
        process = subprocess.run(
            ['git', 'check-ignore', '--stdin', '-z', '-q'],
            input='\0'.join(relative_paths) + '\0',
            capture_output=True,
            text=True, # Decode output as text
            cwd=repo_root, # Run git command from the root
            check=False # Don't throw error on non-zero exit (e.g., if none are ignored)
        )

        if process.returncode == 0 or process.returncode == 1: # 0 = some ignored, 1 = none ignored
             # Split the null-terminated output
            ignored_relative = set(filter(None, process.stdout.split('\0')))
             # Convert back to the original absolute/relative paths provided
            path_map = {os.path.relpath(p, repo_root): p for p in file_paths}
            ignored = {path_map[rel] for rel in ignored_relative if rel in path_map}

        elif process.returncode == 128:
            print("Warning: 'git check-ignore' failed. Is this a git repository?", file=sys.stderr)
        # Else: some other error occurred, proceed without gitignore info for this batch

    except FileNotFoundError:
        # This should have been caught by is_git_available, but belt-and-suspenders
        print("Error: 'git' command not found during check-ignore.", file=sys.stderr)
    except Exception as e:
        print(f"Error running git check-ignore: {e}", file=sys.stderr)

    return ignored

# --- Main Script Logic ---

def main():
    """Generates the combined context file."""
    workspace_root = "."
    abs_root = os.path.abspath(workspace_root)
    files_to_process = []
    git_available = is_git_available()
    is_repo = git_available and os.path.isdir(os.path.join(abs_root, ".git"))

    if not git_available:
        print("Warning: 'git' command not found. Cannot check .gitignore.", file=sys.stderr)
    elif not is_repo:
         print("Warning: Not running in a git repository root. Cannot check .gitignore.", file=sys.stderr)


    print("Starting context generation...")
    print(f"Output file: {OUTPUT_FILE}")
    print(f"Excluding files larger than {MAX_FILE_SIZE_KB}KB")
    print(f"Scanning directory: {abs_root}")

    # First pass: Collect all potentially relevant file paths
    for root, dirs, files in os.walk(workspace_root, topdown=True):
        # Efficiently skip excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        for filename in files:
            filepath = os.path.join(root, filename)
            abs_filepath = os.path.abspath(filepath)
            relative_path = os.path.relpath(filepath, workspace_root)

            # 1. Skip the output file itself
            if abs_filepath == OUTPUT_FILE_ABS:
                # print(f"Skipping output file: {relative_path}") # Debug
                continue

            # 2. Check against explicit exclude patterns (directories already handled by pruning dirs)
            if matches_exclude_pattern(relative_path, EXCLUDE_PATTERNS):
                # print(f"Skipping excluded pattern: {relative_path}") # Debug
                continue

            # If not excluded by patterns, add to list for batch Git check and further processing
            files_to_process.append(filepath)


    # Second pass: Check gitignore (in batch) and other properties
    git_ignored_files = set()
    if is_repo and files_to_process:
        print("Checking .gitignore...")
        # Process in chunks if the list is very large (git command line limits)
        chunk_size = 1000
        for i in range(0, len(files_to_process), chunk_size):
             chunk = files_to_process[i:i+chunk_size]
             git_ignored_files.update(get_git_ignored(chunk, repo_root=abs_root))
        print(f"Found {len(git_ignored_files)} gitignored files to skip.")


    # Third pass: Filter and concatenate
    added_files_count = 0
    with open(OUTPUT_FILE_ABS, "w", encoding="utf-8", errors="replace") as outfile:
        for filepath in files_to_process:
            relative_path = os.path.relpath(filepath, workspace_root)

            # 3. Check if gitignored (use the pre-computed set)
            if filepath in git_ignored_files:
                # print(f"Skipping gitignored file: {relative_path}") # Debug
                continue

            # 4. Check file size
            try:
                file_size_bytes = os.path.getsize(filepath)
                if file_size_bytes > MAX_FILE_SIZE_KB * 1024:
                    # print(f"Skipping large file ({file_size_bytes // 1024} KB): {relative_path}") # Debug
                    continue
            except OSError:
                # print(f"Skipping unreadable file: {relative_path}") # Debug
                continue # Skip if cannot get size (e.g., broken symlink)


            # 5. Check if likely text-based
            if not is_likely_text_file(filepath):
                # print(f"Skipping non-text/binary file: {relative_path}") # Debug
                continue

            # If all checks pass, add the file content
            print(f"Adding: {relative_path}")
            try:
                outfile.write(f"--- START FILE: {relative_path.replace(os.sep, '/')} ---\n")
                with open(filepath, "r", encoding="utf-8", errors="ignore") as infile:
                    # Read and write line by line or in chunks if files can be huge
                    for line in infile:
                         outfile.write(line)
                outfile.write("\n--- END FILE: {relative_path.replace(os.sep, '/')} ---\n\n")
                added_files_count += 1
            except Exception as e:
                print(f"Error reading file {relative_path}: {e}", file=sys.stderr)
                # Optionally write an error marker to the output
                outfile.write(f"--- START FILE: {relative_path.replace(os.sep, '/')} ---\n")
                outfile.write(f"*** Error reading file: {e} ***\n")
                outfile.write(f"--- END FILE: {relative_path.replace(os.sep, '/')} ---\n\n")

    print("-" * 20)
    if added_files_count > 0:
        print(f"Done. Added content from {added_files_count} files to {OUTPUT_FILE}")
    else:
        print(f"Warning: Output file '{OUTPUT_FILE}' created, but no suitable files were found or added.")

if __name__ == "__main__":
    main()
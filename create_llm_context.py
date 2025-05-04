import os

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

    # Common Dependency Directories (often gitignored anyway, but good explicit exclude)
    "node_modules/*",       # Node.js dependencies
    "vendor/*",             # PHP/Ruby dependencies
    "bower_components/*",   # Old JS dependencies
    ".venv/*",              # Python virtual environment
    "venv/*",               # Python virtual environment
    "env/*",                # Common name for virtual env or config
    "__pycache__/*",        # Python bytecode cache
    "target/*",             # Rust/Java build output
    "build/*",              # Common build output dir
    "dist/*",               # Common distribution dir

    # Environment Files (Important!)
    ".env",                 # Standard env file
    ".env.*",               # Covers .env.local, .env.development, etc.
    "config/*",             # Often contains sensitive or large config files

    # Common Binary/Non-Code File Extensions
    "*.png", "*.jpg", "*.jpeg", "*.gif", "*.svg", "*.ico",  # Images
    "*.zip", "*.tar", "*.gz", "*.rar", "*.7z",             # Archives
    "*.pdf", "*.doc", "*.docx", "*.xls", "*.xlsx", "*.ppt", "*.pptx", # Documents
    "*.o", "*.a", "*.so", "*.dll", "*.exe", "*.lib",       # Compiled objects/libs/executables
    "*.class", "*.jar",                                   # Java compiled
    "*.pyc", "*.pyo",                                     # Python compiled
    "*.mp3", "*.wav", "*.ogg",                             # Audio
    "*.mp4", "*.avi", "*.mov", "*.webm",                  # Video
    "*.lock",                                             # Lock files (yarn.lock, package-lock.json often large)
    "*.log",                                              # Log files
    "*.sqlite", "*.db",                                   # Databases

    # Specific Files/Folders to Exclude
    OUTPUT_FILE,                                        # Don't include the output file itself
    ".DS_Store",                                        # macOS metadata
]

# Directories to completely skip during os.walk (more efficient)
# Must be directory names, not patterns. Ensures we don't even look inside.
EXCLUDE_DIRS = {
    ".git",
    "node_modules",         # Node.js dependencies
    "vendor",               # PHP/Ruby dependencies
    "bower_components",     # Old JS dependencies
    ".venv",                # Python virtual environment
    "venv",                 # Python virtual environment
    "env",                  # Common name for virtual env or config dir
    "__pycache__",          # Python bytecode cache
    "target",               # Rust/Java build output
    "build",                # Common build output dir
    "dist",                 # Common distribution dir
    # Add other *specific directory names* here if needed
}

# --- [Rest of the script remains the same] ---
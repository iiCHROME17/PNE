#!/bin/bash

# Usage: ./combine_py.sh /path/to/folder output_file.txt
# Example: ./combine_py.sh ./narrative_engine combined.txt

if [ $# -ne 2 ]; then
    echo "Usage: $0 <folder> <output_file>"
    exit 1
fi

FOLDER="$1"
OUTPUT="$2"

# Clear output file if it exists
> "$OUTPUT"

# Loop over all .py files recursively
find "$FOLDER" -type f -name "*.py" | sort | while read -r file; do
    echo -e "\n# ===== File: $file =====\n" >> "$OUTPUT"
    cat "$file" >> "$OUTPUT"
done

echo "✓ Combined all Python files from $FOLDER into $OUTPUT"

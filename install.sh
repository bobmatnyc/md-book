#!/bin/bash
# Installation script for The Augmented Programmer Book Reader

echo "Installing The Augmented Programmer Book Reader..."

# Check if uv is available
if ! command -v uv &> /dev/null; then
    echo "Error: uv is required but not installed."
    echo "Install uv with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Create virtual environment and install dependencies using uv
echo "Creating virtual environment and installing dependencies..."
uv sync

# Make the script executable
chmod +x book_reader.py

# Create a convenient launcher script
cat > read_book.sh << 'EOF'
#!/bin/bash
# Convenient launcher for The Augmented Programmer Book Reader

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Run the reader using uv
cd "$SCRIPT_DIR"
uv run python book_reader.py "$@"
EOF

chmod +x read_book.sh

echo "Installation complete!"
echo ""
echo "Usage options:"
echo "  1. Direct execution: uv run python book_reader.py"
echo "  2. Convenient launcher: ./read_book.sh"
echo ""
echo "Examples:"
echo "  ./read_book.sh                 # Start interactive reader"
echo "  ./read_book.sh --chapter 5     # Jump to chapter 5"
echo "  ./read_book.sh --toc           # Show table of contents"
echo ""
echo "Run './read_book.sh --help' for more options."

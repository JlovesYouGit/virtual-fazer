#!/bin/bash

# Cobol Compilation and Execution Script
# For Windows: Use GnuCOBOL with appropriate paths

echo "=== Cobol Memory Parser Compilation ==="

# Check if GnuCOBOL is installed
if ! command -v cobc &> /dev/null; then
    echo "GnuCOBOL not found. Please install GnuCOBOL first."
    echo "Download from: https://gnucobol.sourceforge.io/"
    exit 1
fi

# Compile memory parser
echo "Compiling memory_parser.cbl..."
cobc -x -free memory_parser.cbl -o memory_parser.exe

if [ $? -eq 0 ]; then
    echo "Memory parser compiled successfully!"
else
    echo "Compilation failed for memory_parser.cbl"
    exit 1
fi

# Compile database interface
echo "Compiling database_interface.cbl..."
cobc -x -free database_interface.cbl -o db_interface.exe

if [ $? -eq 0 ]; then
    echo "Database interface compiled successfully!"
else
    echo "Compilation failed for database_interface.cbl"
    exit 1
fi

# Create sample data file
echo "Creating sample data file..."
cat > userdata.dat << EOF
12345678-1234-1234-1234-123456789012|John Doe|TECHNOLOGY|85.50|150|2026-04-17 14:30:00|
87654321-4321-4321-4321-210987654321|Jane Smith|SOCIAL|92.75|200|2026-04-17 15:45:00|
11111111-1111-1111-1111-111111111111|Bob Johnson|CREATIVE|78.25|75|2026-04-17 16:20:00|
22222222-2222-2222-2222-222222222222|Alice Brown|BUSINESS|88.00|125|2026-04-17 17:10:00|
33333333-3333-3333-3333-333333333333|Charlie Wilson|TECHNOLOGY|91.50|180|2026-04-17 18:00:00|
EOF

echo "Sample data file created."

# Run memory parser
echo "Running memory parser..."
./memory_parser.exe

if [ $? -eq 0 ]; then
    echo "Memory parser executed successfully!"
    echo "Check parsed_data.txt for results."
else
    echo "Memory parser execution failed."
fi

# Create database file for interface
echo "Creating database file..."
touch database.dat

echo "=== Cobol Setup Complete ==="
echo "Files created:"
echo "  - memory_parser.exe (Memory parsing executable)"
echo "  - db_interface.exe (Database interface executable)"
echo "  - userdata.dat (Sample user data)"
echo "  - database.dat (Database file)"
echo "  - parsed_data.txt (Parser output)"

echo ""
echo "To test the database interface:"
echo "  ./db_interface.exe"
echo ""
echo "Integration with Python backend:"
echo "  Use subprocess to call these executables"
echo "  Pass data through temporary files or stdin/stdout"

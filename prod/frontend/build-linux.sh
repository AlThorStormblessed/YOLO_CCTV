#!/bin/bash

# Script to build NextJS correctly on Linux environments
echo "Setting up Linux-compatible build environment..."

# Make sure lib/utils.ts exists
mkdir -p lib
if [ ! -f "lib/utils.ts" ]; then
  echo "Creating lib/utils.ts..."
  cat > lib/utils.ts << 'EOL'
import { clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: any[]) {
  return twMerge(clsx(inputs))
}
EOL
fi

# Create appropriate configuration files
echo "Creating path alias configuration files..."

# Create jsconfig.json
cat > jsconfig.json << 'EOL'
{
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./*"]
    }
  }
}
EOL

# Ensure dependencies
echo "Installing required dependencies..."
bun install clsx tailwind-merge

# Build with increased memory
echo "Building the application..."
NODE_OPTIONS="--max-old-space-size=4096" bun run build

echo "Build process completed!" 
FROM ubuntu:24.04

# Install Node.js 20 for Claude Code CLI
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs

# Install Python and build tools
RUN apt-get install -y python3 python3-pip python3-venv

# Install Claude Code CLI globally
RUN npm install -g @anthropic-ai/claude-code

# Create application directory
WORKDIR /opt/claude-api

# Copy your main.py file
COPY main.py .

# Create Python

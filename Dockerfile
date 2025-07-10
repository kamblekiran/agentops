# Dockerfile for Azure AgentOps

FROM python:3.11-slim

WORKDIR /app

# Set PATH to ensure all standard binaries are accessible
ENV PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"

# Install system dependencies including git + Azure CLI
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    gnupg \
    lsb-release \
    && curl -sL https://aka.ms/InstallAzureCLIDeb | bash \
    && rm -rf /var/lib/apt/lists/*

# Preinstall any Python CLI dependencies
RUN pip install coverage

# Install Python dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose Streamlit default port
EXPOSE 8501

# Run the app
CMD ["bash", "-c", "streamlit run main.py --server.port=${PORT:-8501} --server.address=0.0.0.0"]
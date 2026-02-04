# Docker Image Setup Instructions

## Pre-Hackathon Setup (for Organizers)

### 1. Pull the Original Image
```bash
# Pull from Google Artifact Registry
docker pull us-west2-docker.pkg.dev/izumi-479101/izumi-repo/swebench-pro-openlibrary-python312:latest

# Or if you have Python 3.12 specific image
docker pull us-west2-docker.pkg.dev/izumi-479101/izumi-repo/swebench-pro-openlibrary:latest
```

### 2. Tag for GitHub Container Registry
```bash
# Tag the image for GitHub Container Registry
docker tag us-west2-docker.pkg.dev/izumi-479101/izumi-repo/swebench-pro-openlibrary-python312:latest \
  manojva/openlibrary-python312:latest
```

### 3. Push to GitHub Container Registry
```bash
# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Push the image
docker push manojva/openlibrary-python312:latest
```

### 4. Set Image Visibility
Make the image publicly accessible:
1. Go to your GitHub organization/user settings
2. Navigate to Packages
3. Find the `openlibrary-python312` package
4. Change visibility to Public

## For Hackathon Participants

### Using the Docker Image

The Docker image is pre-configured and available at:
```
manojva/openlibrary-python312:latest
```

You can use it in your GitHub Actions workflow:

```yaml
jobs:
  evaluate:
    runs-on: ubuntu-latest
    container:
      image: manojva/openlibrary-python312:latest
      options: --user root
```

### Testing Locally

If you want to test locally before pushing to GitHub:

```bash
# Pull the image
docker pull manojva/openlibrary-python312:latest

# Run interactively
docker run -it --rm \
  -v $(pwd):/workspace \
  -w /testbed \
  manojva/openlibrary-python312:latest \
  /bin/bash

# Inside the container, you can test your scripts
cd /testbed
python your_script.py
```

### Image Contents

The Docker image includes:
- Python 3.12
- OpenLibrary repository dependencies
- All required Python packages (pytest, anthropic SDK, etc.)
- Database setup for tests
- Pre-configured environment variables

### Troubleshooting

#### Permission Issues
If you encounter permission issues:
```yaml
container:
  options: --user root  # Run as root user
```

#### Network Issues
If the container can't access external APIs:
```yaml
container:
  options: --network host  # Use host network
```

#### Volume Mounting
To access files from your repository:
```yaml
steps:
  - name: Checkout code
    uses: actions/checkout@v4

  - name: Run script
    run: |
      cp $GITHUB_WORKSPACE/scripts/* /testbed/
      cd /testbed
      python run_claude.py
```

## Alternative: Building Your Own Image

If you need to modify the image:

```dockerfile
# Dockerfile
FROM manojva/openlibrary-python312:latest

# Add your customizations
RUN pip install additional-package

# Copy your files
COPY scripts/ /opt/scripts/

WORKDIR /testbed
```

Build and use:
```bash
docker build -t my-custom-image .
docker run -it my-custom-image
```
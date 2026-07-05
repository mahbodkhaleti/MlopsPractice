# HW03 Docker Image Size Report

| Repository   | Tag   | Size   |
|--------------|-------|--------|

## Analysis
The naive image is larger because it copies the full working directory and keeps build-time tools, caches, notebooks, and data-adjacent files in the final image layer. The optimized multi-stage image installs dependencies in a builder stage, copies only runtime artifacts, and excludes local files through `.dockerignore`.

For production I would use the optimized image because it has a smaller attack surface, transfers faster, and is easier to reproduce in Kubernetes.

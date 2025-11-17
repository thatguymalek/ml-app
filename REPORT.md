## CI/CD Implementation

### Overview
The CI/CD pipeline is implemented using **GitHub Actions** and consists of a single comprehensive workflow that runs on every push and pull request to the `main` and `develop` branches.

### Workflow File: `.github/workflows/ci.yml`

The workflow includes the following stages:

#### 1. **Code Checkout**
```yaml
- name: Checkout code
  uses: actions/checkout@v4
```
- Uses the official GitHub checkout action (v4)
- Clones the repository code into the runner environment

#### 2. **Python Environment Setup**
```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.11'
    cache: 'pip'
```
- Uses the official `actions/setup-python@v5` action
- Configures Python 3.11 environment
- Enables pip caching for faster dependency installation

#### 3. **Dependency Installation**
```yaml
- name: Install dependencies
  run: |
    python -m pip install --upgrade pip
    pip install -r requirements.txt
```
- Upgrades pip to the latest version
- Installs all project dependencies from `requirements.txt`

#### 4. **Code Linting**
```yaml
- name: Lint with flake8
  run: |
    flake8 src tests --count --select=E9,F63,F7,F82 --show-source --statistics
    flake8 src tests --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```
- Two-pass linting strategy:
  - **Pass 1:** Strict check for syntax errors (fails pipeline if found)
  - **Pass 2:** Warning-level checks for code quality (doesn't fail pipeline)

#### 5. **Test Execution**
```yaml
- name: Run tests with pytest
  run: |
    pytest tests/ -v --tb=short --junit-xml=test-results.xml
```
- Runs all tests in the `tests/` directory
- Generates JUnit XML report for test results
- Verbose output with short traceback format

#### 6. **Test Results Upload**
```yaml
- name: Upload test results
  uses: actions/upload-artifact@v4
  if: always()
  with:
    name: test-results
    path: test-results.xml
    retention-days: 30
```
- Uploads test results as artifacts
- Runs even if tests fail (`if: always()`)
- Retains results for 30 days

#### 7. **Docker Image Build**
```yaml
- name: Build Docker image
  run: |
    docker build -t ml-app:${{ github.sha }} .
    docker save ml-app:${{ github.sha }} -o ml-app-image.tar
```
- Builds Docker image tagged with commit SHA
- Saves image as TAR archive for artifact upload

#### 8. **Docker Image Upload**
```yaml
- name: Upload Docker image artifact
  uses: actions/upload-artifact@v4
  with:
    name: docker-image
    path: ml-app-image.tar
    retention-days: 7
    compression-level: 0
```
- Uploads Docker image as artifact
- Retains for 7 days (images are large)
- No compression (Docker images are already compressed)

---

## Design Choices and Rationale

### 1. **Python Version Selection**
- **Choice:** Python 3.11
- **Rationale:** Modern, stable version with performance improvements; compatible with all dependencies (scikit-learn, pandas, numpy)

### 2. **Trigger Events**
- **Choice:** `push` and `pull_request` on `main` and `develop` branches
- **Rationale:** 
  - Ensures code quality before merging to main branch
  - Validates pull requests automatically
  - Includes develop branch for feature development workflow

### 3. **Linting Strategy (Two-Pass)**
- **Choice:** Strict errors first, then warnings
- **Rationale:**
  - Critical syntax errors must fail the build
  - Code quality warnings provide feedback but don't block deployment
  - Encourages clean code without being overly restrictive

### 4. **Test Result Artifacts**
- **Choice:** 30-day retention with `if: always()`
- **Rationale:**
  - Long retention allows historical analysis of test trends
  - Upload even on failure helps debugging
  - JUnit XML format integrates with many CI tools

### 5. **Docker Image Artifacts**
- **Choice:** 7-day retention, no additional compression
- **Rationale:**
  - Docker images are large; shorter retention saves storage costs
  - Images already compressed by Docker layers
  - TAR format allows easy loading with `docker load`

### 6. **Pip Caching**
- **Choice:** Enable pip caching in setup-python action
- **Rationale:**
  - Significantly speeds up subsequent workflow runs
  - Reduces dependency download time
  - Free optimization with minimal configuration

### 7. **Dockerfile Design**
- **Choice:** Slim Python base image, layered copying
- **Rationale:**
  - Smaller image size for faster builds
  - Copy requirements first for better layer caching
  - Production-ready container configuration

---

## Running Locally

### Prerequisites
- Python 3.11 or higher
- pip package manager
- Docker (optional, for containerized runs)
- Git

### Local Development Setup

#### 1. Clone the Repository
```bash
git clone https://github.com/thatguymalek/ml-app.git
cd ml-app
```

#### 2. Create Virtual Environment (Recommended)
```bash
# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Run Tests
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src

# Generate JUnit XML report (same as CI)
pytest tests/ -v --junit-xml=test-results.xml
```

#### 5. Run Linter
```bash
# Check for critical errors
flake8 src tests --count --select=E9,F63,F7,F82 --show-source --statistics

# Full linting
flake8 src tests --count --max-complexity=10 --max-line-length=127 --statistics
```

#### 6. Train the Model
```bash
# Navigate to src directory
cd src
python train.py
cd ..
```

#### 7. Make Predictions
```bash
cd src
python predict.py
cd ..
```

### Running with Docker

#### Build the Image
```bash
docker build -t ml-app:local .
```

#### Run Training in Container
```bash
docker run ml-app:local
```

#### Run Tests in Container
```bash
docker run ml-app:local pytest tests/ -v
```

#### Load CI-Built Image
```bash
# Download artifact from GitHub Actions, then:
docker load -i ml-app-image.tar
docker run ml-app:<commit-sha>
```

---

## CI Pipeline Behavior

### Workflow Triggers

The CI pipeline automatically triggers when:

1. **Push Events**
   - Direct push to `main` branch
   - Direct push to `develop` branch
   - Merge commits to these branches

2. **Pull Request Events**
   - PR opened targeting `main` or `develop`
   - New commits pushed to PR branch
   - PR synchronized (force push, rebase)

### Pipeline Execution Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Trigger (Push/PR)                                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│ 2. Checkout Code (actions/checkout@v4)                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│ 3. Setup Python 3.11 + Pip Cache (actions/setup-python@v5) │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│ 4. Install Dependencies (pip install -r requirements.txt)  │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│ 5. Run Flake8 Linter                                        │
│    - Critical errors → FAIL pipeline                        │
│    - Warnings → Continue (logged)                           │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│ 6. Run Pytest Tests                                         │
│    - Generate test-results.xml                              │
│    - Tests fail → FAIL pipeline                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│ 7. Upload Test Results (always runs)                       │
│    - Artifact: test-results.xml (30 days)                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│ 8. Build Docker Image                                       │
│    - Tag: ml-app:<commit-sha>                               │
│    - Save as TAR file                                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│ 9. Upload Docker Image Artifact (7 days)                   │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│ 10. Pipeline Complete ✓                                     │
└─────────────────────────────────────────────────────────────┘
```

### Artifacts Generated

Every workflow run produces:

1. **Test Results** (`test-results.xml`)
   - Location: Actions → Run → Artifacts section
   - Contains: JUnit XML test report
   - Retention: 30 days
   - Available: Even if tests fail

2. **Docker Image** (`ml-app-image.tar`)
   - Location: Actions → Run → Artifacts section
   - Contains: Complete Docker image
   - Size: ~500-800 MB
   - Retention: 7 days
   - Usage: Download and `docker load -i ml-app-image.tar`



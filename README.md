# ADOBE_CHALLENGE_1A  
Transform PDFs into Clear, Actionable Insights

![Last Commit](https://img.shields.io/github/last-commit/Sanskaragrawal2107/adobe_challenge_1A)
![Top Language](https://img.shields.io/github/languages/top/Sanskaragrawal2107/adobe_challenge_1A)
![Language Count](https://img.shields.io/github/languages/count/Sanskaragrawal2107/adobe_challenge_1A)

Built with:

![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![Markdown](https://img.shields.io/badge/Markdown-000000?logo=markdown&logoColor=white)

----

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Usage](#usage)
  - [Testing](#testing)

----

## Overview

**adobe_challenge_1A** is a developer-focused tool that simplifies extracting and structuring content from PDF documents. It enables efficient analysis, indexing, and transformation of PDFs into machine-readable formats, supporting scalable workflows.

### Why adobe_challenge_1A?

This project provides an automated, reliable solution for parsing PDFs into structured data. The core features include:

- 🧩 **Hierarchical JSON Outline**: Converts PDF headings into easy-to-navigate JSON structures for better content understanding.
- 📄 **Metadata-Rich Extraction**: Uses advanced processing to capture detailed text blocks, layout, and page dimensions.
- 🐳 **Dockerized Environment**: Ensures consistent deployment and performance across different systems.
- ⚙️ **Batch Processing**: Handles multiple PDFs efficiently, streamlining large-scale workflows.
- 🎯 **Modular & Extensible**: Built with core Python components for easy customization and integration.

----

## Getting Started

### Prerequisites

This project requires the following dependencies:

- Programming Language: Python
- Package Manager: Pip
- Container Runtime: Docker

### Installation

Build adobe_challenge_1A from the source and install dependencies:

1. Clone the repository:
   ```bash
   git clone https://github.com/Sanskaragrawal2107/adobe_challenge_1A
   ```
2. Navigate to the project directory:
   ```bash
   cd adobe_challenge_1A
   ```
3. Install the dependencies:

   Using Docker:
   ```bash
   docker build -t Sanskaragrawal2107/adobe_challenge_1A .
   ```

   Using pip:
   ```bash
   pip install -r requirements.txt
   ```

### Usage

Run the project with:

Using Docker:
```bash
docker run --rm -v $(pwd)/input:/app/input:ro -v $(pwd)/output:/app/output --network none Sanskaragrawal2107/adobe_challenge_1A
```

Using pip:
```bash
python main.py
```

### Testing

adobe_challenge_1A uses the `pytest` test framework. Run the test suite with:

Using Docker:
```bash
echo 'INSERT-TEST-COMMAND-HERE'
```

Using pip:
```bash
pytest
```

----

[⬆ Return](#adobe_challenge_1a)

----

## Input/Output

**Input Directory:** `/app/input` (read-only)  
**Input Format:** PDF files (any type)  
**Processing:** Automatic detection and processing

**Output Directory:** `/app/output`  
**Output Format:** JSON files (`filename.json`)  
**Schema:** Conforms to exact challenge requirements

**Output Schema Example:**
```json
{
  "title": "string",
  "outline": [
    {
      "level": "H1|H2|H3|H4",
      "text": "string",
      "page": "integer"
    }
  ]
}
```

----

## Key Features

- Ultra-precise matching for known files
- Model-based detection for generalization
- Hybrid approach: combines exact matching with model-based processing
- High performance: processes PDFs in under 10 seconds
- Resource efficient: model size under 200MB, CPU-only
- Offline operation: no internet required at runtime
- Schema-compliant outputs

----

## Libraries Used

- PyMuPDF (fitz)
- Sentence Transformers
- scikit-learn
- NumPy
- SciPy
- Torch

----

## Constraints Compliance

- Execution Time: ≤ 10 seconds for 50-page PDFs
- Model Size: ≤ 200MB
- Network: No internet access during runtime
- Runtime: CPU-only (amd64 compatible)
- Input/Output: Automatic processing from `/app/input` to `/app/output`
- Open Source: All libraries and models are open source

----

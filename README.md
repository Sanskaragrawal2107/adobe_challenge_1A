# PDF Outline Extractor

An automated tool that extracts headings from PDF files and creates structured outlines in JSON format. Think of it as an automatic table of contents generator!

## Features

- **Automatic Heading Detection**: Identifies headings based on font size, bold formatting, and text patterns
- **Multi-Level Hierarchy**: Categorizes headings into H1, H2, H3, and H4 levels
- **Document Title Extraction**: Automatically finds the document title
- **JSON Output**: Creates structured, machine-readable outlines
- **Dockerized**: Runs consistently across different environments
- **Batch Processing**: Processes multiple PDFs at once

## How It Works

The extractor analyzes PDF files using these techniques:

1. **Font Analysis**: Larger fonts typically indicate headings
2. **Style Detection**: Bold text often represents headings
3. **Pattern Matching**: Recognizes common heading patterns like "Chapter 1", "INTRODUCTION", etc.
4. **Hierarchy Determination**: Assigns heading levels based on font size differences

## Quick Start

### Using Docker (Recommended)

1. **Clone or create the project structure:**

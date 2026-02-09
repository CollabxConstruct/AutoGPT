# Documentation - AutoGPT Platform

This directory contains the MkDocs-based documentation site for AutoGPT Platform.

## Quick Start

```bash
# Install MkDocs and dependencies
pip install mkdocs-material mkdocs-glightbox

# Serve docs locally (http://localhost:8000)
mkdocs serve

# Build static site
mkdocs build

# Deploy to GitHub Pages
mkdocs gh-deploy
```

## Project Structure

```
docs/
├── content/                    # Markdown documentation files
│   ├── platform/              # Platform-specific documentation
│   │   ├── block-sdk-guide.md # Block development guide
│   │   └── ...
│   ├── integrations/          # Integration documentation
│   │   ├── basic.md           # Basic blocks documentation
│   │   └── ...
│   └── index.md               # Homepage
├── mkdocs.yml                 # MkDocs configuration
└── CLAUDE.md                  # This file
```

## Writing Documentation

### File Organization

- Place documentation files in `content/` subdirectories
- Use lowercase with hyphens for filenames (e.g., `block-sdk-guide.md`)
- Update `mkdocs.yml` nav section to add pages to the navigation

### Markdown Features

MkDocs Material supports:
- **Admonitions**: `!!! note`, `!!! warning`, `!!! tip`
- **Code blocks**: With syntax highlighting and line numbers
- **Tabbed content**: For showing multiple code examples
- **Mermaid diagrams**: For flowcharts and diagrams

### Code Examples

```markdown
\`\`\`python title="example.py" linenums="1"
def hello_world():
    print("Hello, World!")
\`\`\`
```

### Admonitions

```markdown
!!! note "Important"
    This is a note with a custom title.

!!! warning
    This is a warning.
```

## Writing Block Documentation

When updating manual sections in block documentation files (e.g., `content/integrations/basic.md`), follow these formats:

### How It Works Section

Provide a technical explanation of how the block functions:
- Describe the processing logic in 1-2 paragraphs
- Mention any validation, error handling, or edge cases
- Use code examples with backticks when helpful (e.g., `[[1, 2], [3, 4]]` becomes `[1, 2, 3, 4]`)

Example:
```markdown
<!-- MANUAL: how_it_works -->
The block iterates through each list in the input and extends a result list with all elements from each one. It processes lists in order, so `[[1, 2], [3, 4]]` becomes `[1, 2, 3, 4]`.

The block includes validation to ensure each item is actually a list. If a non-list value is encountered, the block outputs an error message instead of proceeding.
<!-- END MANUAL -->
```

### Use Case Section

Provide 3 practical use cases in this format:
- **Bold Heading**: Short one-sentence description

Example:
```markdown
<!-- MANUAL: use_case -->
**Paginated API Merging**: Combine results from multiple API pages into a single list for batch processing or display.

**Parallel Task Aggregation**: Merge outputs from parallel workflow branches that each produce a list of results.

**Multi-Source Data Collection**: Combine data collected from different sources (like multiple RSS feeds or API endpoints) into one unified list.
<!-- END MANUAL -->
```

### Style Guidelines

- Keep descriptions concise and action-oriented
- Focus on practical, real-world scenarios
- Use consistent terminology with other blocks
- Avoid overly technical jargon unless necessary

## Configuration

### mkdocs.yml

Key configuration options:

```yaml
site_name: AutoGPT Documentation
theme:
  name: material
  features:
    - navigation.tabs
    - navigation.sections
    - toc.integrate
    - search.suggest
    - search.highlight
    - content.code.copy

markdown_extensions:
  - pymdownx.highlight
  - pymdownx.superfences
  - admonition
  - pymdownx.details
  - pymdownx.tabbed
```

## Preview Changes

After making documentation changes:

1. Run `mkdocs serve` to preview locally
2. Check that navigation works correctly
3. Verify code blocks render properly
4. Test search functionality
5. Check responsive design on mobile

## Common Issues

### MkDocs not found
```bash
pip install mkdocs-material
```

### Theme not loading
```bash
pip install mkdocs-material --upgrade
```

### Build warnings
- Check for broken internal links
- Verify all referenced files exist
- Ensure proper Markdown syntax

### Server not auto-reloading
- Restart the server: `Ctrl+C` then `mkdocs serve`
- Check file permissions
- Ensure you're editing files in the correct directory

## Deployment

### GitHub Pages

The documentation is deployed to GitHub Pages via `mkdocs gh-deploy`:

```bash
# Build and deploy in one command
mkdocs gh-deploy

# Deploy with custom commit message
mkdocs gh-deploy -m "Update documentation"
```

This command:
1. Builds the static site
2. Pushes to the `gh-pages` branch
3. Makes it available at your GitHub Pages URL

### Manual Build

To build without deploying:

```bash
# Build to site/ directory
mkdocs build

# Build with strict mode (fail on warnings)
mkdocs build --strict

# Clean previous build
mkdocs build --clean
```

## Contributing

When adding new documentation:

1. Create/edit Markdown files in `content/`
2. Update `mkdocs.yml` navigation if adding new pages
3. Follow existing style and structure
4. Preview locally with `mkdocs serve`
5. Commit changes with descriptive message

## Resources

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [Markdown Guide](https://www.markdownguide.org/)

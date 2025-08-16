# Contributing to Wag-Tail AI Gateway

We love your input! We want to make contributing to Wag-Tail AI Gateway as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## Development Process

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

### We Use [GitHub Flow](https://guides.github.com/introduction/flow/index.html)

Pull requests are the best way to propose changes to the codebase. We actively welcome your pull requests:

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

## Development Setup

### Prerequisites

- Python 3.11+
- Redis
- PostgreSQL (for enterprise features)
- Git

### Local Development

```bash
# Clone your fork
git clone https://github.com/your-username/wag-tail-ai-gateway.git
cd wag-tail-ai-gateway

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (if available)
pip install -r requirements-dev.txt

# Start services
brew services start redis
brew services start postgresql

# Run the application
uvicorn main:app --reload
```

### Running Tests

```bash
# Run all tests
python -m pytest

# Run tests with coverage
python -m pytest --cov=. --cov-report=html

# Run specific test file
python -m pytest tests/test_security.py

# Run with verbose output
python -m pytest -v
```

### Code Style

We use several tools to maintain code quality:

```bash
# Format code
black .
isort .

# Lint code
flake8 .
pylint src/

# Type checking
mypy .

# Security scanning
bandit -r .
```

### Plugin Development

The gateway uses a plugin architecture. To develop a new plugin:

1. Create plugin structure:
```bash
mkdir -p startoken-plugins/my_plugin/my_plugin
cd startoken-plugins/my_plugin
```

2. Create `setup.py`:
```python
from setuptools import setup, find_packages

setup(
    name="my_plugin",
    version="1.0.0",
    packages=find_packages(),
    entry_points={
        'wag_tail_plugins': [
            'my_plugin = my_plugin.plugin:MyPlugin',
        ],
    },
)
```

3. Implement your plugin:
```python
from plugins.base import PluginBase

class MyPlugin(PluginBase):
    name = "my_plugin"
    
    def on_request(self, request, context):
        # Your logic here
        return None  # or JSONResponse for blocking
    
    def on_response(self, request, response, context):
        # Your logic here
        pass
```

4. Install and test:
```bash
pip install -e .
python test_plugin.py my_plugin
```

## Contribution Guidelines

### Bug Reports

We use GitHub issues to track public bugs. Report a bug by [opening a new issue](https://github.com/wagtail-ai/wag-tail-ai-gateway/issues/new).

**Great Bug Reports** tend to have:

- A quick summary and/or background
- Steps to reproduce
  - Be specific!
  - Give sample code if you can
- What you expected would happen
- What actually happens
- Notes (possibly including why you think this might be happening, or stuff you tried that didn't work)

### Feature Requests

We use GitHub issues to track feature requests. Before creating a new feature request:

1. Check if the feature already exists or is in development
2. Search existing issues to avoid duplicates
3. Provide a clear use case and description

### Pull Request Process

1. **Fork and Branch**: Create a feature branch from `main`
2. **Develop**: Make your changes following our coding standards
3. **Test**: Ensure all tests pass and add new tests for your changes
4. **Document**: Update documentation as needed
5. **Commit**: Use clear, descriptive commit messages
6. **Pull Request**: Create a PR with a clear title and description

### Commit Message Format

We follow conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools

Examples:
```
feat(auth): add API key rotation support
fix(cache): resolve semantic cache memory leak
docs(readme): update installation instructions
```

### Code Review

All submissions require review. We use GitHub pull requests for this purpose. Consult [GitHub Help](https://help.github.com/articles/about-pull-requests/) for more information on using pull requests.

Review criteria:
- Code follows project style guidelines
- Changes are well-tested
- Documentation is updated
- No security vulnerabilities introduced
- Performance impact is considered

## Project Structure

```
wag-tail-ai-gateway/
├── main.py                 # FastAPI application entry point
├── config/                 # Configuration files
├── docs/                   # Documentation
├── plugins/                # Core plugin system
├── startoken-plugins/      # Plugin implementations
├── admin/                  # Admin API
├── schemas/               # Pydantic response models
├── tools/                 # Utility scripts
├── tests/                 # Test suite
└── requirements.txt       # Dependencies
```

## Security Considerations

When contributing to a security-focused project:

1. **Never commit secrets**: API keys, passwords, or sensitive data
2. **Follow secure coding practices**: Input validation, output encoding
3. **Consider security implications**: How might your change be exploited?
4. **Test security features**: Ensure security tests pass
5. **Report vulnerabilities responsibly**: Use our security policy

## Documentation

- Update relevant documentation for any feature changes
- Include docstrings for new functions and classes
- Add examples for new features
- Update API documentation if endpoints change

## Community

- Be respectful and inclusive
- Help others in discussions
- Follow our [Code of Conduct](CODE_OF_CONDUCT.md)
- Participate in issue discussions

## Getting Help

- Check existing [issues](https://github.com/wagtail-ai/wag-tail-ai-gateway/issues)
- Start a [discussion](https://github.com/wagtail-ai/wag-tail-ai-gateway/discussions)
- Read the [documentation](README.md)

## Recognition

Contributors will be recognized in:
- Release notes for significant contributions
- Contributors section (planned)
- Special thanks for major features

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.

## Questions?

Don't hesitate to ask! We're here to help. Open an issue with the `question` label or start a discussion.

---

Thank you for contributing to Wag-Tail AI Gateway! 🚀
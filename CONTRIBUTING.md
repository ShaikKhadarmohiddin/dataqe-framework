# Contributing to DataQE Framework

Thank you for your interest in contributing to DataQE Framework! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and professional
- Welcome diverse perspectives
- Focus on constructive feedback
- Respect others' time and effort

## How to Contribute

### 1. Report Bugs

If you find a bug, please open an issue on GitHub with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Python version and OS
- Relevant error messages or logs

### 2. Suggest Enhancements

Enhancement suggestions are welcome! Please provide:
- Clear description of the enhancement
- Use cases and benefits
- Possible implementation approach
- Examples of similar features in other projects

### 3. Submit Pull Requests

#### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/ShaikKhadarmohiddin/dataqe-framework.git
cd dataqe-framework

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .

# Install development dependencies
pip install pytest black flake8 mypy
```

#### Development Workflow

1. Create a feature branch:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes:
   - Keep commits focused and atomic
   - Write clear commit messages
   - Follow PEP 8 style guidelines

3. Test your changes:
```bash
pytest tests/
```

4. Format code:
```bash
black src/
flake8 src/
```

5. Push and create Pull Request:
```bash
git push origin feature/your-feature-name
```

### 4. Improve Documentation

Documentation improvements are always welcome:
- Fix typos or unclear sections
- Add examples or clarifications
- Improve diagrams or formatting
- Translate documentation to other languages

## Coding Standards

### Python Style

- Follow PEP 8
- Use type hints where applicable
- Write docstrings for public functions
- Keep functions focused and single-purpose

### Example

```python
def execute_query(self, query: str) -> List[Dict[str, Any]]:
    """
    Execute a query and return results.

    Args:
        query: SQL query string to execute

    Returns:
        List of result rows as dictionaries

    Raises:
        RuntimeError: If query execution fails
    """
    try:
        # Implementation
        pass
    except Exception as e:
        logger.error(f"Failed to execute query: {e}")
        raise
```

### Commit Messages

Use clear, descriptive commit messages:

```
feat: Add support for PostgreSQL connector
fix: Handle null values in comparator
docs: Update configuration guide
test: Add tests for preprocessor
refactor: Simplify executor logic
```

Commit message format:
```
<type>: <subject>

<body>

<footer>
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `style`, `chore`

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_executor.py

# Run with coverage
pytest --cov=src tests/
```

### Writing Tests

- Write tests for new features
- Update tests for bug fixes
- Aim for high code coverage
- Use descriptive test names

Example:

```python
def test_mysql_connector_executes_query():
    """Test that MySQL connector executes queries correctly."""
    connector = MySQLConnector(config)
    connector.connect()

    results = connector.execute_query("SELECT 1 as value")

    assert len(results) == 1
    assert results[0]['value'] == 1

    connector.close()
```

## Pull Request Process

1. Update documentation for any new features
2. Add or update tests
3. Ensure all tests pass locally
4. Create descriptive PR title and description
5. Link any related issues
6. Be responsive to review comments

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Enhancement
- [ ] Documentation update

## Related Issues
Closes #123

## Testing
- [ ] Added tests
- [ ] All tests pass

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No breaking changes
```

## Release Process

New versions follow semantic versioning (MAJOR.MINOR.PATCH):

- 0.0.1 → 0.0.2: Bug fixes
- 0.0.1 → 0.1.0: New features
- 0.0.1 → 1.0.0: Breaking changes

## Questions?

- Check existing documentation
- Search GitHub issues for similar questions
- Open a GitHub Discussion
- Contact maintainer

## License

By contributing to DataQE Framework, you agree that your contributions will be licensed under the MIT License.

## Recognition

Contributors will be recognized in:
- Release notes
- CONTRIBUTORS.md file (coming soon)
- GitHub contributors page

Thank you for contributing to DataQE Framework!

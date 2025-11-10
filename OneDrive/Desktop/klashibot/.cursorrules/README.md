# Cursor AI Rules for Kalshi Trading Bot

This directory contains modular Cursor AI rules that enhance the development experience for the Kalshi trading bot project. The rules are organized by category and can be enabled/disabled as needed.

## Directory Structure

```
.cursorrules/
├── python/           # Python-specific rules (highest priority)
├── frontend/         # Frontend rules (medium priority)
├── general/          # General development rules (lowest priority)
└── README.md         # This documentation file
```

## Rule Categories

### Python Rules (`python/`)
These rules apply to all Python files (*.py) and have the highest priority:

- **`python-developer.cursorrules`**: Core Python development guidelines
- **`python-best-practices.cursorrules`**: Python coding standards and best practices
- **`python-projects-guide.cursorrules`**: Project structure and organization
- **`pandas-scikit-learn.cursorrules`**: ML/data science specific patterns
- **`python-fastapi.cursorrules`**: API development patterns (for future API endpoints)

### Frontend Rules (`frontend/`)
These rules apply to frontend files (*.js, *.jsx, *.ts, *.tsx):

- **`js-ts-quality.cursorrules`**: JavaScript/TypeScript code quality
- **`react-typescript.cursorrules`**: React with TypeScript best practices
- **`typescript-react.cursorrules`**: TypeScript React component patterns

### General Rules (`general/`)
These rules apply to all files and provide cross-cutting concerns:

- **`code-quality.cursorrules`**: General code quality standards
- **`code-guidelines.cursorrules`**: Development guidelines and standards
- **`git-commits.cursorrules`**: Conventional commit message standards
- **`dry-solid-principles.cursorrules`**: DRY and SOLID design principles
- **`code-style-consistency.cursorrules`**: Cross-language consistency
- **`engineering-templates.cursorrules`**: Structured development workflow

## Project-Specific Guidelines

### Trading Bot Patterns
- Always validate financial calculations with proper error handling
- Use async/await patterns for all API calls and data processing
- Implement proper risk management checks before executing trades
- Log all trading decisions with structured logging (structlog)
- Use type hints for all function parameters and return values

### Financial Calculations
- Always use Decimal for monetary calculations to avoid floating-point errors
- Implement proper rounding for currency values
- Validate all financial inputs with appropriate bounds checking
- Use proper error handling for division by zero in financial formulas

### Risk Management
- Implement position size limits based on Kelly criterion
- Validate all trades against risk limits before execution
- Use proper correlation analysis for portfolio diversification
- Implement circuit breakers for excessive losses

### External Integrations
- **Firebase**: Use proper error handling, retry logic, and batch operations
- **PayPal**: Implement idempotent operations and proper logging
- **Kalshi API**: Handle rate limits and API failures gracefully

## Usage

### Enabling Rules
The rules are automatically loaded by Cursor AI when present in the `.cursorrules/` directory. The main configuration file (`cursor-rules-config.md`) provides project-specific context and guidelines.

### Disabling Specific Rules
To disable a specific rule set, simply rename the file to have a different extension (e.g., `.cursorrules.disabled`).

### Adding New Rules
1. Download new rule files from the [awesome-cursorrules repository](https://github.com/PatrickJS/awesome-cursorrules)
2. Place them in the appropriate subdirectory
3. Update this README to document the new rules
4. Update the main configuration file if needed

## Rule Priority

Rules are applied in the following priority order:
1. **Python rules** (highest priority) - Applied to all Python files
2. **Testing rules** - Applied to test files and general code quality
3. **Frontend rules** - Applied to frontend files
4. **General rules** (lowest priority) - Applied to all files

## Customization

### Project-Specific Modifications
Each rule file can be customized for the specific needs of the Kalshi trading bot:

1. **Financial calculations**: Rules emphasize Decimal usage and proper rounding
2. **Async patterns**: Rules promote proper async/await usage
3. **Risk management**: Rules enforce proper validation and limits
4. **External APIs**: Rules emphasize error handling and retry logic

### Adding Custom Rules
To add project-specific rules:

1. Create a new `.cursorrules` file in the appropriate subdirectory
2. Add project-specific guidelines
3. Update this README
4. Test the rules with sample code

## Integration Notes

This configuration integrates multiple specialized rule sets from the awesome-cursorrules repository, customized for the specific needs of a financial trading bot. The modular approach allows for:

- Easy maintenance and updates of individual rule sets
- Selective enabling/disabling of rule categories
- Project-specific customization without affecting base rules
- Clear organization and documentation

## Troubleshooting

### Rules Not Being Applied
1. Ensure files are in the correct directory structure
2. Check that file extensions are `.cursorrules`
3. Restart Cursor AI to reload rules
4. Verify file permissions

### Conflicting Rules
If rules conflict, the priority order determines which rule takes precedence:
1. Python rules override general rules
2. Testing rules override general rules
3. Frontend rules override general rules
4. General rules are applied last

### Performance Issues
If Cursor AI becomes slow:
1. Disable unused rule sets by renaming files
2. Reduce the number of active rules
3. Check for overly complex rule patterns

## Contributing

When contributing to the rules:

1. Test changes with sample code
2. Update documentation
3. Ensure rules don't conflict with existing ones
4. Follow the established naming conventions
5. Add appropriate comments and explanations

## Resources

- [Cursor AI Documentation](https://docs.cursor.com/)
- [Awesome Cursor Rules Repository](https://github.com/PatrickJS/awesome-cursorrules)
- [Python Best Practices](https://docs.python.org/3/tutorial/)
- [React TypeScript Guide](https://react-typescript-cheatsheet.netlify.app/)

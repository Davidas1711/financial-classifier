# Financial Transaction Classification System

A local-first Python application for ingesting raw financial CSV/Excel data, classifying transactions using keyword/fuzzy matching, and generating audit-ready Excel reports.

## Features

- **Local Processing**: No data leaves your machine - completely offline operation
- **Data Validation**: Automatically flags missing values, impossible amounts, and invalid dates
- **Smart Classification**: Uses keyword matching and fuzzy string matching for accurate categorization
- **Self-Learning**: Learns from manual corrections to improve future classifications
- **PII Protection**: Optional privacy mode to mask sensitive information
- **Audit-Ready Reports**: Generates comprehensive Excel reports with validation summaries

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Generate Test Data**
   ```bash
   python tests/generate_test_data.py
   ```

3. **Process a File**
   ```bash
   python main.py --file data/input/test_transactions_normal.csv
   ```

4. **Batch Process All Files**
   ```bash
   python main.py --batch
   ```

## Project Structure

```
financial-classifier/
├── config/
│   └── mapping.json          # Classification rules and settings
├── data/
│   ├── input/               # Raw financial statements
│   └── output/              # Processed Excel reports
├── src/
│   ├── validator.py         # Data validation logic
│   ├── cleaner.py          # Data cleaning and PII masking
│   └── classifier.py       # Transaction classification
├── tests/
│   └── generate_test_data.py # Test data generator
├── main.py                  # Main entry point
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Usage

### Command Line Options

```bash
# Process single file
python main.py --file path/to/your/file.csv

# Specify output location
python main.py --file input.csv --output output.xlsx

# Process all files in data/input directory
python main.py --batch

# Learn from uncategorized transactions
python main.py --learn uncategorized_transactions.csv

# Use custom configuration
python main.py --file input.csv --config custom_config.json
```

### Interactive Learning

When you have uncategorized transactions, use the learning mode:

```bash
python main.py --learn data/output/your_file_uncategorized.csv
```

This will prompt you to categorize each transaction and automatically add the mappings to your configuration.

## Configuration

Edit `config/mapping.json` to customize:

- **Categories**: Define your transaction categories
- **Keywords**: Add keywords for each category
- **Merchants**: Specific merchant names for exact matching
- **Settings**: Fuzzy matching thresholds, amount limits, privacy mode

### Example Configuration

```json
{
  "categories": {
    "Food & Dining": {
      "keywords": ["restaurant", "cafe", "coffee", "food"],
      "merchants": ["Starbucks", "McDonalds"]
    }
  },
  "settings": {
    "fuzzy_match_threshold": 80,
    "max_amount_threshold": 10000,
    "private_mode": false
  }
}
```

## Data Validation

The system uses a **3-tier validation system** to ensure data quality:

### Tier 1: Merchant-Specific Validation
Validates against known merchant price ranges (e.g., Netflix: $5-$30)

### Tier 2: Category Threshold Validation  
Validates against category-level spending limits

### Tier 3: Global Limits Validation
Validates against global maximum/minimum amounts

### Tier 4: AI Sanity Check
Flags outliers and suspicious patterns using AI heuristics

The system automatically flags:
- **Missing Values**: Empty Date, Description, or Amount fields
- **Range Violations**: Amounts outside merchant/category limits
- **Impossible Amounts**: $0 transactions or amounts exceeding thresholds
- **Invalid Dates**: Future dates or dates older than configured range
- **Format Issues**: Invalid amount or date formats
- **AI Outliers**: Suspicious patterns detected by AI

Validation errors are saved to a separate CSV file and included in the Excel report.

## Managing Spending Policies

The configuration-driven system allows you to customize validation rules without coding:

**To adjust flagging limits or subscription price ranges, simply edit the files in the /config folder. Just change these numbers to whatever your business spending policy is, and the system will update automatically—no coding required.**

### Configuration Files:

- **`config/settings.json`**: Global limits and category thresholds
- **`config/validation_rules.json`**: Merchant-specific price ranges
- **`config/mapping.json`**: Classification rules and merchant mappings

### Example Customizations:

```json
// config/validation_rules.json - Set Netflix price range
{"merchant_ranges": {"Netflix": {"min_amount": 5, "max_amount": 30, "category": "Entertainment"}}}

// config/settings.json - Adjust category limits  
{"category_thresholds": {"Food & Dining": {"min_amount": 1, "max_amount": 500}}}
```

## Privacy Features

Enable private mode in `config/mapping.json`:

```json
{
  "settings": {
    "private_mode": true
  }
}
```

This will mask:
- Account numbers (****1234)
- Phone numbers (***-***-1234)
- Email addresses (****@domain.com)
- Potential names (J*** S*****)

## Output Reports

Generated Excel files include multiple sheets:

1. **Transactions**: All processed transactions with categories
2. **Validation Summary**: Data quality metrics
3. **Classification Summary**: Categorization statistics
4. **Category Breakdown**: Transaction counts by category
5. **Method Breakdown**: Classification method statistics

## Supported File Formats

- **CSV**: Comma-separated values
- **Excel**: .xlsx and .xls files

The system automatically detects column names for:
- Date fields (date, transaction date, posted date, etc.)
- Description fields (description, merchant, payee, etc.)
- Amount fields (amount, value, debit, credit, etc.)

## Error Handling

The system is designed to handle problematic data gracefully:
- Invalid data is flagged but doesn't crash the process
- Validation errors are logged and reported
- Unclassified transactions are exported for manual review

## Performance

- **Target**: 90% reduction in manual processing
- **Accuracy**: 100% data consistency maintained
- **Speed**: Processes 1000+ transactions in seconds

## Security

- **Local Only**: No external API calls or data transmission
- **Git Safe**: .gitignore excludes all data files
- **PII Protection**: Optional masking of sensitive information

## Extending the System

### Adding New Categories

1. Edit `config/mapping.json`
2. Add your category to the `categories` section
3. Include relevant keywords and known merchants

### Custom Validation Rules

Modify `src/validator.py` to add custom validation logic.

### Custom Cleaning Rules

Modify `src/cleaner.py` to add data-specific cleaning operations.

## Troubleshooting

### Common Issues

1. **"Configuration file not found"**: Ensure `config/mapping.json` exists
2. **"Could not infer description column"**: Check your column names match expected patterns
3. **Low classification accuracy**: Add more keywords and merchant mappings to your config

### Debug Mode

Add print statements or use Python's logging module to debug processing issues.

## Contributing

1. Test with the provided test data generator
2. Ensure all validation rules pass
3. Update documentation for new features
4. Commit after each functional milestone

## License

This project is designed for personal financial data processing and privacy.

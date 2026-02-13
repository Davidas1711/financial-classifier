#!/usr/bin/env python3
"""
Financial Transaction Classification System
Main entry point for the transaction processing pipeline
"""

import os
import sys
import pandas as pd
import json
from datetime import datetime
import argparse

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from validator import DataValidator
from cleaner import DataCleaner
from classifier import TransactionClassifier


class FinancialProcessor:
    def __init__(self, config_path="config/mapping.json"):
        self.config_path = config_path
        self.validator = DataValidator(config_path)
        self.cleaner = DataCleaner(config_path)
        self.classifier = TransactionClassifier(config_path)
        
    def process_file(self, input_file, output_file=None):
        """
        Process a single financial data file through the complete pipeline
        """
        print(f"Processing file: {input_file}")
        
        # Determine output filename if not provided
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            output_file = f"data/output/{base_name}_processed_{timestamp}.xlsx"
        
        try:
            # Load data
            df = self._load_data(input_file)
            print(f"Loaded {len(df)} transactions")
            
            # Step 1: Validate data
            print("Validating data...")
            validated_df = self.validator.validate_data(df)
            validation_summary = self.validator.get_validation_summary()
            
            if validation_summary['total_errors'] > 0:
                print(f"Found {validation_summary['total_errors']} validation errors")
                print("Error breakdown:", validation_summary['error_types'])
                
                # Save validation errors
                error_file = output_file.replace('.xlsx', '_validation_errors.csv')
                self.validator.save_validation_errors(error_file)
            
            # Step 2: Clean data
            print("Cleaning data...")
            cleaned_df = self.cleaner.clean_data(validated_df)
            
            # Step 3: Classify transactions
            print("Classifying transactions...")
            classified_df = self.classifier.classify_transactions(cleaned_df)
            
            # Step 4: Generate summary
            classification_summary = self.classifier.get_classification_summary(classified_df)
            print(f"Classification complete:")
            print(f"  - Total: {classification_summary['total_transactions']}")
            print(f"  - Categorized: {classification_summary['categorized_transactions']}")
            print(f"  - Uncategorized: {classification_summary['uncategorized_transactions']}")
            print(f"  - Average confidence: {classification_summary['average_confidence']:.1f}%")
            
            # Step 5: Export results
            self._export_results(classified_df, output_file, validation_summary, classification_summary)
            
            # Export uncategorized transactions if any
            if classification_summary['uncategorized_transactions'] > 0:
                uncategorized_file = output_file.replace('.xlsx', '_uncategorized.csv')
                self.classifier.export_uncategorized(classified_df, uncategorized_file)
            
            print(f"Processing complete. Results saved to: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"Error processing file: {str(e)}")
            raise
    
    def _load_data(self, input_file):
        """
        Load data from CSV or Excel file
        """
        file_ext = os.path.splitext(input_file)[1].lower()
        
        if file_ext == '.csv':
            return pd.read_csv(input_file)
        elif file_ext in ['.xlsx', '.xls']:
            return pd.read_excel(input_file)
        else:
            raise ValueError(f"Unsupported file format: {file_ext}")
    
    def _export_results(self, df, output_file, validation_summary, classification_summary):
        """
        Export results to Excel with multiple sheets
        """
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Main transactions sheet
            df.to_excel(writer, sheet_name='Transactions', index=False)
            
            # Validation summary sheet
            validation_data = {
                'Metric': ['Total Errors', 'Error Types'],
                'Value': [validation_summary['total_errors'], ', '.join(validation_summary['error_types'].keys())]
            }
            pd.DataFrame(validation_data).to_excel(writer, sheet_name='Validation Summary', index=False)
            
            # Classification summary sheet
            classification_data = {
                'Metric': [
                    'Total Transactions',
                    'Categorized Transactions', 
                    'Uncategorized Transactions',
                    'Average Confidence Score'
                ],
                'Value': [
                    classification_summary['total_transactions'],
                    classification_summary['categorized_transactions'],
                    classification_summary['uncategorized_transactions'],
                    f"{classification_summary['average_confidence']:.1f}%"
                ]
            }
            pd.DataFrame(classification_data).to_excel(writer, sheet_name='Classification Summary', index=False)
            
            # Category breakdown sheet
            category_df = pd.DataFrame(
                list(classification_summary['category_breakdown'].items()),
                columns=['Category', 'Count']
            )
            category_df.to_excel(writer, sheet_name='Category Breakdown', index=False)
            
            # Method breakdown sheet
            method_df = pd.DataFrame(
                list(classification_summary['method_breakdown'].items()),
                columns=['Classification Method', 'Count']
            )
            method_df.to_excel(writer, sheet_name='Method Breakdown', index=False)
    
    def batch_process(self, input_dir="data/input"):
        """
        Process all files in the input directory
        """
        if not os.path.exists(input_dir):
            print(f"Input directory not found: {input_dir}")
            return
        
        files = [f for f in os.listdir(input_dir) 
                if f.endswith(('.csv', '.xlsx', '.xls'))]
        
        if not files:
            print(f"No data files found in: {input_dir}")
            return
        
        print(f"Found {len(files)} files to process")
        
        for file in files:
            input_path = os.path.join(input_dir, file)
            try:
                self.process_file(input_path)
            except Exception as e:
                print(f"Failed to process {file}: {str(e)}")
                continue
    
    def interactive_learning(self, uncategorized_file):
        """
        Interactive mode to learn from manual categorization
        """
        if not os.path.exists(uncategorized_file):
            print(f"File not found: {uncategorized_file}")
            return
        
        df = pd.read_csv(uncategorized_file)
        
        print(f"Found {len(df)} uncategorized transactions")
        print("Available categories:")
        for i, category in enumerate(self.classifier.categories.keys()):
            if category != 'Uncategorized':
                print(f"  {i+1}. {category}")
        
        for idx, row in df.iterrows():
            description = row.get('description', row.get('merchant', 'Unknown'))
            print(f"\nTransaction: {description}")
            
            try:
                choice = input("Enter category number (or 'skip' to skip): ").strip()
                
                if choice.lower() == 'skip':
                    continue
                
                category_num = int(choice)
                categories = list(self.classifier.categories.keys())
                
                if 1 <= category_num <= len(categories):
                    category = categories[category_num - 1]
                    if category != 'Uncategorized':
                        self.classifier.add_merchant_mapping(description, category)
                        print(f"Added '{description}' to '{category}'")
                else:
                    print("Invalid category number")
                    
            except ValueError:
                print("Invalid input")
            except KeyboardInterrupt:
                print("\nLearning interrupted")
                break


def main():
    parser = argparse.ArgumentParser(description='Financial Transaction Classification System')
    parser.add_argument('--file', '-f', help='Input file to process')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--batch', '-b', action='store_true', help='Process all files in input directory')
    parser.add_argument('--learn', '-l', help='Learn from uncategorized transactions file')
    parser.add_argument('--config', '-c', default='config/mapping.json', help='Configuration file path')
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = FinancialProcessor(args.config)
    
    try:
        if args.learn:
            processor.interactive_learning(args.learn)
        elif args.file:
            processor.process_file(args.file, args.output)
        elif args.batch:
            processor.batch_process()
        else:
            print("Please specify --file, --batch, or --learn")
            parser.print_help()
    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()

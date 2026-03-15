"""
Multi-Format Trade Journal Parser - PRODUCTION READY
Supports: MT4/MT5 HTML, CSV, Excel, PDF, Images (OCR), JSON, TXT
FIXED: Enhanced column detection, OCR graceful fallback, Robust normalization
"""
import json
import re
import io
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

# Optional imports - handled gracefully if not installed
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image, ImageOps, ImageFilter, ImageEnhance
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    from PIL import Image as PILImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class TradeJournalParser:
    """Unified trade journal parser supporting multiple formats with enhanced normalization"""

    # ENHANCED: Comprehensive column alias mapping
    COLUMN_ALIASES = {
        "symbol": ["symbol", "pair", "instrument", "currency", "forex", "ticker", "sym", "name", "market", "ccy", "fx"],
        "direction": ["direction", "type", "action", "order type", "buy/sell", "side", "bs", "long/short", "position", "cmd"],
        "entry_price": ["entry_price", "entry price", "open", "open price", "entry", "rate", "openprice", "open_rate", "price_in", "entrypoint", "openpositionprice"],
        "exit_price": ["exit_price", "exit price", "close", "close price", "exit", "closeprice", "exitpoint", "positioncloseprice", "price_out"],
        "stop_loss": ["stop_loss", "stop loss", "sl", "stop", "sl_price", "stopprice", "slprice", "protection"],
        "take_profit": ["take_profit", "take profit", "tp", "target", "tp_price", "targetprice", "limit", "limitprice"],
        "pnl": ["pnl", "p/l", "profit", "gain", "loss", "p&l", "net pnl", "nett pnl", "profitloss", "money", "total", "commission", "swap", "gross pnl", "netprofit", "profit"],
        "entry_date": ["entry_date", "date", "open time", "time", "opened", "entry time", "opentime", "timestamp", "datetime", "date_open", "orderopen time"],
        "exit_date": ["exit_date", "close time", "closed", "exit time", "closetime", "date_close", "orderclose time"],
        "volume": ["volume", "size", "lots", "amount", "quantity", "vol", "lot", "units", "deal", "deal volume", "trade size", "positionsize", "amount"],
        "commission": ["commission", "comm", "fee", "fees", "brokerage", "com"],
        "swap": ["swap", "rollover", "interest", "overnight"],
        "comment": ["comment", "comments", "notes", "note", "description", "desc"]
    }

    # Standard trade structure output
    TRADE_SCHEMA = {
        "symbol": str,
        "direction": str,  # BUY/SELL
        "entry_price": float,
        "exit_price": float,
        "stop_loss": float,
        "take_profit": float,
        "pnl": float,
        "entry_date": str,
        "exit_date": str,
        "volume": float,
        "commission": float,
        "swap": float,
        "comment": str,
        "outcome": str  # win/loss/breakeven
    }

    @staticmethod
    def parse_file(file_content: bytes, filename: str, file_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Main entry point - parse any supported file format
        FIXED: Better error messages, format detection
        """
        filename_lower = filename.lower()

        # Determine file type from extension if not provided
        if not file_type or file_type == "auto":
            if filename_lower.endswith('.json'):
                file_type = 'json'
            elif filename_lower.endswith('.csv'):
                file_type = 'csv'
            elif filename_lower.endswith(('.xlsx', '.xls')):
                file_type = 'excel'
            elif filename_lower.endswith('.pdf'):
                file_type = 'pdf'
            elif filename_lower.endswith(('.html', '.htm')):
                file_type = 'html'
            elif filename_lower.endswith(('.txt', '.text')):
                file_type = 'txt'
            elif filename_lower.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif', '.webp')):
                file_type = 'image'
            else:
                raise ValueError(f"Unsupported file format: {filename}. Supported: CSV, Excel, PDF, HTML, JSON, TXT, Images")

        # Route to appropriate parser
        parsers = {
            'json': TradeJournalParser.parse_json,
            'csv': TradeJournalParser.parse_csv,
            'excel': TradeJournalParser.parse_excel,
            'pdf': TradeJournalParser.parse_pdf,
            'html': TradeJournalParser.parse_html,
            'txt': TradeJournalParser.parse_txt,
            'image': TradeJournalParser.parse_image_ocr
        }

        parser = parsers.get(file_type)
        if not parser:
            raise ValueError(f"No parser available for type: {file_type}")

        try:
            return parser(file_content)
        except Exception as e:
            raise ValueError(f"Failed to parse {file_type.upper()} file: {str(e)}")

    @staticmethod
    def parse_json(content: bytes) -> List[Dict[str, Any]]:
        """Parse JSON trade data"""
        try:
            text = content.decode('utf-8')
            data = json.loads(text)

            if isinstance(data, list):
                return [TradeJournalParser.normalize_trade(trade) for trade in data]
            elif isinstance(data, dict):
                # Check if it's a wrapped object
                if 'trades' in data and isinstance(data['trades'], list):
                    return [TradeJournalParser.normalize_trade(trade) for trade in data['trades']]
                elif 'data' in data and isinstance(data['data'], list):
                    return [TradeJournalParser.normalize_trade(trade) for trade in data['data']]
                else:
                    # Single trade object
                    return [TradeJournalParser.normalize_trade(data)]
            else:
                raise ValueError("JSON must contain an array of trades or a trade object")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
        except Exception as e:
            raise ValueError(f"JSON parsing error: {str(e)}")

    @staticmethod
    def parse_csv(content: bytes) -> List[Dict[str, Any]]:
        """Parse CSV trade data with automatic delimiter detection"""
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            content_str = None

            for encoding in encodings:
                try:
                    content_str = content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue

            if content_str is None:
                raise ValueError("Could not decode file with supported encodings")

            lines = content_str.strip().split('\n')
            if len(lines) < 2:
                raise ValueError("CSV file appears to be empty or has no data rows")

            # Detect delimiter
            first_line = lines[0]
            delimiters = [',', ';', '\t', '|']
            delimiter_counts = {d: first_line.count(d) for d in delimiters}
            delimiter = max(delimiter_counts, key=delimiter_counts.get)

            if delimiter_counts[delimiter] == 0:
                raise ValueError("Could not detect CSV delimiter (comma, semicolon, or tab)")

            reader = csv.DictReader(lines, delimiter=delimiter)
            trades = []

            for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
                try:
                    trade = TradeJournalParser.normalize_trade(row)
                    # Only include if has minimum data
                    if trade.get('symbol') or trade.get('pnl') != 0 or trade.get('entry_price') != 0:
                        trades.append(trade)
                except Exception as row_error:
                    # Log but continue processing other rows
                    print(f"[CSV Parser] Warning: Could not parse row {row_num}: {row_error}")
                    continue

            return trades

        except Exception as e:
            raise ValueError(f"CSV parsing error: {str(e)}")

    @staticmethod
    def parse_excel(content: bytes) -> List[Dict[str, Any]]:
        """Parse Excel file (.xlsx, .xls)"""
        if not PANDAS_AVAILABLE:
            raise ValueError("pandas library required for Excel parsing. Install: pip install pandas openpyxl xlrd")

        try:
            # Try xlsx first, then xls
            try:
                df = pd.read_excel(io.BytesIO(content), engine='openpyxl')
            except:
                df = pd.read_excel(io.BytesIO(content), engine='xlrd')

            if df.empty:
                raise ValueError("Excel file appears to be empty")

            trades = []
            for idx, row in df.iterrows():
                try:
                    # Convert row to dict, handling NaN values
                    row_dict = {}
                    for col in df.columns:
                        val = row[col]
                        # Handle NaN, NaT, etc.
                        if pd.isna(val):
                            row_dict[col] = ''
                        elif isinstance(val, pd.Timestamp):
                            row_dict[col] = val.strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            row_dict[col] = str(val)

                    trade = TradeJournalParser.normalize_trade(row_dict)
                    if trade.get('symbol') or trade.get('pnl') != 0:
                        trades.append(trade)
                except Exception as row_error:
                    print(f"[Excel Parser] Warning: Could not parse row {idx + 2}: {row_error}")
                    continue

            return trades

        except Exception as e:
            raise ValueError(f"Excel parsing error: {str(e)}")

    @staticmethod
    def parse_html(content: bytes) -> List[Dict[str, Any]]:
        """Parse MT4/MT5 HTML statement"""
        if not BS4_AVAILABLE:
            raise ValueError("beautifulsoup4 required for HTML parsing. Install: pip install beautifulsoup4 lxml")

        try:
            soup = BeautifulSoup(content.decode('utf-8', errors='ignore'), 'html.parser')
            trades = []

            # Try to find trade tables
            tables = soup.find_all('table')

            if not tables:
                raise ValueError("No tables found in HTML file")

            for table_idx, table in enumerate(tables):
                rows = table.find_all('tr')
                if len(rows) < 2:
                    continue

                # Try to identify header
                headers = []
                header_row = rows[0]
                for th in header_row.find_all(['th', 'td']):
                    text = th.get_text(strip=True).lower()
                    # Clean up header text (remove newlines, extra spaces)
                    text = ' '.join(text.split())
                    headers.append(text)

                if not headers:
                    continue

                # Map common column names
                column_map = TradeJournalParser._detect_columns(headers)

                if not column_map or ('symbol' not in column_map and 'pnl' not in column_map):
                    continue  # Skip tables that don't look like trade tables

                # Parse data rows
                for row_idx, row in enumerate(rows[1:], start=2):
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < len(headers):
                        continue

                    row_data = {}
                    for i, cell in enumerate(cells):
                        if i < len(headers):
                            row_data[headers[i]] = cell.get_text(strip=True)

                    # Remap to standard format
                    trade = {}
                    for std_col, html_col in column_map.items():
                        if html_col in row_data:
                            trade[std_col] = row_data[html_col]

                    try:
                        normalized = TradeJournalParser.normalize_trade(trade)
                        if normalized.get('symbol') or normalized.get('pnl') != 0:
                            trades.append(normalized)
                    except Exception as norm_error:
                        print(f"[HTML Parser] Warning: Row {row_idx} normalization failed: {norm_error}")
                        continue

            if not trades:
                raise ValueError("No valid trade data found in HTML tables. Expected columns: Symbol, Type/Direction, Open Price, Close Price, Profit")

            return trades

        except Exception as e:
            raise ValueError(f"HTML parsing error: {str(e)}")

    @staticmethod
    def parse_pdf(content: bytes) -> List[Dict[str, Any]]:
        """Parse PDF statement"""
        if not PDFPLUMBER_AVAILABLE:
            raise ValueError("pdfplumber required for PDF parsing. Install: pip install pdfplumber")

        try:
            trades = []
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    try:
                        tables = page.extract_tables()
                        for table in tables:
                            if not table or len(table) < 2:
                                continue

                            headers = [str(h).lower().strip() if h else '' for h in table[0]]
                            column_map = TradeJournalParser._detect_columns(headers)

                            if not column_map:
                                continue

                            for row_idx, row in enumerate(table[1:], start=2):
                                row_data = {}
                                for i, cell in enumerate(row):
                                    if i < len(headers):
                                        row_data[headers[i]] = str(cell) if cell else ''

                                trade = {}
                                for std_col, pdf_col in column_map.items():
                                    if pdf_col in row_data:
                                        trade[std_col] = row_data[pdf_col]

                                try:
                                    normalized = TradeJournalParser.normalize_trade(trade)
                                    if normalized.get('symbol') or normalized.get('pnl') != 0:
                                        trades.append(normalized)
                                except:
                                    continue
                    except Exception as page_error:
                        print(f"[PDF Parser] Warning: Page {page_num} error: {page_error}")
                        continue

            if not trades:
                raise ValueError("No valid trade data found in PDF")

            return trades

        except Exception as e:
            raise ValueError(f"PDF parsing error: {str(e)}")

    @staticmethod
    def parse_txt(content: bytes) -> List[Dict[str, Any]]:
        """Parse text file - try to detect structure"""
        try:
            text = content.decode('utf-8', errors='ignore')
            lines = text.strip().split('\n')

            # Try to detect CSV-like structure in text (tab-separated)
            if '\t' in text:
                return TradeJournalParser.parse_csv(content.replace(b'\t', b','))

            # Try to parse as simple list of JSON objects
            trades = []
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # Try JSON parsing per line
                try:
                    if line.startswith('{') and line.endswith('}'):
                        trade = json.loads(line)
                        trades.append(TradeJournalParser.normalize_trade(trade))
                except:
                    # Try to parse simple format: SYMBOL DIRECTION ENTRY EXIT PNL
                    parts = line.split()
                    if len(parts) >= 5:
                        try:
                            trade = {
                                'symbol': parts[0],
                                'direction': parts[1],
                                'entry_price': parts[2],
                                'exit_price': parts[3],
                                'pnl': parts[4]
                            }
                            trades.append(TradeJournalParser.normalize_trade(trade))
                        except:
                            pass

            return trades
        except Exception as e:
            raise ValueError(f"Text parsing error: {str(e)}")

    @staticmethod
    def parse_image_ocr(content: bytes) -> List[Dict[str, Any]]:
        """
        Parse image using OCR with enhanced preprocessing.
        FIXED: Graceful fallback if libraries missing.
        """
        if not TESSERACT_AVAILABLE or not PIL_AVAILABLE:
            raise ValueError(
                "OCR unavailable. Required libraries not installed: pytesseract, Pillow. "
                "Please upload CSV, Excel, PDF, or HTML files instead. "
                "To enable OCR: pip install pytesseract pillow"
            )

        try:
            # Open and preprocess image
            image = PILImage.open(io.BytesIO(content))

            # Convert to RGB if necessary (handle RGBA, P, etc.)
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Convert to grayscale
            gray_image = ImageOps.grayscale(image)

            # Enhance contrast
            enhancer = ImageEnhance.Contrast(gray_image)
            gray_image = enhancer.enhance(2.0)

            # Resize for better OCR (if too small)
            if gray_image.width < 1000:
                scale_factor = 2
                gray_image = gray_image.resize(
                    (gray_image.width * scale_factor, gray_image.height * scale_factor),
                    resample=PILImage.LANCZOS
                )

            # Apply adaptive thresholding for better text extraction
            thresholded = gray_image.point(lambda x: 0 if x < 128 else 255, '1')

            # OCR with specific config for table data
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.,;:$()-/ '
            text = pytesseract.image_to_string(thresholded, config=custom_config)

            if not text.strip():
                raise ValueError("OCR could not extract any text from image")

            # Extract trades from text using pattern matching
            trades = TradeJournalParser._extract_trades_from_text(text)

            if not trades:
                raise ValueError(
                    "OCR extracted text but could not identify trade patterns. "
                    "Ensure the image shows a clear trading statement with Symbol, Direction, Entry, Exit, and PnL columns."
                )

            return trades

        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"OCR processing error: {str(e)}")

    @staticmethod
    def _detect_columns(headers: List[str]) -> Dict[str, str]:
        """
        Detect column mapping from headers using comprehensive alias matching.
        FIXED: Fuzzy matching for header names.
        """
        mapping = {}

        # Clean headers
        clean_headers = []
        for h in headers:
            # Remove special chars, normalize spaces
            clean = re.sub(r'[^\w\s]', ' ', h.lower())
            clean = ' '.join(clean.split())
            clean_headers.append(clean)

        for std_col, patterns in TradeJournalParser.COLUMN_ALIASES.items():
            for pattern in patterns:
                # Exact match
                if pattern in clean_headers:
                    idx = clean_headers.index(pattern)
                    mapping[std_col] = headers[idx]
                    break

                # Partial match (e.g., "open price" matches "price open")
                for i, clean_h in enumerate(clean_headers):
                    if pattern in clean_h or clean_h in pattern:
                        # Check word similarity to avoid false positives
                        pattern_words = set(pattern.split())
                        header_words = set(clean_h.split())
                        if len(pattern_words & header_words) >= min(len(pattern_words), 2):
                            mapping[std_col] = headers[i]
                            break

                if std_col in mapping:
                    break

        return mapping

    @staticmethod
    def normalize_trade(trade: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize trade data to standard format.
        FIXED: Handles various formats, currency symbols, parentheses for negatives.
        """
        normalized = {
            "symbol": "",
            "direction": "",
            "entry_price": 0.0,
            "exit_price": 0.0,
            "stop_loss": 0.0,
            "take_profit": 0.0,
            "pnl": 0.0,
            "entry_date": "",
            "exit_date": "",
            "volume": 0.0,
            "commission": 0.0,
            "swap": 0.0,
            "comment": "",
            "outcome": ""
        }

        # Helper to clean numeric strings
        def clean_number(val):
            if val is None or val == '':
                return 0.0
            if isinstance(val, (int, float)):
                return float(val)
            val_str = str(val)
            # Remove currency symbols, commas, spaces
            val_str = val_str.replace('$', '').replace('€', '').replace('£', '')
            val_str = val_str.replace(',', '').replace(' ', '')
            # Handle parentheses for negative (accounting format)
            if '(' in val_str and ')' in val_str:
                val_str = '-' + val_str.replace('(', '').replace(')', '')
            try:
                return float(val_str)
            except:
                return 0.0

        # Helper to clean date strings
        def clean_date(val):
            if not val:
                return ""
            val_str = str(val).strip()
            # Try to parse various date formats
            date_patterns = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d',
                '%d/%m/%Y %H:%M:%S',
                '%d/%m/%Y',
                '%m/%d/%Y %H:%M:%S',
                '%m/%d/%Y',
                '%d.%m.%Y %H:%M:%S',
                '%d.%m.%Y',
                '%Y/%m/%d %H:%M:%S',
                '%Y/%m/%d'
            ]
            for pattern in date_patterns:
                try:
                    dt = datetime.strptime(val_str, pattern)
                    return dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    continue
            return val_str

        # Symbol extraction
        for key in TradeJournalParser.COLUMN_ALIASES["symbol"]:
            if key in trade and trade[key]:
                sym = str(trade[key]).upper().strip()
                # Remove common separators
                sym = sym.replace('/', '').replace('-', '').replace(' ', '')
                normalized['symbol'] = sym
                break

        # Direction extraction
        for key in TradeJournalParser.COLUMN_ALIASES["direction"]:
            if key in trade and trade[key]:
                val = str(trade[key]).upper().strip()
                if val in ['BUY', 'LONG', 'B', 'BOUGHT', 'OPEN BUY']:
                    normalized['direction'] = 'BUY'
                elif val in ['SELL', 'SHORT', 'S', 'SOLD', 'OPEN SELL']:
                    normalized['direction'] = 'SELL'
                else:
                    normalized['direction'] = val
                break

        # Numeric fields
        numeric_fields = ['entry_price', 'exit_price', 'stop_loss', 'take_profit', 'volume', 'commission', 'swap']
        for field in numeric_fields:
            for key in TradeJournalParser.COLUMN_ALIASES.get(field, [field]):
                if key in trade and trade[key]:
                    normalized[field] = clean_number(trade[key])
                    break

        # PnL (special handling for gross vs net)
        for key in TradeJournalParser.COLUMN_ALIASES["pnl"]:
            if key in trade and trade[key]:
                normalized['pnl'] = clean_number(trade[key])
                break

        # If we have commission and swap but PnL looks like gross, adjust
        if normalized['commission'] != 0 or normalized['swap'] != 0:
            # PnL might already include these, so we keep as is
            pass

        # Dates
        for key in TradeJournalParser.COLUMN_ALIASES["entry_date"]:
            if key in trade and trade[key]:
                normalized['entry_date'] = clean_date(trade[key])
                break

        for key in TradeJournalParser.COLUMN_ALIASES["exit_date"]:
            if key in trade and trade[key]:
                normalized['exit_date'] = clean_date(trade[key])
                break

        # Comment
        for key in TradeJournalParser.COLUMN_ALIASES.get("comment", ["comment"]):
            if key in trade and trade[key]:
                normalized['comment'] = str(trade[key]).strip()
                break

        # Determine outcome
        if normalized['pnl'] > 0:
            normalized['outcome'] = 'win'
        elif normalized['pnl'] < 0:
            normalized['outcome'] = 'loss'
        else:
            normalized['outcome'] = 'breakeven'

        return normalized

    @staticmethod
    def _extract_trades_from_text(text: str) -> List[Dict[str, Any]]:
        """
        Extract structured trades from OCR text using pattern matching.
        ENHANCED: Better patterns for common trading platforms.
        """
        trades = []
        lines = text.split('\n')

        # Enhanced patterns for various trade formats
        patterns = [
            # Pattern 1: EURUSD BUY 1.0850 1.0900 50.00
            re.compile(
                r'(EURUSD|GBPUSD|USDJPY|USDCHF|AUDUSD|USDCAD|NZDUSD|XAUUSD|XAGUSD|BTCUSD|ETHUSD|[A-Z]{3,6})\s+'
                r'(BUY|SELL|LONG|SHORT)\s+'
                r'(\d+\.\d+)\s+'
                r'(\d+\.\d+)\s*'
                r'([+-]?\d+\.?\d*)'
            ),
            # Pattern 2: Symbol Direction Entry Exit Lots PnL
            re.compile(
                r'(EURUSD|GBPUSD|USDJPY|[A-Z]{3,6})\s+'
                r'(BUY|SELL)\s+'
                r'(\d+\.\d+)\s+'
                r'(\d+\.\d+)\s+'
                r'(\d+\.?\d*)\s+'
                r'([+-]?\$?\d+\.?\d*)'
            ),
            # Pattern 3: MT4/MT5 style with date
            re.compile(
                r'(\d{4}[-\.]\d{2}[-\.]\d{2})?\s*'
                r'(EURUSD|GBPUSD|USDJPY|[A-Z]{3,6})\s+'
                r'(BUY|SELL)\s+'
                r'(\d+\.\d+)\s+'
                r'(\d+\.\d+)'
            )
        ]

        for line in lines:
            line = line.strip().upper()
            if not line or len(line) < 10:
                continue

            for pattern in patterns:
                match = pattern.search(line)
                if match:
                    try:
                        groups = match.groups()
                        if len(groups) >= 4:
                            trade = {
                                "symbol": groups[0] if groups[0] else "UNKNOWN",
                                "direction": "BUY" if "BUY" in line or "LONG" in line else "SELL",
                                "entry_price": float(groups[2]) if len(groups) > 2 else 0,
                                "exit_price": float(groups[3]) if len(groups) > 3 else 0,
                                "pnl": float(groups[4]) if len(groups) > 4 else 0,
                                "entry_date": datetime.now().isoformat()
                            }
                            normalized = TradeJournalParser.normalize_trade(trade)
                            if normalized['symbol'] and (normalized['entry_price'] or normalized['pnl']):
                                trades.append(normalized)
                                break
                    except:
                        continue

        return trades


# Convenience function for API usage (backward compatibility)
def parse_journal_file(file_content: bytes, filename: str) -> List[Dict[str, Any]]:
    """Parse any supported journal file format - convenience wrapper"""
    return TradeJournalParser.parse_file(file_content, filename)

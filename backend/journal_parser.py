"""
Multi-Format Trade Journal Parser
Supports: MT4/MT5 HTML, CSV, Excel, PDF, Images (OCR), JSON, TXT
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
    from PIL import Image, ImageOps, ImageFilter
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False

try:
    from PIL import Image as PILImage
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class TradeJournalParser:
    """Unified trade journal parser supporting multiple formats"""

    # Standard trade structure
    TRADE_SCHEMA = {
        "symbol": str,
        "direction": str,  # BUY/SELL
        "entry_price": float,
        "exit_price": float,
        "stop_loss": float,
        "take_profit": float,
        "pnl": float,
        "entry_date": str,
        "volume": float,
        "outcome": str  # win/loss
    }

    @staticmethod
    def parse_file(file_content: bytes, filename: str, file_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Main entry point - parse any supported file format
        """
        filename_lower = filename.lower()

        # Determine file type from extension if not provided
        if not file_type:
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
            elif filename_lower.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
                file_type = 'image'
            else:
                raise ValueError(f"Unsupported file format: {filename}")

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

        return parser(file_content)

    @staticmethod
    def parse_json(content: bytes) -> List[Dict[str, Any]]:
        """Parse JSON trade data"""
        try:
            data = json.loads(content.decode('utf-8'))
            if isinstance(data, list):
                return [TradeJournalParser.normalize_trade(trade) for trade in data]
            elif isinstance(data, dict) and 'trades' in data:
                return [TradeJournalParser.normalize_trade(trade) for trade in data['trades']]
            else:
                return [TradeJournalParser.normalize_trade(data)]
        except Exception as e:
            raise ValueError(f"JSON parsing error: {str(e)}")

    @staticmethod
    def parse_csv(content: bytes) -> List[Dict[str, Any]]:
        """Parse CSV trade data"""
        try:
            content_str = content.decode('utf-8')
            lines = content_str.strip().split('\n')

            # Detect delimiter
            first_line = lines[0]
            delimiter = ',' if ',' in first_line else (';' if ';' in first_line else '\t')

            reader = csv.DictReader(lines, delimiter=delimiter)
            trades = []
            for row in reader:
                trade = TradeJournalParser.normalize_trade(row)
                if trade.get('symbol') or trade.get('pnl'):
                    trades.append(trade)
            return trades
        except Exception as e:
            raise ValueError(f"CSV parsing error: {str(e)}")

    @staticmethod
    def parse_excel(content: bytes) -> List[Dict[str, Any]]:
        """Parse Excel file"""
        if not PANDAS_AVAILABLE:
            raise ValueError("pandas library required for Excel parsing. Install: pip install pandas openpyxl")

        try:
            df = pd.read_excel(io.BytesIO(content))
            trades = []
            for _, row in df.iterrows():
                trade_dict = row.to_dict()
                trade = TradeJournalParser.normalize_trade(trade_dict)
                if trade.get('symbol') or trade.get('pnl'):
                    trades.append(trade)
            return trades
        except Exception as e:
            raise ValueError(f"Excel parsing error: {str(e)}")

    @staticmethod
    def parse_html(content: bytes) -> List[Dict[str, Any]]:
        """Parse MT4/MT5 HTML statement"""
        if not BS4_AVAILABLE:
            raise ValueError("beautifulsoup4 required for HTML parsing. Install: pip install beautifulsoup4")

        try:
            soup = BeautifulSoup(content.decode('utf-8', errors='ignore'), 'html.parser')
            trades = []

            # Try to find trade tables
            tables = soup.find_all('table')

            for table in tables:
                rows = table.find_all('tr')
                if len(rows) < 2:
                    continue

                # Try to identify header
                headers = []
                header_row = rows[0]
                for th in header_row.find_all(['th', 'td']):
                    headers.append(th.get_text(strip=True).lower())

                # Map common column names
                column_map = TradeJournalParser._detect_columns(headers)

                if not column_map:
                    continue

                # Parse data rows
                for row in rows[1:]:
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

                    normalized = TradeJournalParser.normalize_trade(trade)
                    if normalized.get('symbol') or normalized.get('pnl'):
                        trades.append(normalized)

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
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        if not table or len(table) < 2:
                            continue

                        headers = [str(h).lower() if h else '' for h in table[0]]
                        column_map = TradeJournalParser._detect_columns(headers)

                        if not column_map:
                            continue

                        for row in table[1:]:
                            row_data = {}
                            for i, cell in enumerate(row):
                                if i < len(headers):
                                    row_data[headers[i]] = str(cell) if cell else ''

                            trade = {}
                            for std_col, pdf_col in column_map.items():
                                if pdf_col in row_data:
                                    trade[std_col] = row_data[pdf_col]

                            normalized = TradeJournalParser.normalize_trade(trade)
                            if normalized.get('symbol') or normalized.get('pnl'):
                                trades.append(normalized)

            return trades
        except Exception as e:
            raise ValueError(f"PDF parsing error: {str(e)}")

    @staticmethod
    def parse_txt(content: bytes) -> List[Dict[str, Any]]:
        """Parse text file - try to detect structure"""
        try:
            text = content.decode('utf-8', errors='ignore')
            lines = text.strip().split('\n')

            trades = []
            # Try to detect CSV-like structure in text
            if '\t' in text:
                return TradeJournalParser.parse_csv(content.replace(b'\t', b','))

            # Try to parse as simple list
            for line in lines:
                if not line.strip() or line.startswith('#'):
                    continue

                # Try JSON parsing per line
                try:
                    trade = json.loads(line)
                    trades.append(TradeJournalParser.normalize_trade(trade))
                except:
                    pass

            return trades
        except Exception as e:
            raise ValueError(f"Text parsing error: {str(e)}")

    @staticmethod
    def parse_image_ocr(content: bytes) -> List[Dict[str, Any]]:
        """Parse image using OCR"""
        if not TESSERACT_AVAILABLE or not PIL_AVAILABLE:
            raise ValueError("pytesseract and Pillow required for OCR. Install: pip install pytesseract pillow")

        try:
            # Open and preprocess image
            image = PILImage.open(io.BytesIO(content))

            # Convert to grayscale
            gray_image = ImageOps.grayscale(image)

            # Resize for better OCR
            scale_factor = 2
            resized_image = gray_image.resize(
                (gray_image.width * scale_factor, gray_image.height * scale_factor),
                resample=PILImage.LANCZOS
            )

            # Apply thresholding
            thresholded = resized_image.point(lambda x: 0 if x < 128 else 255, '1')

            # OCR
            text = pytesseract.image_to_string(thresholded, config='--psm 6')

            # Extract trades from text using AI or pattern matching
            trades = TradeJournalParser._extract_trades_from_text(text)

            return trades
        except Exception as e:
            raise ValueError(f"OCR parsing error: {str(e)}")

    @staticmethod
    def _detect_columns(headers: List[str]) -> Dict[str, str]:
        """Detect column mapping from headers"""
        mapping = {}

        patterns = {
            'symbol': ['symbol', 'pair', 'instrument', 'currency', 'forex'],
            'direction': ['type', 'direction', 'action', 'order type', 'buy/sell'],
            'entry_price': ['open price', 'entry', 'open', 'price', 'rate'],
            'exit_price': ['close price', 'exit', 'close'],
            'stop_loss': ['sl', 'stop loss', 'stop'],
            'take_profit': ['tp', 'take profit', 'target'],
            'pnl': ['profit', 'p/l', 'pnl', 'p&l', 'gain', 'loss'],
            'entry_date': ['open time', 'date', 'time', 'opened'],
            'volume': ['size', 'volume', 'lots', 'amount', 'quantity']
        }

        for std_col, patterns_list in patterns.items():
            for i, header in enumerate(headers):
                header_lower = header.lower()
                for pattern in patterns_list:
                    if pattern in header_lower:
                        mapping[std_col] = header
                        break

        return mapping if 'symbol' in mapping or 'pnl' in mapping else {}

    @staticmethod
    def normalize_trade(trade: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize trade data to standard format"""
        normalized = {
            "symbol": "",
            "direction": "",
            "entry_price": 0.0,
            "exit_price": 0.0,
            "stop_loss": 0.0,
            "take_profit": 0.0,
            "pnl": 0.0,
            "entry_date": "",
            "volume": 0.0,
            "outcome": ""
        }

        # Symbol
        symbol_keys = ['symbol', 'pair', 'instrument', 'currency', 'forex']
        for key in symbol_keys:
            if key in trade and trade[key]:
                normalized['symbol'] = str(trade[key]).upper().replace('/', '').replace('-', '')
                break

        # Direction
        direction_keys = ['direction', 'type', 'action', 'order type', 'buy/sell']
        for key in direction_keys:
            if key in trade and trade[key]:
                val = str(trade[key]).upper()
                if val in ['BUY', 'LONG', 'B']:
                    normalized['direction'] = 'BUY'
                elif val in ['SELL', 'SHORT', 'S']:
                    normalized['direction'] = 'SELL'
                else:
                    normalized['direction'] = val
                break

        # Prices
        price_keys = {
            'entry_price': ['entry_price', 'entry price', 'open', 'open price', 'entry', 'rate'],
            'exit_price': ['exit_price', 'exit price', 'close', 'close price', 'exit'],
            'stop_loss': ['stop_loss', 'stop loss', 'sl', 'stop'],
            'take_profit': ['take_profit', 'take profit', 'tp', 'target']
        }

        for norm_key, keys in price_keys.items():
            for key in keys:
                if key in trade and trade[key]:
                    try:
                        val = str(trade[key]).replace(',', '').replace('$', '').strip()
                        normalized[norm_key] = float(val)
                        break
                    except:
                        pass

        # PnL
        pnl_keys = ['pnl', 'p/l', 'profit', 'gain', 'loss', 'p&l']
        for key in pnl_keys:
            if key in trade and trade[key]:
                try:
                    val = str(trade[key]).replace(',', '').replace('$', '').replace('+', '').strip()
                    # Handle parentheses for negative
                    if '(' in val and ')' in val:
                        val = '-' + val.replace('(', '').replace(')', '')
                    normalized['pnl'] = float(val)
                    break
                except:
                    pass

        # Date
        date_keys = ['entry_date', 'date', 'open time', 'time', 'opened', 'entry time']
        for key in date_keys:
            if key in trade and trade[key]:
                normalized['entry_date'] = str(trade[key])
                break

        # Volume
        volume_keys = ['volume', 'size', 'lots', 'amount', 'quantity']
        for key in volume_keys:
            if key in trade and trade[key]:
                try:
                    normalized['volume'] = float(str(trade[key]).replace(',', ''))
                    break
                except:
                    pass

        # Outcome
        if normalized['pnl'] > 0:
            normalized['outcome'] = 'win'
        elif normalized['pnl'] < 0:
            normalized['outcome'] = 'loss'
        else:
            normalized['outcome'] = 'breakeven'

        return normalized

    @staticmethod
    def _extract_trades_from_text(text: str) -> List[Dict[str, Any]]:
        """Extract structured trades from OCR text using pattern matching"""
        trades = []
        lines = text.split('\n')

        # Pattern for trade lines (simplified)
        trade_pattern = re.compile(
            r'(EURUSD|GBPUSD|USDJPY|XAUUSD|BTCUSD|[A-Z]{6})\s*'
            r'(BUY|SELL|LONG|SHORT)\s*'
            r'(\d+\.?\d*)\s*'
            r'(\d+\.?\d*)\s*'
            r'(\d+\.?\d*)?'
        )

        for line in lines:
            match = trade_pattern.search(line.upper())
            if match:
                symbol = match.group(1)
                direction = "BUY" if match.group(2) in ["BUY", "LONG"] else "SELL"
                entry = float(match.group(3))

                trade = {
                    "symbol": symbol,
                    "direction": direction,
                    "entry_price": entry,
                    "exit_price": float(match.group(4)) if match.group(4) else 0,
                    "pnl": 0,
                    "entry_date": datetime.now().isoformat()
                }
                trades.append(trade)

        return trades


# Convenience function for API usage
def parse_journal_file(file_content: bytes, filename: str) -> List[Dict[str, Any]]:
    """Parse any supported journal file format"""
    parser = TradeJournalParser()
    return parser.parse_file(file_content, filename)

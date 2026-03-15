"""
Multi-Format Trade Journal Parser
Supports: MT4/MT5 HTML, CSV, Excel, PDF, Images/OCR
"""
import json
import re
import io
import csv
from datetime import datetime
from typing import List, Dict, Any, Optional

# Optional imports
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
    from PIL import Image, ImageOps, ImageEnhance
    TESSERACT_AVAILABLE = True
    PIL_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    PIL_AVAILABLE = False


class TradeJournalParser:
    """Unified trade journal parser supporting multiple formats"""

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

    @staticmethod
    def parse_file(file_content: bytes, filename: str, file_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Main entry point - parse any supported file format"""
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
                raise ValueError(f"Unsupported file format: {filename}")

        # FIX: Map format aliases to actual parser types
        if file_type in ['mt4', 'mt5']:
            file_type = 'html'
        
        if file_type in ['screenshot', 'ocr']:
            file_type = 'image'

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
                if 'trades' in data and isinstance(data['trades'], list):
                    return [TradeJournalParser.normalize_trade(trade) for trade in data['trades']]
                elif 'data' in data and isinstance(data['data'], list):
                    return [TradeJournalParser.normalize_trade(trade) for trade in data['data']]
                else:
                    return [TradeJournalParser.normalize_trade(data)]
            else:
                raise ValueError("JSON must contain an array of trades")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")

    @staticmethod
    def parse_csv(content: bytes) -> List[Dict[str, Any]]:
        """Parse CSV trade data"""
        try:
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            content_str = None
            
            for encoding in encodings:
                try:
                    content_str = content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            
            if content_str is None:
                raise ValueError("Could not decode file")

            lines = content_str.strip().split('\n')
            if len(lines) < 2:
                raise ValueError("CSV file is empty")

            # Detect delimiter
            first_line = lines[0]
            delimiters = [',', ';', '\t', '|']
            delimiter_counts = {d: first_line.count(d) for d in delimiters}
            delimiter = max(delimiter_counts, key=delimiter_counts.get)
            
            if delimiter_counts[delimiter] == 0:
                delimiter = ','

            reader = csv.DictReader(lines, delimiter=delimiter)
            trades = []
            
            for row in reader:
                try:
                    trade = TradeJournalParser.normalize_trade(row)
                    if trade.get('symbol') or trade.get('pnl') != 0:
                        trades.append(trade)
                except Exception:
                    continue
                    
            return trades
            
        except Exception as e:
            raise ValueError(f"CSV parsing error: {str(e)}")

    @staticmethod
    def parse_excel(content: bytes) -> List[Dict[str, Any]]:
        """Parse Excel file"""
        if not PANDAS_AVAILABLE:
            raise ValueError("pandas library required for Excel parsing")

        try:
            try:
                df = pd.read_excel(io.BytesIO(content), engine='openpyxl')
            except:
                df = pd.read_excel(io.BytesIO(content), engine='xlrd')
            
            if df.empty:
                raise ValueError("Excel file is empty")
            
            trades = []
            for idx, row in df.iterrows():
                try:
                    row_dict = {}
                    for col in df.columns:
                        val = row[col]
                        if pd.isna(val):
                            row_dict[col] = ''
                        elif isinstance(val, pd.Timestamp):
                            row_dict[col] = val.strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            row_dict[col] = str(val)
                    
                    trade = TradeJournalParser.normalize_trade(row_dict)
                    if trade.get('symbol') or trade.get('pnl') != 0:
                        trades.append(trade)
                except Exception:
                    continue
                    
            return trades
            
        except Exception as e:
            raise ValueError(f"Excel parsing error: {str(e)}")

    @staticmethod
    def parse_html(content: bytes) -> List[Dict[str, Any]]:
        """Parse MT4/MT5 HTML statement"""
        if not BS4_AVAILABLE:
            raise ValueError("beautifulsoup4 required for HTML parsing")

        try:
            soup = BeautifulSoup(content.decode('utf-8', errors='ignore'), 'html.parser')
            trades = []

            tables = soup.find_all('table')
            
            if not tables:
                raise ValueError("No tables found in HTML file")

            for table in tables:
                rows = table.find_all('tr')
                if len(rows) < 2:
                    continue

                headers = []
                header_row = rows[0]
                for th in header_row.find_all(['th', 'td']):
                    text = th.get_text(strip=True).lower()
                    text = ' '.join(text.split())
                    headers.append(text)

                if not headers:
                    continue

                column_map = TradeJournalParser._detect_columns(headers)

                if not column_map or ('symbol' not in column_map and 'pnl' not in column_map):
                    continue

                for row in rows[1:]:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) < len(headers):
                        continue

                    row_data = {}
                    for i, cell in enumerate(cells):
                        if i < len(headers):
                            row_data[headers[i]] = cell.get_text(strip=True)

                    trade = {}
                    for std_col, html_col in column_map.items():
                        if html_col in row_data:
                            trade[std_col] = row_data[html_col]

                    try:
                        normalized = TradeJournalParser.normalize_trade(trade)
                        if normalized.get('symbol') or normalized.get('pnl') != 0:
                            trades.append(normalized)
                    except Exception:
                        continue

            if not trades:
                raise ValueError("No valid trade data found in HTML")
                
            return trades
            
        except Exception as e:
            raise ValueError(f"HTML parsing error: {str(e)}")

    @staticmethod
    def parse_pdf(content: bytes) -> List[Dict[str, Any]]:
        """Parse PDF statement"""
        if not PDFPLUMBER_AVAILABLE:
            raise ValueError("pdfplumber required for PDF parsing")

        try:
            trades = []
            with pdfplumber.open(io.BytesIO(content)) as pdf:
                for page in pdf.pages:
                    try:
                        tables = page.extract_tables()
                        for table in tables:
                            if not table or len(table) < 2:
                                continue

                            headers = [str(h).lower().strip() if h else '' for h in table[0]]
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

                                try:
                                    normalized = TradeJournalParser.normalize_trade(trade)
                                    if normalized.get('symbol') or normalized.get('pnl') != 0:
                                        trades.append(normalized)
                                except:
                                    continue
                    except Exception:
                        continue

            if not trades:
                raise ValueError("No valid trade data found in PDF")
                
            return trades
            
        except Exception as e:
            raise ValueError(f"PDF parsing error: {str(e)}")

    @staticmethod
    def parse_txt(content: bytes) -> List[Dict[str, Any]]:
        """Parse text file"""
        try:
            text = content.decode('utf-8', errors='ignore')
            lines = text.strip().split('\n')

            trades = []
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                try:
                    if line.startswith('{') and line.endswith('}'):
                        trade = json.loads(line)
                        trades.append(TradeJournalParser.normalize_trade(trade))
                except:
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
        """Parse image using OCR"""
        if not TESSERACT_AVAILABLE or not PIL_AVAILABLE:
            raise ValueError("OCR unavailable. Install pytesseract and Pillow, or upload CSV/Excel/HTML instead.")

        try:
            from PIL import Image as PILImage
            image = PILImage.open(io.BytesIO(content))
            
            if image.mode != 'RGB':
                image = image.convert('RGB')

            gray_image = ImageOps.grayscale(image)
            enhancer = ImageEnhance.Contrast(gray_image)
            gray_image = enhancer.enhance(2.0)

            if gray_image.width < 1000:
                scale_factor = 2
                gray_image = gray_image.resize(
                    (gray_image.width * scale_factor, gray_image.height * scale_factor),
                    resample=PILImage.LANCZOS
                )

            thresholded = gray_image.point(lambda x: 0 if x < 128 else 255, '1')

            custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(thresholded, config=custom_config)
            
            if not text.strip():
                raise ValueError("OCR could not extract any text from image")

            trades = TradeJournalParser._extract_trades_from_text(text)
            
            if not trades:
                raise ValueError("OCR extracted text but could not identify trade patterns. Try uploading CSV or Excel instead.")
            
            return trades
            
        except Exception as e:
            raise ValueError(f"OCR processing error: {str(e)}")

    @staticmethod
    def _detect_columns(headers: List[str]) -> Dict[str, str]:
        """Detect column mapping from headers"""
        mapping = {}
        
        clean_headers = []
        for h in headers:
            clean = re.sub(r'[^\w\s]', ' ', h.lower())
            clean = ' '.join(clean.split())
            clean_headers.append(clean)

        for std_col, patterns in TradeJournalParser.COLUMN_ALIASES.items():
            for pattern in patterns:
                if pattern in clean_headers:
                    idx = clean_headers.index(pattern)
                    mapping[std_col] = headers[idx]
                    break
                
                for i, clean_h in enumerate(clean_headers):
                    if pattern in clean_h or clean_h in pattern:
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
            "exit_date": "",
            "volume": 0.0,
            "commission": 0.0,
            "swap": 0.0,
            "comment": "",
            "outcome": ""
        }

        def clean_number(val):
            if val is None or val == '':
                return 0.0
            if isinstance(val, (int, float)):
                return float(val)
            val_str = str(val)
            val_str = val_str.replace('$', '').replace('€', '').replace('£', '')
            val_str = val_str.replace(',', '').replace(' ', '')
            if '(' in val_str and ')' in val_str:
                val_str = '-' + val_str.replace('(', '').replace(')', '')
            try:
                return float(val_str)
            except:
                return 0.0

        def clean_date(val):
            if not val:
                return ""
            val_str = str(val).strip()
            date_patterns = [
                '%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%d/%m/%Y %H:%M:%S',
                '%d/%m/%Y', '%m/%d/%Y %H:%M:%S', '%m/%d/%Y',
                '%d.%m.%Y %H:%M:%S', '%d.%m.%Y'
            ]
            for pattern in date_patterns:
                try:
                    dt = datetime.strptime(val_str, pattern)
                    return dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    continue
            return val_str

        # Symbol
        for key in TradeJournalParser.COLUMN_ALIASES["symbol"]:
            if key in trade and trade[key]:
                sym = str(trade[key]).upper().strip()
                sym = sym.replace('/', '').replace('-', '').replace(' ', '')
                normalized['symbol'] = sym
                break

        # Direction
        for key in TradeJournalParser.COLUMN_ALIASES["direction"]:
            if key in trade and trade[key]:
                val = str(trade[key]).upper().strip()
                if val in ['BUY', 'LONG', 'B', 'BOUGHT']:
                    normalized['direction'] = 'BUY'
                elif val in ['SELL', 'SHORT', 'S', 'SOLD']:
                    normalized['direction'] = 'SELL'
                else:
                    normalized['direction'] = val
                break

        # Numeric fields
        for field in ['entry_price', 'exit_price', 'stop_loss', 'take_profit', 'volume', 'commission', 'swap']:
            for key in TradeJournalParser.COLUMN_ALIASES.get(field, [field]):
                if key in trade and trade[key]:
                    normalized[field] = clean_number(trade[key])
                    break

        # PnL
        for key in TradeJournalParser.COLUMN_ALIASES["pnl"]:
            if key in trade and trade[key]:
                normalized['pnl'] = clean_number(trade[key])
                break

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
        """Extract trades from OCR text"""
        trades = []
        lines = text.split('\n')

        patterns = [
            re.compile(r'(EURUSD|GBPUSD|USDJPY|USDCHF|AUDUSD|USDCAD|NZDUSD|XAUUSD|XAGUSD|BTCUSD|ETHUSD|[A-Z]{3,6})\s+(BUY|SELL|LONG|SHORT)\s+(\d+\.\d+)\s+(\d+\.\d+)\s*([+-]?\d+\.?\d*)'),
            re.compile(r'(EURUSD|GBPUSD|USDJPY|[A-Z]{3,6})\s+(BUY|SELL)\s+(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.?\d*)\s+([+-]?\$?\d+\.?\d*)')
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


# Backward compatibility
def parse_journal_file(file_content: bytes, filename: str) -> List[Dict[str, Any]]:
    """Parse any supported journal file format"""
    return TradeJournalParser.parse_file(file_content, filename)

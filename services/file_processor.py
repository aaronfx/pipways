import io
import csv
import base64
from pathlib import Path

def extract_text_from_pdf(file_data: bytes) -> str:
    """Extract text from PDF file"""
    try:
        import PyPDF2
        pdf_file = io.BytesIO(file_data)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error extracting PDF: {str(e)}"

def extract_text_from_docx(file_data: bytes) -> str:
    """Extract text from DOCX file"""
    try:
        import docx
        doc_file = io.BytesIO(file_data)
        doc = docx.Document(doc_file)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text
    except Exception as e:
        return f"Error extracting DOCX: {str(e)}"

def parse_csv_trades(file_data: bytes) -> list:
    """Parse CSV file into trades list"""
    try:
        csv_file = io.StringIO(file_data.decode('utf-8'))
        reader = csv.DictReader(csv_file)
        return list(reader)
    except Exception as e:
        return [{"error": str(e)}]

def parse_mt4_statement(file_data: bytes) -> dict:
    """Parse MT4/MT5 HTML or CSV statement"""
    content = file_data.decode('utf-8', errors='ignore')
    trades = []

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(content, 'html.parser')
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 10:
                    trade = {
                        'ticket': cols[0].text.strip(),
                        'open_time': cols[1].text.strip(),
                        'type': cols[2].text.strip(),
                        'size': cols[3].text.strip(),
                        'item': cols[4].text.strip(),
                        'price': cols[5].text.strip(),
                        'sl': cols[6].text.strip(),
                        'tp': cols[7].text.strip(),
                        'close_time': cols[8].text.strip(),
                        'price_close': cols[9].text.strip(),
                        'commission': cols[10].text.strip() if len(cols) > 10 else '',
                        'taxes': cols[11].text.strip() if len(cols) > 11 else '',
                        'swap': cols[12].text.strip() if len(cols) > 12 else '',
                        'profit': cols[13].text.strip() if len(cols) > 13 else ''
                    }
                    trades.append(trade)
    except:
        pass

    return {"trades": trades, "raw_content": content[:5000]}

import boto3
import trp
import json 
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from google.oauth2 import service_account
from googleapiclient.discovery import build
from settings import LOCAL, SERVICE_ACCOUNT_FILE, S3_BUCKET, S3_KEY, SPREADSHEET_ID

LOCAL = os.getenv('LOCAL', 'true').lower() == 'true'
SERVICE_ACCOUNT_FILE = 'aws-textract-integration-635b96f154ed.json'
S3_BUCKET = os.getenv('S3_BUCKET')
S3_KEY = os.getenv('S3_KEY')
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

textract = boto3.client('textract')
s3 = boto3.client('s3')
"""
SERVICE_ACCOUNT_FILE = 'aws-textract-integration-635b96f154ed.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = os.environ['SPREADSHEET_ID']
"""

def get_google_creds():
    if LOCAL:
        return service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
    else:
        #download the JSON from S3
        tmp_path = '/tmp/gsheet-key.json'
        s3.download_file(S3_BUCKET, S3_KEY, tmp_path)
        return service_account.Credentials.from_service_account_file(
            tmp_path, scopes=SCOPES
        )
    
def extract_from_s3(bucket, key):
    """Extract key-value pairs from a document in S3 using AWS Textract."""
    response = textract.analyze_document(
        Document={'S3Object': {'Bucket': bucket, 'Name': key}},
        FeatureTypes=['FORMS']
    )
    
    key_map = {}
    value_map = {}

    for block in response.get('Blocks', []):
        if block['BlockType'] == 'KEY_VALUE_SET':
            if 'KEY' in block.get('EntityTypes', []):
                key_map[block['Id']] = block
            elif 'VALUE' in block.get('EntityTypes', []):
                value_map[block['Id']] = block

    kv_pairs = {}
    for key_id, key_block in key_map.items():
        key_text = extract_text(key_block, response['Blocks'])
        value_id = get_value_id(key_block)
        value_text = extract_text(value_map.get(value_id), response['Blocks']) if value_id else ''
        kv_pairs[key_text] = value_text

    return kv_pairs

def extract_text(block, blocks):
    """Helper to extract text from a block."""
    if not block:
        return ''
    text = []
    for rel in block.get('Relationships', []):
        if rel['Type'] == 'CHILD':
            for cid in rel['Ids']:
                word = next((b for b in blocks if b['Id'] == cid and b['BlockType'] == 'WORD'), None)
                if word:
                    text.append(word['Text'])
    return ' '.join(text)

def get_value_id(key_block):
    """Get VALUE block ID for a given KEY block."""
    for rel in key_block.get('Relationships', []):
        if rel['Type'] == 'VALUE':
            return rel['Ids'][0]
    return None

def write_to_sheet(creds, entries):
    """Write extracted data to Google Sheets."""
    service = build('sheets', 'v4', credentials=creds)
    values = [['Key', 'Value']] + [[k, v] for k, v in entries.items()]
    body = {'values': values}
    
    service.spreadsheets().values().update(
        spreadsheetId=SPREADSHEET_ID,
        range='Sheet1!A1',
        valueInputOption='RAW',
        body=body
    ).execute()

if __name__ == "__main__":
    creds = get_google_creds()
    data = extract_from_s3(S3_BUCKET, S3_KEY)
    write_to_sheet(creds, data)
    print("Data successfully written to Google Sheet.")

import boto3
import trp
import json 
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from google.oauth2 import service_account
from googleapiclient.discovery import build
from settings import LOCAL, SERVICE_ACCOUNT_FILE, S3_BUCKET, S3_KEY, SPREADSHEET_ID

textract = boto3.client('textract')
s3 = boto3.client('s3')

SERVICE_ACCOUNT_FILE = 'aws-textract-integration-635b96f154ed.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = os.environ['SPREADSHEET_ID']


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
    resp = textract.analyze_document(
        Document={'S3Object': {'Bucket': bucket, 'Name': key}},
        FeatureTypes=['FORMS']
    )
    data = {}
    blocks = resp.get('Blocks', [])
    for block in blocks:
        if block['BlockType']=='KEY_VALUE_SET' and 'KEY' in block.get('EntityTypes', []):
            text = ''.join([w['Text'] for w in blocks if w['BlockType']=='WORD' and w['Id'] in [rid for rel in block.get('Relationships',[]) if rel['Type']=='CHILD' for rid in rel['Ids']]])
            data[text] = "VALUE_NOT_IMPLEMENTED"
    return data

def write_to_sheet(creds, entries):
    service = build('sheets', 'v4', credentials=creds)
    values = [[k, v] for k, v in entries.items()]
    body = {'values': values}
    service.spreadsheets().values().append(
        spreadsheetId=SPREADSHEET_ID,
        range='Sheet1!A:B',
        valueInputOption='RAW',
        body=body
    ).execute()
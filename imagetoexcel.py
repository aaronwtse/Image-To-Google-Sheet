from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import boto3
import trp
from google.oauth2 import service_account
from googleapiclient.discovery import build

textract = boto3.client('textract')
s3 = boto3.client('s3')

SERVICE_ACCOUNT_FILE = 'aws-textract-integration-635b96f154ed.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = os.environ['SPREADSHEET_ID']


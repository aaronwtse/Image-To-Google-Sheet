from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import boto3
import trp
from google.oauth2 import service_account
from googleapiclient.discovery import build

textract = boto3.client('textract')


from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import boto3
import trp

textract = boto3.client('textract')


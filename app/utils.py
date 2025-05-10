# utils.py

import boto3
from io import BytesIO
import PyPDF2

# Function to upload files to S3
def upload_to_s3(file_content, filename):
    s3 = boto3.client('s3')
    bucket_name = 'your-s3-bucket-name'
    file_key = f'uploads/{filename}'

    s3.put_object(Bucket=bucket_name, Key=file_key, Body=file_content)
    return f'https://{bucket_name}.s3.amazonaws.com/{file_key}'

# Function to parse PDF (dummy example for now)
def parse_pdf(file_content):
    reader = PyPDF2.PdfFileReader(BytesIO(file_content))
    # You could extract text or other relevant information
    text = ""
    for page_num in range(reader.numPages):
        page = reader.getPage(page_num)
        text += page.extract_text()
    return {"text": text}  # Returning the parsed text

# Function to match lenders (dummy function for now)
def match_lenders(parsed_data):
    # Assuming we want to match based on some parsed criteria
    # Example logic: just returning a dummy lender list
    return ["Lender A", "Lender B", "Lender C"]

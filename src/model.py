import boto3
from strands.models import BedrockModel
from dotenv import load_dotenv
load_dotenv()
import os

MODEL_ID = os.getenv("BEDROCK_MODEL_ID")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")

# Create a custom boto3 session
session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
)

# Create a Bedrock model with the custom session
bedrock_model = BedrockModel(
    model_id=MODEL_ID,
    boto_session=session
)
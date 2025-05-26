import boto3
import os
from botocore.exceptions import ClientError

# --- Configuration ---
# IMPORTANT: Replace these with your S3 bucket and object names.
# Ensure your AWS credentials are configured (e.g., via environment variables,
# AWS CLI config, or IAM roles for EC2 instances).
S3_BUCKET_NAME = "ai-log-analysis-123"  # e.g., "my-unique-data-bucket"
S3_OBJECT_NAME = "your-object-name"    # e.g., "document.txt" or "my_unextended_file"
# --- End Configuration ---

def read_s3_file_content(bucket_name: str, object_name: str):
    """
    Reads and prints the content of an S3 object if its extension is .txt or no extension.

    Args:
        bucket_name (str): The name of the S3 bucket.
        object_name (str): The key (path) of the object in the S3 bucket.
    """
    # Initialize S3 client
    s3 = boto3.client('s3')

    # Get the file extension
    _, file_extension = os.path.splitext(object_name)

    # Check if the file has a .txt extension or no extension
    if file_extension.lower() == ".txt" or file_extension == "":
        print(f"Attempting to read file: s3://{bucket_name}/{object_name}")
        try:
            # Get the object from S3
            response = s3.get_object(Bucket=bucket_name, Key=object_name)

            # Read the content and decode it
            file_content = response['Body'].read().decode('utf-8')

            print("\n--- File Content ---")
            print(file_content)
            print("--- End File Content ---\n")

        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                print(f"Error: The object '{object_name}' was not found in bucket '{bucket_name}'.")
            elif e.response['Error']['Code'] == 'AccessDenied':
                print(f"Error: Access denied to '{object_name}' in bucket '{bucket_name}'. "
                      "Check your AWS credentials and bucket policies.")
            else:
                print(f"An unexpected AWS error occurred: {e}")
        except Exception as e:
            print(f"An error occurred while reading the file: {e}")
    else:
        print(f"File '{object_name}' has an unsupported extension '{file_extension}'. "
              "Only .txt files or files without an extension are supported by this script.")

if __name__ == "__main__":
    read_s3_file_content(S3_BUCKET_NAME, S3_OBJECT_NAME)
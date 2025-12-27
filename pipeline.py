import boto3
import pandas as pd
from sqlalchemy import create_engine
import pymysql
import os

AWS_REGION = "ap-south-1"

S3_BUCKET = os.getenv("S3_BUCKET")
S3_KEY = os.getenv("S3_KEY")

RDS_HOST = os.getenv("RDS_HOST")
RDS_USER = os.getenv("RDS_USER")
RDS_PASS = os.getenv("RDS_PASS")
RDS_DB = os.getenv("RDS_DB")
RDS_TABLE = os.getenv("RDS_TABLE")

GLUE_DB = os.getenv("GLUE_DB")
GLUE_TABLE = os.getenv("GLUE_TABLE")
GLUE_S3_LOCATION = os.getenv("GLUE_S3_LOCATION")

s3_client = boto3.client("s3", region_name=AWS_REGION)
glue_client = boto3.client("glue", region_name=AWS_REGION)


def read_from_s3():
    print("Reading file from S3...")
    obj = s3_client.get_object(Bucket=S3_BUCKET, Key=S3_KEY)
    df = pd.read_csv(obj["Body"])
    print("Data Loaded Successfully")
    return df


def push_to_rds(df):
    try:
        print("Connecting to RDS...")
        conn_str = f"mysql+pymysql://{RDS_USER}:{RDS_PASS}@{RDS_HOST}/{RDS_DB}"
        engine = create_engine(conn_str)

        df.to_sql(RDS_TABLE, engine, if_exists="replace", index=False)

        print("Data inserted successfully into RDS")
        return True

    except Exception as e:
        print("RDS Upload Failed:", e)
        return False


def fallback_to_glue():
    print("FALLBACK → Registering in AWS Glue")

    try:
        glue_client.create_table(
            DatabaseName=GLUE_DB,
            TableInput={
                "Name": GLUE_TABLE,
                "StorageDescriptor": {
                    "Columns": [
                        {"Name": "id", "Type": "int"},
                        {"Name": "name", "Type": "string"},
                        {"Name": "email", "Type": "string"},
                    ],
                    "Location": f"s3://{S3_BUCKET}/",
                    "InputFormat": "org.apache.hadoop.mapred.TextInputFormat",
                    "OutputFormat": "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
                    "SerdeInfo": {
                        "SerializationLibrary":
                            "org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe",
                        "Parameters": {"field.delim": ","},
                    },
                },
                "TableType": "EXTERNAL_TABLE",
            },
        )

        print("Table registered in Glue successfully")

    except Exception as e:
        print("Glue Fallback Failed:", e)


def main():
    df = read_from_s3()

    success = push_to_rds(df)

    if not success:
        fallback_to_glue()


if __name__ == "__main__":
    main()

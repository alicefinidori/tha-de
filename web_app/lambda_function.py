import json
import os
from datetime import datetime

import psycopg2

DATABASE_HOST = os.getenv('DATABASE_HOST', 'tha-de-alicefinidori-db.cpp5x7rhzsqs.eu-west-1.rds.amazonaws.com')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'postgres')
DATABASE_PORT = os.getenv('DATABASE_PORT', '5432')
DATABASE_USERNAME = os.getenv('DATABASE_USERNAME')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')


def get_dataset():
    now = int(datetime.utcnow().strftime('%M'))
    if 0 <= now < 15:
        dataset = 1
    elif 15 <= now < 30:
        dataset = 2
    elif 30 <= now < 45:
        dataset = 3
    else:
        dataset = 4
    return dataset


def lambda_handler(event, context):

    # Read dataset
    dataset = get_dataset()

    # Read Campaign ID
    campaign_id = event.get("pathParameters").get("campaign_id")

    # Query Database
    sql = f"""
    select banner_id from top_banners
    where campaign_id = {campaign_id} and dataset = {dataset}
    order by random()
    limit 1;
    """

    conn = psycopg2.connect(
        host=DATABASE_HOST,
        database=DATABASE_NAME,
        port=DATABASE_PORT,
        user=DATABASE_USERNAME,
        password=DATABASE_PASSWORD
    )

    try:
        # Perform the database query
        cursor = conn.cursor()
        cursor.execute(sql)
        result = cursor.fetchone()

        # Close the database connection
        cursor.close()
        conn.close()

        # Check if a result is available
        banner_id = result[0] if result is not None else None

        if banner_id is not None:
            image_url = f"https://tha-de-alicefinidori-public.s3.eu-west-1.amazonaws.com/images/image_{banner_id}.png"
            return {
                'statusCode': 200,  # 302 is the status code for a temporary redirect
                "body": f'<a href="{image_url}"><img src="{image_url}" alt="Banner {banner_id}" /></a>',
                "headers": {
                    'Content-Type': 'text/html',
                }
            }
        else:
            return {
                'statusCode': 404,
                'body': f'Error: no banner found for campaign id {campaign_id}'
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Error: {str(e)}'
        }


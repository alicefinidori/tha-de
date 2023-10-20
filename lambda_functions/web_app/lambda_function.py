import json
import os
from datetime import datetime

import psycopg2

DATABASE_HOST = os.getenv('DATABASE_HOST')
DATABASE_NAME = os.getenv('DATABASE_NAME')
DATABASE_PORT = os.getenv('DATABASE_PORT')
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
    campaign_id = event.get('campaign_id')

    # Query Database
    sql = f"""
    select banner_id from final_table
    where campaign_id = {campaign_id} and dataset = {dataset}
    order by random()
    limit 1;
    """

    conn = psycopg2.connect(
        host=DATABASE_HOST,
        database=DATABASE_NAME,
        port=DATABASE_PORT,
        user=DATABASE_USERNAME,
        password=DATABASE_USERNAME
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
        if result is not None:
            # The result is the first column of the first row
            output = result[0]
        else:
            output = None

        return {
            'statusCode': 200,
            'body': json.dumps(output)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Error: {str(e)}'
        }




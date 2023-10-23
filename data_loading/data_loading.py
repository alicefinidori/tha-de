import os
from sqlalchemy import create_engine # Using sqlalchemy for its convenient writing of dataframes to postgres
from sqlalchemy.sql import text
import pandas as pd

DATABASE_HOST = os.getenv('DATABASE_HOST', 'tha-de-alicefinidori-db.cpp5x7rhzsqs.eu-west-1.rds.amazonaws.com')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'postgres')
DATABASE_PORT = os.getenv('DATABASE_PORT', '5432')
DATABASE_USERNAME = os.getenv('DATABASE_USERNAME')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD')

DATASET_CSV_PATH = '../datasets/csv'

CREATE_FINAL_TABLES_SQL = f"""
    create table if not exists clicks(
        click_id int primary key,
        banner_id int,
        campaign_id int
    );

    create table if not exists conversions(
        conversion_id int primary key,
        click_id int,
        revenue float,
        CONSTRAINT fk_click
        FOREIGN KEY(click_id) 
        REFERENCES clicks(click_id)	
    );

    create table if not exists impressions(
        banner_id int,
        campaign_id int	
    );

    create or replace view conversions_and_clicks_agg as (
        select dataset, campaign_id, banner_id, coalesce(sum(revenue), 0) as total_revenue, count(distinct click_id) as click_counts
        from impressions i 
        left join clicks cl using(dataset, banner_id, campaign_id)
        left join conversions co using(click_id, dataset)
        group by dataset, campaign_id, banner_id 
    );

    create or replace view count_x as (
        select dataset, campaign_id, count(distinct banner_id) as x
        from conversions_and_clicks_agg 
        where total_revenue > 0
        group by dataset, campaign_id
    );

    create or replace view top_10_conversions as (
        select dataset, campaign_id, banner_id, total_revenue, click_counts
        from (
            select 
                *,
                row_number() over (partition by dataset, campaign_id order by total_revenue desc) as row_num
            from conversions_and_clicks_agg c 
            where total_revenue > 0
        ) A
        where row_num <= 10
    );

    create or replace view top_5_non_converted_clicks as (
        select dataset, campaign_id, banner_id, total_revenue, click_counts
        from (
            select 
                *,
                row_number() over (partition by dataset, campaign_id order by click_counts desc) as row_num
            from conversions_and_clicks_agg c 
            where total_revenue = 0 and click_counts > 0
        ) B
        where row_num <= 5
    );

    create or replace view random_5_non_clicked_impressions as (
        select dataset, campaign_id, banner_id, total_revenue, click_counts
        from (
            select 
                *,
                row_number() over (partition by dataset, campaign_id order by random()) as row_num
            from conversions_and_clicks_agg c 
            where total_revenue = 0 and click_counts = 0
        ) A where row_num <= 5
    );

    create materialized view if not exists top_banners as 
    select * from (
        select *, row_number() over (partition by dataset, campaign_id order by dataset, campaign_id, total_revenue, click_counts) as row_num
        from (
            select * from top_10_conversions co
            union
            select * from top_5_non_converted_clicks cl
            union
            select * from random_5_non_clicked_impressions i
        ) A 
        left join count_x using(dataset, campaign_id)
    ) B where row_num <= case when x >= 10 then 10 when x >= 5 then x else 5 end;
"""

REFRESH_MATERIALIZED_VIEW = f"""
    refresh materialized view top_banners;
"""


def import_csv(dataset, csv_name, engine):
    local_csv_file = f'{DATASET_CSV_PATH}/{dataset}/{csv_name}_{dataset}.csv'
    df = pd.read_csv(local_csv_file)
    initial_len = len(df)
    if csv_name in ['clicks', 'conversions']:
        df = df.drop_duplicates(ignore_index=True)
        final_len = len(df)
        print(f'Dropped {initial_len - final_len} duplicates for file {csv_name}_{dataset}')

    try:
        df.to_sql(f'{csv_name}_{dataset}', engine, if_exists='fail', index=False)
    except ValueError as e:
        print(f'Table {csv_name}_{dataset} already contains data. Ignoring.')


def insert_into(csv_name, con):
    sql = f'INSERT INTO {csv_name}'
    sql_list = []
    for dataset in [1,2,3,4]:
        sql_list.append(f"""
        select *, {dataset} from {csv_name}_{dataset}
        """)
    sql += "union".join(sql_list)
    sql += """
    ON CONFLICT DO NOTHING;
    """
    con.execute(text(sql))
    return sql


if __name__ == '__main__':

    datasets = [1, 2, 3, 4]

    engine = create_engine(f'postgresql://{DATABASE_USERNAME}:{DATABASE_PASSWORD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}')

    with engine.connect() as con:

        con.execute(text(CREATE_FINAL_TABLES_SQL))
        for csv_name in ['clicks', 'conversions', 'impressions']:
            for dataset in datasets:
                print(f'Importing file {csv_name} dataset {dataset}')
                import_csv(dataset, csv_name, engine)
            insert_into(csv_name, con)

        con.execute(text(REFRESH_MATERIALIZED_VIEW))
        con.commit()








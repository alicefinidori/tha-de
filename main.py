import pandas as pd

DATASET_CSV_PATH = 'datasets/csv'


def get_csvs_as_df(csv_name, sort_values_by=None):
    dfs = []
    for dataset in [1,2,3,4]:
        path = f'{DATASET_CSV_PATH}/{dataset}/{csv_name}_{dataset}.csv'
        df = pd.read_csv(path).drop_duplicates(ignore_index=True)
        if sort_values_by is not None:
            df = df.sort_values(by=sort_values_by)
        dfs.append(df)
    return dfs


if __name__ == '__main__':

    impressions = get_csvs_as_df('impressions', ['banner_id','campaign_id'])
    clicks = get_csvs_as_df('clicks')

    joined_dfs = []
    for dataset in [0,1,2,3]:
        new_df = pd.merge(impressions[dataset], clicks[dataset], how='left', left_on=['banner_id', 'campaign_id'], right_on=['banner_id', 'campaign_id'])
        joined_dfs.append(new_df)

    print(len(impressions))

# See PyCharm help at https://www.jetbrains.com/help/pycharm/

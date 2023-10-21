# THA - DE - Banner Selection Web Application 

The goal of this project is to create a web page which serves banners for one of many websites owned by our client.

## Assumptions made for this exercise

- The web application is a read only application, i.e. it will not write to the source data. Indeed, this application is used to serve banners and not to update the logic with which the banners are served.
- The web application has a single endpoint which returns a single banner for a given ``campaign_id``. 
- The source data is expected to be static, based on the instruction that importing a duplicate CSV file should be gracefully rejected. 
- We want to avoid saturation on our client's website (not ours) so the banners returned should not show a fixed order based on revenue. 

## Architecture 

### Web application 

The web app is available at the following endpoint: https://8xrnxosynb.execute-api.eu-west-1.amazonaws.com/default/campaigns/{campaign_id}.

The web application has the following architecture

![web_app_architecture_with_s3.png](readme_images%2Fweb_app_architecture_with_s3.png)

A user connects to a lambda function via API Gateway, which in turn queries a Postgres Database on Amazon RDS containing the result data, and returns a banner_id. 

The lambda function then returns the campaign id a dataset values (purely for validation purposes) and an image. When clicked, it links to the S3 bucket link of that image. For the final product, the image would link to the correct ad. 

All resources used for this application on AWS were tagged with the following key value pairs

| Key | Value |
| -------- | -------- | 
| owner | alicefinidori | 
| project | tha-de-alicefinidori | 
| environment | dev | 

For automation purposed, the next step would be to import these resources using the tags into a Cloudformation Stack or with Terraform. 


### Data Loading

As mentioned in the initial assumptions, the data loading is expected to happen ad-hoc, and should not allow to import duplicated data.
Therefore, for this exercise, the data is to be updated manually via a data loading script in this repository. A potential improvement would be to automate this import (see enhancements at the end of this file).

The data loading script can be executed by running the following commands in the root directory of this project:
```commandline
pip install -r data_loading/requirements.txt
python data_loading/data_loading.py
```
Note : this script expects the remote database password and username to be stored respectively as the environment variables ``DATABASE_PASSWORD`` and ``DATABASE_USERNAME``.



Furthermore, for simplicity and time constraints (to be able to quickly explore the raw data and test transformations), we will be following an ELT process, where all the raw data is loaded to the final data Store, then transformed in the same data store.
Since the raw data is not required by the web application, a future enhancement could be to remove the raw data from the final data store and store is simply as intermediary csv or in a data warehouse.

We will also not be catering for schema changes in this exercise. 

The data model used to store the data is described in the next section. 

## Data Modelling

### Source Data

The source data is split into 4 data sets, representing the 4 quarters of an hour i.e. a visit to the website on any hour will direct to a different dataset depending on the minute of the hour: 

| Minute | Dataset| 
| ------- | ------- | 
| 00 <= m < 15 | dataset 1 | 
| 15 <= m < 30 |  dataset 2 | 
| 30 <= m < 45 | dataset 3 | 
| 45 <= m < 00 | dataset 4 | 

 Each data set contains the same following files: 
- ``impressions.csv``: File containing impressions of different banners a campaign i.e. a record for each time a user saw a banner within a given campaign.
- ``clicks.csv``: File containing clicks on different banners within a campaign i.e. a record for each time a user clicked on a banner within a given campaign.
- ``conversions.csv``: File containing conversions for each converted click i.e. a record for each time a click generated revenue, and the amount of revenue generated.

### Data Schema

#### Snowflake Schema

For this project, with normalising the data, the ERD diagram can be as follows:
![erd.png](readme_images%2Ferd.png)
With the following tables: 
- campaign_banner

This table is the reference of what banner belongs to what campaign within each dataset. The ``dataset`` field is added to reference which dataset this campaign belongs to.
This is the only table that can not be directly associated with one of the input csv files. Because this reference data does not exist, it can be inferred from the ``impressions.csv`` files.

- impressions

The list of impressions for each campaign_banner. The ``impressions_id`` can be auto generated for each record in the ``impresions.csv`` file.

- clicks: 

The list of clicks for each campaign_banner. Obtained from the ``clicks.csv`` and extracting the ``campaign_banner_id`` from the ``campaign_banner`` table. 

- conversions

The list of clicks and revenue for each campaign_banner. Directly generated from the ``conversions.csv`` file.


#### Business Rules

For each campaign, our web page wants to select at random a banner within a list of banners with the following business rules: 

|  X definition | Definition/Requirement | 
| ------ |--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------| 
| X  | the number of banners with conversions within a campaign                                                                                                                                                                       | 
| X >= 10 | Show the Top 10 banners based on revenue within that campaign                                                                                                                                                                  | 
| X in range(5,10) | Show the Top X banners based on revenue within that campaign                                                                                                                                                                   | 
| X in range(1,5) | Your collection of banners should consist of 5 banners, containing: The top x banners based on revenue within that campaign and Banners with the most clicks within that campaign to make up a collection of 5 unique banners. | 
| X == 0 | Show the Top 5 banners based on clicks. If the number of banners with clicks is less than 5 within that campaign, then you should add random banners to make up a collection of 5 unique banners.                              | 


#### Final schema used

For this exercise and this data structure, our final target table requires to re-aggregate the data, so we can use the simpler ERD. It will entail a little bit of data duplication, but that can be ignored for this dataset.

![erd_2.png](readme_images%2Ferd_2.png)

Each of the above table contains is the union of the individual dataset csvs. 

To get the source reference of what banner belongs to what campaign within each dataset, we can simplify by using the distinct ``banner_id``, ``campaign_id`` combinations.

Next, to obtain the actual data that is extracted by the web app, views are created. The two main views are:

- conversions_and_clicks_agg: 

![conversions_and_clicks_agg.png](readme_images%2Fconversions_and_clicks_agg.png)

For each dataset, campaign_id, banner_id combination (including those without clicks or conversions), calculate total revenue and click counts. 

- top_banners

![top_banners.png](readme_images%2Ftop_banners.png)

For each dataset, campaign_id, banner_id combination, show between 5 and 10 banners depending on the business rules defined above.
The main data source for this view is the ``conversions_and_clicks_agg`` view and some other intermediary views.

The web page will select for each campaign id a random banner within this view to serve to our end user.
Because it will be queried directly by the app, this view is persisted in the form of a materialized view. 

## Deploying th lambda function

To deploy the lambda function for the web app, create zip file package with the following commands in the root directory of this project:
```commandline
docker build -t lambda-builder .
docker run --rm -v $(pwd)/web_app:/app lambda-builder
```

## Load testing

In order to load test this application, the [locust](https://docs.locust.io/en/stable/what-is-locust.html) framework is used.

Note: This framework is new to me :). 

To run the load test, run the following commands in the root directory of this project:
```commandline
pip install locust
locust -f load_test/locustfile.py --host=https://8xrnxosynb.execute-api.eu-west-1.amazonaws.com --users 500 --spawn-rate 208 --run-time 2m
```
Then open the following link in a browser: http://0.0.0.0:8089/, and start the test.

The requirement for load on this application is as follows: 

> Your application should serve at least 5000 requests per minute ­ The script and results of the stress­ test should be provided.

For determining those parameters, we use the following calculation: 
```
Hatch Rate = (Total Number of Users / Test Duration in seconds) * (Desired Requests Per Minute / 60)
```
i.e. in our case: 
```commandline
Hatch Rate = (500 / 120) * (5,000 / 60) = 208.33 
```

![load_test.png](readme_images%2Fload_test.png)

The app sustains the load test. 

If we were to run the test with double the number of users, the failure rate goes to about 10 percent. In order to improve the performance of our app, we would need to increase the lambda concurrency limit. This was not done as part of this exercise. 



## Enhancements


1. Ensure a unique visitor never sees the same banner twice in a row. 

In the current implementation, the web page will select a random banner thanks to the use of the ``random()`` method in Postgres. 
We will assume for the sake of this exercise that it is highly unlikely that for a given user, the same banner will be returned twice.

An enhancement of this app would be to ensure a user does not see the same banner twice by storing session data for all API calls: 
- when a given user opens a session, each time an API call is made, the last returned banner is stored in the session data as ``previous_banner_id`` 
- the following time a user queries the database explicitly excluding ``previous_banner_id``

2. Continuous updates to the source data

An initial assumption for this project is that the source data will be not be updated. 

If this requirement changes, we could introduce: 
- a batch process to import new csv files on a schedule (e.g. a lambda function triggered by updated to an S3 bucket).
- a streaming architecture to continuously update the ``impressions`` and ``conversions`` data sources.

3. Raw data storage

In this exercise, for simplicity and time constraints (to be able to quickly explore the raw data and test transformations), we will be following an ELT process, where all the raw data is loaded to the final data Store, then transformed in the same data store.
Since the raw data is not required by the web application, a future enhancement could be to remove the raw data from the final data store and store is simply as intermediary csv or in a data warehouse.

Another improvement would be to cater for schema changes in the raw data. 

4. CI/CD

All the resources and code were manually updated for this project. Including CI/CD will make it more maintainable.

5. Security

For the sake of this exercise, security was not a main concern. For a production application, the necessary precautions will need to be taken for networking and API Gateway authorizations to make sure this application is secure.

6. Infrastructure as Code

The AWS resources were manually created via the AWS console.
The next step would be to import them into a Cloudformation Stack or into Terraform in order to easily re-create the environments. 

7. Data validation tests

The data transformation in this project is done via SQL, and the python code is fairly straightforward. For rigorous testing of the output of the API, we would need to introduce data validation steps in the transformation. This could be done by using a framework like dbt to run the ELT steps, which includes testing capability.  

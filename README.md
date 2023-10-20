# THA - DE - Banner Selection Web Application 

The goal of this project is to create a web page which serves banners for one of many websites owned by our client.

## Architecture 

The web application has the following architecture
![architecture.drawio.png](readme_images%2Farchitecture.drawio.png)

A user connects to a lambda function via API Gateway, which in turn queries a Postgres Database on Amazon RDS containing the result data.


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

### Snowflake schema

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


### Business Rules

For each campaign, our web page wants to select at random a banner within a list of banners with the following business rules: 

|  X definition | Definition/Requirement | 
| ------ |--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------| 
| X  | the number of banners with conversions within a campaign                                                                                                                                                                       | 
| X >= 10 | Show the Top 10 banners based on revenue within that campaign                                                                                                                                                                  | 
| X in range(5,10) | Show the Top X banners based on revenue within that campaign                                                                                                                                                                   | 
| X in range(1,5) | Your collection of banners should consist of 5 banners, containing: The top x banners based on revenue within that campaign and Banners with the most clicks within that campaign to make up a collection of 5 unique banners. | 
| X == 0 | Show the Top 5 banners based on clicks. If the number of banners with clicks is less than 5 within that campaign, then you should add random banners to make up a collection of 5 unique banners.                              | 


To obtain this list, we will create the following two tables:

- conversions_and_clicks_agg: 

![conversions_and_clicks_agg.png](readme_images%2Fconversions_and_clicks_agg.png)

For each campaign_banner (i.e. id, campaign_id, banner_id combination), calculate total revenue and click counts.

- top_banners

![top_banners.png](readme_images%2Ftop_banners.png)

For each campaign_banner (i.e. id, campaign_id, banner_id combination), show between 5 and 10 banners depending on the business rules defined above. 
The web page will select for each campaign id a random banner within this list to serve to our end user. 



## Load testing


## Enhancements


1. Ensure a unique visitor never sees the same banner twice in a row. 

In the current implementation, the web page will select a random banner thanks to the use of the ``random()`` method in Postgres. 
We will assume for the sake of this exercise that it is highly unlikely that for a given user, the same banner will be returned twice.

An enhancement of this app would be to ensure a user does not see the same banner twice by storing session data for all API calls: 
- when a given user opens a session, each time an API call is made, the last returned banner is stored in the session data as ``previous_banner_id`` 
- the following time a user queries the database explicitly excluding ``previous_banner_id``

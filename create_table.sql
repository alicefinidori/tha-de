create table clicks_1(
	click_id int,
	banner_id int,
	campaign_id int
);

create table conversions_1(
	conversion_id int,
	click_id int,
	revenue float
);

create table impressions_1(
	banner_id int,
	campaign_id int
);

create table clicks_2(
	click_id int,
	banner_id int,
	campaign_id int
);

create table conversions_2(
	conversion_id int,
	click_id int,
	revenue float
);

create table impressions_2(
	banner_id int,
	campaign_id int
);

create table clicks_3(
	click_id int,
	banner_id int,
	campaign_id int
);

create table conversions_3(
	conversion_id int,
	click_id int,
	revenue float
);

create table impressions_3(
	banner_id int,
	campaign_id int
);

create table clicks_4(
	click_id int,
	banner_id int,
	campaign_id int
);

create table conversions_4(
	conversion_id int,
	click_id int,
	revenue float
);

create table impressions_4(
	banner_id int,
	campaign_id int
);

create table clicks as
select distinct click_id, banner_id, campaign_id, dataset from (
	select *, 1 as dataset from clicks_1
	union
	select *, 2 as dataset from clicks_2
	union
	select *, 3 as dataset from clicks_3
	union
	select *, 4 as dataset from clicks_4
) A ;

create table conversions as
select distinct conversion_id, click_id, revenue, dataset from (
	select *, 1 as dataset from conversions_1
	union
	select *, 2 as dataset from conversions_2
	union
	select *, 3 as dataset from conversions_3
	union
	select *, 4 as dataset from conversions_4
) A ;

create table impressions as
select banner_id, campaign_id, dataset from (
	select *, 1 as dataset from impressions_1
	union
	select *, 2 as dataset from impressions_2
	union
	select *, 3 as dataset from impressions_3
	union
	select *, 4 as dataset from impressions_4
) A;

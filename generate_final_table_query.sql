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

drop table final_table;
create table final_table as 
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
select * from final_table
where campaign_id = 1 and dataset = 1
order by random();
;
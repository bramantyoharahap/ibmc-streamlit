
sql_cmd_responderCount = "select count(*) as responderCount from df_response_header"

template_sql_command = """
                WITH T AS(            
                    select 
                        a.id,
                        a.name,
                        a.gender,
                        a.band,
                        a.years_of_service,
                        a.area,
                        a.generation,
                        b.Question,
                        b.Option,
                        cast(e.Grade as varchar(1)) as Rank
                    from df_response_header as a 
                    inner join df_response_detail as b on a.Id = b.ResponseId
                    left join df_question as c on c.Id = b.Question
                    inner join df_domain as d on d.Id = c.Domain 
                    left join df_option as e on e.Id = b.Option
                    where 1=1
                    [#ADDITIONAL_CRITERIA#]
                    --and d.Name in ([#DOMAIN_IDs#])
                    --and d.Name = '[#DOMAIN_IDs#]'
                ),
                T2 AS(
                    SELECT 
                        Option,
                        case 
                            when Rank=1 then '#72d8ff'
                            when Rank=2 then '#b5e6a2'
                            when Rank=3 then '#daf2d0'
                            when Rank=4 then '#ffff47'
                            when Rank=5 then '#fd5454'
                        end as Color,
                        Rank,
                        count(*) as ResponderCount
                    FROM T
                    GROUP BY Option
                )
                SELECT *,
                    ROUND(AVG(ResponderCount/[#RESPONDERCOUNT#]*100), 2)||'%' as Percentage
                FROM T2
                GROUP BY Color
                ORDER BY CASE WHEN Color = '#72d8ff' THEN 1
                     WHEN Color = '#b5e6a2' THEN 2
                     WHEN Color = '#daf2d0' THEN 3
                     WHEN Color = '#ffff47' THEN 4
                     WHEN Color = '#fd5454' THEN 5 ELSE '' END;
                """
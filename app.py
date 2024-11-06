import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from pandasql import sqldf
import plotly.express as px

spreadsheet_master = "https://docs.google.com/spreadsheets/d/1WYwhKtns9Jd0QZ4QmlJOd_YO9baQG5sBLGeBcf-hJMY"
spreadsheet_response = "https://docs.google.com/spreadsheets/d/1PbqBhlvhcIFN7i-19vVZqEkYX45s07mcgn3QVyUQdjQ"

# Create a connection object.
conn = st.connection("gsheets", type=GSheetsConnection)

df_question = conn.read(spreadsheet=spreadsheet_master, worksheet="Question")
df_domain = conn.read(spreadsheet=spreadsheet_master, worksheet="Domain")
df_option = conn.read(spreadsheet=spreadsheet_master, worksheet="Option")
df_option["Grade"] = df_option["Grade"].astype(int)
df_response_header = conn.read(
    spreadsheet=spreadsheet_response, worksheet="mondaydotcom_response_header"
)
df_response_detail = conn.read(
    spreadsheet=spreadsheet_response, worksheet="mondaydotcom_response_detail"
)
group = 1

def fn():
    
    respondercount = sqldf("select count(*) as responderCount from df_response_header")
    respondercount = respondercount['responderCount'].loc[0]
    
    st.header("IBM Consulting - Way Habits - Pertamedika")
    st.text("Date: 30 Oct 2024")
    st.text(f"""Total Responder: {respondercount}""")
    
    
    for id_domain in range(1,30) :
    
        q = sqldf(f"select cast(id as int) as id from df_question where domain={id_domain}")
        print(q)
        for i, row in q.iterrows():
            _df = sqldf(
                f"""
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
                    where a.grp = '{group}'
                    and b.Question = {row['id']}
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
                    --ORDER BY Color, Option ASC;
                )
                SELECT *,
                    ROUND(ResponderCount/{float(respondercount)}*100, 2) as Percentage
                FROM T2
                ORDER BY CASE WHEN Color = '#72d8ff' THEN 1
                     WHEN Color = '#b5e6a2' THEN 2
                     WHEN Color = '#daf2d0' THEN 3
                     WHEN Color = '#ffff47' THEN 4
                     WHEN Color = '#fd5454' THEN 5 ELSE '' END;
                """
            )

            df_temp = sqldf(
                f"""
                select 
                    d.Name,
                    b.Question as QId,
                    c.Question as Question
                from df_response_header as a 
                inner join df_response_detail as b on a.Id = b.ResponseId
                left join df_question as c on c.Id = b.Question
                inner join df_domain as d on d.Id = c.Domain 
                left join df_option as e on e.Id = b.Option
                where a.grp = '{group}'
                and b.Question = {row['id']}
                group by d.Name
                        """
            )

            st.header(
                f"""
                    Domain - {df_temp.loc[0,'Name']}\n
                    Question: {int(df_temp.loc[0,'QId'])} - {df_temp.loc[0,'Question']}
                    """
            )

            fig = px.bar(
                _df,
                x="Option",
                y="ResponderCount",
                color="Color",
                color_discrete_map="identity",
                text_auto=False,
                text="Percentage"
            )
            # st.text(f"""Total Responder {respondercount}""")

            fig.update_yaxes(range=[0, respondercount], dtick=2)
            st.plotly_chart(fig)
            # print(_df)
            # st.bar_chart(_df, x="Rank", y="ResponderCount", color="Color", stack=True)`
            
def fn2():
    
    respondercount = sqldf("select count(*) as responderCount from df_response_header")
    respondercount = respondercount['responderCount'].loc[0]
    
    st.header("IBM Consulting - Way Habits - Pertamedika")
    st.text("Date: 30 Oct 2024")
    st.text(f"""Total Responder: {respondercount}""")
    
    
    for id_domain in range(1,7) :
        
        _df = sqldf(
                f"""
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
                    where a.grp = '{group}'
                    and c.Domain = {id_domain}
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
                    --ORDER BY Color, Option ASC;
                )
                SELECT *,
                    ROUND(AVG(ResponderCount/{float(respondercount)}*100), 2)||'%' as Percentage
                FROM T2
                GROUP BY Color
                ORDER BY CASE WHEN Color = '#72d8ff' THEN 1
                     WHEN Color = '#b5e6a2' THEN 2
                     WHEN Color = '#daf2d0' THEN 3
                     WHEN Color = '#ffff47' THEN 4
                     WHEN Color = '#fd5454' THEN 5 ELSE '' END;
                """
            )

        df_temp = sqldf(
            f"""
            select 
                d.Name,
                b.Question as QId,
                c.Question as Question
            from df_response_header as a 
            inner join df_response_detail as b on a.Id = b.ResponseId
            left join df_question as c on c.Id = b.Question
            inner join df_domain as d on d.Id = c.Domain 
            left join df_option as e on e.Id = b.Option
            where a.grp = '{group}'
            and c.Domain = {id_domain}
            group by d.Name
                    """
        )

        st.header(
            f"""
                Domain - {df_temp.loc[0,'Name']}
                """
        )

        fig = px.bar(
            _df,
            x="Option",
            y="ResponderCount",
            color="Color",
            color_discrete_map="identity",
            text_auto=False,
            text="Percentage"
        )

        fig.update_yaxes(range=[0, respondercount], dtick=2)
        st.plotly_chart(fig)

fn2()


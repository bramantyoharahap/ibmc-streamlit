import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from pandasql import sqldf
import plotly.express as px
from streamlit_extras.stylable_container import stylable_container
from global_variable import sql_cmd_responderCount, template_sql_command


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


class App:
    _df = None
    fig = None
    placeholder = st.empty()
    container = st.container()
    st.session_state["clear"] = False
    sitebar = st.sidebar
    df_sales = conn.read(spreadsheet=spreadsheet_master, worksheet="Sales")
    df = sqldf("select * from df_sales")
    cl = 0
    criteria = {
        "domain": [],
        "average": False
    }
    
    def __init__(self):
        self.build_sidebar()
        
    def fn(self):
        st.session_state["clear"] = False
        self.build_header()
        self.build_sidebar()
        self.build_charts()
            
    def build_header(self):
        respondercount = sqldf(sql_cmd_responderCount)
        respondercount = respondercount['responderCount'].loc[0]
        st.header("IBM Consulting - Way Habits")
        st.text(f"""Total Responder: {respondercount}""")
                    
    def show_datavis(self):    
        self.build_header()
        selected_domain = st.session_state["selected_domain"]
        sqlCommand = template_sql_command
        _sales = self.df_sales
        respondercount = sqldf(sql_cmd_responderCount)
        respondercount = respondercount['responderCount'].loc[0]
        
        if selected_domain == []:
            sqlCommand = sqlCommand.replace("[#ADDITIONAL_CRITERIA#]", "and d.Name = d.Name")
            sqlCommand = sqlCommand.replace("[#RESPONDERCOUNT#]", str(respondercount))
            print(sqlCommand)
            self.df = sqldf(sqlCommand)
            self.build_charts()
        else:
            domains = str(selected_domain).replace("[", "").replace("]", "")
            
            sqlCommand = sqlCommand.replace("[#ADDITIONAL_CRITERIA#]", f"and d.Name in ({domains})")
            sqlCommand = sqlCommand.replace("[#RESPONDERCOUNT#]", str(respondercount))
            print(sqlCommand)
            self.df = sqldf(sqlCommand)
            self.build_charts()
            
    def apply_criteria(self):
        respondercount = sqldf("select count(*) as responderCount from df_response_header")
        respondercount = respondercount['responderCount'].loc[0]
        selected_domain = st.session_state["selected_domain"]
        selected_avg = True if st.session_state["selected_avg"] == 'Yes' else False
        
        if selected_domain != []:
            for domain in selected_domain:
                domain_id = sqldf(f"select cast(id as int) as id from df_domain where name='{domain}'")['id'][0]
                questions = sqldf(f"select cast(id as int) as id from df_question where domain={domain_id}")
                
                if selected_avg:
                    self.apply_average(domain_id, respondercount)
                else:
                    self.apply_detail(questions, respondercount)
                    
        else:
            domain_ids = sqldf("select cast(id as int) as id from df_domain")['id']
            
            for domain_id in domain_ids:
                questions = sqldf(f"select cast(id as int) as id from df_question where domain={domain_id}")
                if selected_avg:
                    self.apply_average(domain_id, respondercount)
                else:
                    self.apply_detail(questions, respondercount)
               
    def apply_average(self, id_domain, respondercount):
        print("id_domain:", id_domain)
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
                where 1=1
                and d.Id = {id_domain}
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
            where 1=1
            and d.Id = {id_domain}
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
            x="Rank",
            y="ResponderCount",
            color="Color",
            color_discrete_map="identity",
            text_auto=False,
            text="Percentage"
        )
        
        fig.update_yaxes(range=[0, respondercount], dtick=2)
        st.plotly_chart(fig)
    
    def apply_detail(self, questions, respondercount):
        for i, row in questions.iterrows():
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
                    where b.Question = {row['id']}
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
                        count(*) as ResponderCount,
                        ROUND(count(*)/{float(respondercount)}*100, 2)||'%' as Percentage
                    FROM T
                    GROUP BY Option
                    --ORDER BY Color, Option ASC;
                )
                SELECT *
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
                where b.Question = {row['id']}
                group by d.Name
                        """
            )

            st.title(
                f"""
                    Domain - {df_temp.loc[0,'Name']}\n
                    Question {int(df_temp.loc[0,'QId'])} - {df_temp.loc[0,'Question']}
                    """
            )
            st.text(f"""Total Responder {respondercount}""")
            
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
        
    def build_sidebar(self):
        with self.sitebar:
            st.multiselect("Select Domain", df_domain['Name'], [], on_change=self.apply_criteria, key="selected_domain", )
            st.selectbox("Average per Domain", ['Yes', 'No'], index=1, key='selected_avg', on_change=self.apply_criteria)
            st.button("OK", on_click=self.apply_criteria, key="btnShow")

    def build_charts(self):
        fig = px.bar(
                self.df,
                x="Option",
                y="ResponderCount",
                color="Color",
                color_discrete_map="identity",
                text_auto=False,
                text="Percentage"
            )
            # st.text(f"""Total Responder {respondercount}""")

        fig.update_yaxes(range=[0, 26], dtick=2)
        st.plotly_chart(fig)
        # fig = px.bar(
        #         self.df,
        #         x="Year",
        #         y="Amount"
        #     )
        # st.plotly_chart(fig)
        
app = App()


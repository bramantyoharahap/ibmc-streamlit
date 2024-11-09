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
df_response_header = conn.read(spreadsheet=spreadsheet_response, worksheet="mondaydotcom_response_header")
df_response_detail = conn.read(spreadsheet=spreadsheet_response, worksheet="mondaydotcom_response_detail")
df_band = conn.read(spreadsheet=spreadsheet_master, worksheet="Band")
df_area = conn.read(spreadsheet=spreadsheet_master, worksheet="Area")
df_gender = conn.read(spreadsheet=spreadsheet_master, worksheet="Gender")
df_generation = conn.read(spreadsheet=spreadsheet_master, worksheet="Generation")
df_yos = conn.read(spreadsheet=spreadsheet_master, worksheet="YearOfService")
df_group = conn.read(spreadsheet=spreadsheet_master, worksheet="Group")


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
    key_domain = "key_domain"
    key_band = "key_band"
    key_area = "key_area"
    key_gender = "key_gender"
    key_generation = "key_generation"
    key_yos = "key_yos"
    key_group = "key_group"
    
    criteria = {
        "domain": [],
        "average": False,
        "band": [],
        "area": [],
        "gender": [],
        "generation": [],
        'yos':[],
        'group': []
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
        selected_domain = st.session_state[self.key_domain]
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
            
    def build_command_criteria(self):
        result = ""
        bands = "" if self.criteria["band"] == [] else str(self.criteria["band"]).replace("[","").replace("]","")
        areas = "" if self.criteria["area"] == [] else str(self.criteria["area"]).replace("[","").replace("]","")
        genders = "" if self.criteria["gender"] == [] else str(self.criteria["gender"]).replace("[","").replace("]","")
        generations = "" if self.criteria["generation"] == [] else str(self.criteria["generation"]).replace("[","").replace("]","")
        yos = "" if self.criteria["yos"] == [] else str(self.criteria["yos"]).replace("[","").replace("]","")
        groups = "" if self.criteria["group"] == [] else str(self.criteria["group"]).replace("[","").replace("]","")
        
        if bands != "":
            result = result + f"and a.band in ({bands})\n"
        elif areas != "":
            result = result + f"and a.area in ({areas})\n"
        elif genders != "":
            result = result + f"and a.gender in ({genders})\n"
        elif generations != "":
            result = result + f"and a.generation in ({generations})\n"
        elif yos != "":
            result = result + f"and a.years_of_service in ({yos})\n"
        elif groups != "":
            result = result + f"and f.name in ({groups})\n"
        else:
            result = ""
        
        return result
    
    def apply_criteria(self):
        self.criteria["domain"] = st.session_state[self.key_domain]
        self.criteria["average"] = True if st.session_state["selected_avg"] == 'Yes' else False
        self.criteria["band"] = st.session_state[self.key_band]
        self.criteria["area"] = st.session_state[self.key_area]
        self.criteria["gender"] = st.session_state[self.key_gender]
        self.criteria["generation"] = st.session_state[self.key_generation]
        self.criteria["yos"] = st.session_state[self.key_yos]
        self.criteria["group"] = st.session_state[self.key_group]
        command_criteria = self.build_command_criteria()
        respondercount = sqldf(f"""
                               select count(*) as responderCount 
                               from df_response_header as a
                               left join df_group as f on f.id = a.grp
                               where 1=1
                               {command_criteria}
                               """)
        respondercount = respondercount['responderCount'].loc[0]
        
        if self.criteria["domain"] != []:
            for domain in self.criteria["domain"]:
                domain_id = sqldf(f"select cast(id as int) as id from df_domain where name='{domain}'")['id'][0]
                questions = sqldf(f"select cast(id as int) as id from df_question where domain={domain_id}")
                
                if self.criteria["average"]:
                    self.apply_average(domain_id, respondercount)
                else:
                    self.apply_detail(questions, respondercount)
                    
        else:
            domain_ids = sqldf("select cast(id as int) as id from df_domain")['id']
            
            for domain_id in domain_ids:
                questions = sqldf(f"select cast(id as int) as id from df_question where domain={domain_id}")
                if self.criteria["average"]:
                    self.apply_average(domain_id, respondercount)
                else:
                    self.apply_detail(questions, respondercount)
               
    def apply_average(self, id_domain, respondercount):
        command_criteria = self.build_command_criteria()
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
                left join df_group as f on f.Id = a.grp
                where 1=1
                and d.Id = {id_domain}
                {command_criteria}
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
            inner join df_option as e on e.Id = b.Option
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
        st.text(f"""Total Responder {respondercount}""")

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
            command_criteria = self.build_command_criteria()
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
                        a.grp,
                        b.Question,
                        b.Option,
                        cast(e.Grade as varchar(1)) as Rank
                    from df_response_header as a 
                    inner join df_response_detail as b on a.Id = b.ResponseId
                    left join df_question as c on c.Id = b.Question
                    inner join df_domain as d on d.Id = c.Domain 
                    left join df_option as e on e.Id = b.Option
                    left join df_group as f on f.Id = a.grp
                    where 1=1
                    and b.Question = {row['id']}
                    {command_criteria}
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
    
    def reset_criteria(self):
        st.session_state[self.key_domain] = []
        st.session_state["selected_avg"] = 'No'
        st.session_state[self.key_band] = []
        st.session_state[self.key_area] = []
        st.session_state[self.key_gender] = []
        st.session_state[self.key_generation] = []
        st.session_state[self.key_yos] = []
        self.apply_criteria()
    
    def build_sidebar(self):
        with self.sitebar:
            st.title("Search Criteria")
            col1, col2 = st.columns([1,1])
            
            with col1:
                st.multiselect("Select Domain", df_domain['Name'], [], on_change=self.apply_criteria, key=self.key_domain)
                st.multiselect("Select Band", df_band['Band'], [], on_change=self.apply_criteria, key=self.key_band)
                st.multiselect("Select Gender", df_gender['Gender'], [], on_change=self.apply_criteria, key=self.key_gender)
                st.multiselect("Select Year of Service", df_yos['YoS'], [], on_change=self.apply_criteria, key=self.key_yos)
                st.button(  "OK", on_click=self.apply_criteria, key="btnShow")
            with col2:
                st.selectbox("Average per Domain", ['Yes', 'No'], index=1, key='selected_avg', on_change=self.apply_criteria)
                st.multiselect("Select Area", df_area['Area'], [], on_change=self.apply_criteria, key=self.key_area)
                st.multiselect("Select Generation", df_generation['Generation'], [], on_change=self.apply_criteria, key=self.key_generation)    
                st.multiselect("Select Project/Group", df_group['Name'], [], on_change=self.apply_criteria, key=self.key_group)
                st.button("Reset", on_click=self.reset_criteria, key="btnReset")
            
            
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


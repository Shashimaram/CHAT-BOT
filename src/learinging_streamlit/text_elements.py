import streamlit as st
import polars as pl


st.markdown(
"""
<style>
.stMainMenu
    {
    visibility: hidden;
    }
</style>
""",
unsafe_allow_html=True
)


st.markdown(
"""
<style>
.st-emotion-cache-1wbqy5l
    {
    visibility: hidden;
    }
</style>
""",
unsafe_allow_html=True
)

st.text("Hello World")
st.markdown("Hello World")





code = """
for x in range(10):
    print(x)
"""
st.code(code, language="python")
st.latex(r"f(x) = \int_{-\infty}^\infty \hat f(\xi)\,e^{2 \pi i \xi x} \,d\xi")
st.text_input("Enter your name")
st.text_area("Enter your bio")
st.number_input("Enter your age")
st.date_input("Enter your date of birth")
st.time_input("Enter your time")
st.multiselect("Select your hobbies", ["Reading", "Writing", "Coding"])



json = {
    "name": "John",
    "age": 30,
    "gender": "Male",
    "hobbies": ["Reading", "Writing", "Coding"]
}
st.json(json)

python_code = """
import streamlit as st
st.write("hello world")
"""
st.code(python_code, language="python")


st.write(json)

df =  pl.DataFrame({
    "name": ["John", "Jane", "Jim"],
    "age": [30, 25, 35],
    "gender": ["Male", "Female", "Male"]
})
st.dataframe(df)


# table:
st.write("This is a test table")
test_table = {
    "name": ["John", "Jane", "Jim"],
    "age": [30, 25, 35],
    "gender": ["Male", "Female", "Male"]
}
st.table(test_table)




st.image("C:/Users/smaram/Desktop/BOT/generated_charts/Top_10_AWS_Services_by_Total_Cost_1766847162.png",caption= "Top 10 AWS Services by Total Cost",width=500)


# Widgets:


st.checkbox("I agree")
st.toggle("I agree")
st.radio("Select your gender", ["Male", "Female", "Other"])
st.select_slider("Select your age", [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100])
st.slider("Select your age", 0, 100,step=10)
st.selectbox("Select your gender", ["Male", "Female", "Other"])
st.file_uploader("Upload your file")
st.color_picker("Select your color")
st.date_input("Select your date")
st.time_input("Select your time")


import random


def on_click():
    text = "atfarfd" + str(random.randint(1, 100))
    st.text_area("Enter your bio",value=text)
    
st.button("Click me", on_click=on_click())





from agents import research_agent, visualiation_agent
from strands import Agent
from model import bedrock_model

Main_prompt = """
You are a Data analyse agent specialized in analyzing Cloud billing data, You have two tools attached: read_schema_tool and execute_query. table name :  aws_oci_testing_data
Use the read_schema_tool to get the schema of the table and the execute_query to execute the query on the table. Use the execute_query to answer the user question.
You have to answer the user question by researching using attached tools. If you need to visualize data, use the visualization agent.
You can use the execute_query to answer the user question up to 10 times to get the data you need to answer the user question.
"""


research_agent  = Agent(
    model=bedrock_model,
    name="research_agent",
    tools=[
        research_agent,
        visualiation_agent,
    ],
    system_prompt=Main_prompt,
)


import asyncio

async def run_swarm():
    result = await research_agent.invoke_async("What is the cost Total EC2 Instances aws_oci_testing_data")
    return result

result = asyncio.run(run_swarm())

print(result.content)
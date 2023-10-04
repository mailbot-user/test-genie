import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space
import openai
import json
import pandas as pd

import os
from dotenv import load_dotenv, find_dotenv

# read local .env file
_ = load_dotenv(find_dotenv())

openai.api_key = os.getenv('OPENAI_API_KEY')


# Function to return system prompt
def get_system_prompt():

    system_message = f"""
    Imagine you are a software tester responsible for testing different testcase scenarios. 
    Your task is to design a test case that verifies the scenario's functionality. 
    Write a test case for the scenario that covers both positive and negative scenarios. 
    Ensure that you include the steps to validate the scenario and any expected outcomes. 
    Consider various test data and test environment details to make your test case comprehensive.
    Please provide a clear and structured test case that can be followed by a tester to ensure the 
    functions correctly and securely.
    You'll be provided the scenario along with the user queries
    """
    return system_message


# Function to return test steps prompt
def get_testcase_steps_prompt(scenario):

    user_message_2 = f"""
    Create a JSON representation of a test case {scenario}. 
    Include the following details in the JSON structure:
    1. Test Case Name.
    2. Objective.
    3. Preconditions (as an array).
    4. Test Steps (as an array of objects, each with Step, Action, and Expected_Result).
    5. Postconditions (as an array).

    Ensure that the JSON structure follows the format shown below:

    {{
        "Test_Case": "Test Case Name",
        "Objective": "Objective",
        "Preconditions": ["Precondition 1", "Precondition 2", ...],
        "Test_Steps": [
            {{
                "Step": 1,
                "Action": "Action description",
                "Expected_Result": "Expected result description"
            }},
            {{
                "Step": 2,
                "Action": "Action description",
                "Expected_Result": "Expected result description"
            }},
            ...
        ],
        "Postconditions": ["Postcondition 1", "Postcondition 2", ...]
    }}     """
    return user_message_2


# Function to generate a response from ChatGPT
def get_completion_from_messages(messages, model="gpt-3.5-turbo-16k", temperature=0):
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,  # this is the degree of randomness of the model's output
    )
    return response.choices[0].message["content"]


@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')


# creating a streamlit app
st.set_page_config(page_title='Testcases', layout='wide', page_icon='img/logo.png')


st.title('💬 Test Genie')
with st.sidebar:
    add_vertical_space(5)


st.subheader("Introducing Test Genie : Your Ultimate Testing Companion")
st.write("""Test Genie is your go-to web application for effortless test case generation. 
We've simplified the testing process, so you can focus on what matters most - ensuring software quality. 
Just describe your scenario, objectives, and any specific requirements, and let Test Genie do the rest.""")

st.write("""🔍 How It Works:""")

st.write("""1. Enter Your Scenario: Tell us about your testing scenario.\n 2. Auto-generate Test Cases: Our intelligent algorithms will create comprehensive test cases for you.\n 
3. Review & Customize: Easily review and tailor your test cases.\n 
4. Streamline Testing: Execute your test cases efficiently.""")

scenario = st.text_input('Test Case', placeholder="Write a test case for ")

# if Generate Test cases button is pressed
if st.button("Generate Test cases"):
    if scenario:
        if "scenario" not in st.session_state:
            st.session_state.scenario = scenario
        else:
            st.session_state.scenario = scenario

# if there's scenario, proceed to generate testcases
if "scenario" in st.session_state:
    system_prompt = get_system_prompt()
    user_message = get_testcase_steps_prompt(st.session_state.scenario)
    if 'messages' not in st.session_state:
        st.session_state['messages'] = [
            {"role": "system", "content": system_prompt},
            {'role': 'user',
             'content': user_message},
        ]
    else:
        st.session_state['messages'] = [
            {"role": "system", "content": system_prompt},
            {'role': 'user',
             'content': user_message}
        ]

    with st.spinner('Generating test cases'):
        teststeps_response = get_completion_from_messages(st.session_state['messages'])
    st.session_state['messages'].append({'role': 'assistant', 'content': teststeps_response})

    if "teststeps_response" not in st.session_state:
        st.session_state["teststeps_response"] = teststeps_response
    else:
        st.session_state["teststeps_response"] = teststeps_response

# display the test steps
if "teststeps_response" in st.session_state:
    st.subheader("Generated Test steps")

    string_data2 = st.session_state.teststeps_response.replace('\n},\n{', '},\n{')
    data_list2 = json.loads(string_data2)

    st.markdown("#### Test Case:")
    st.write(data_list2['Test_Case'])

    st.markdown("#### Objective:")
    st.write(data_list2['Objective'])

    st.markdown("#### Preconditions:")
    for item in data_list2.get('Preconditions'):
        st.markdown(f"- {item}")

    st.markdown("#### Test Steps:")
    df2 = pd.DataFrame(data_list2['Test_Steps'], columns=["Step", "Action", "Expected_Result"])
    df2 = df2.set_index("Step")
    st.dataframe(df2)

    st.markdown("#### Postconditions:")
    for item in data_list2.get('Postconditions'):
        st.markdown(f"- {item}")

    csv = convert_df(df2)
    st.download_button(
        label="Download the steps",
        data=csv,
        file_name='testcase_steps.csv',
        mime='text/csv',
    )



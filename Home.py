import streamlit as st
import PyPDF2
from streamlit_extras.add_vertical_space import add_vertical_space
from streamlit_extras.app_logo import add_logo
import openai
import json
import pandas as pd
from st_aggrid import AgGrid, GridUpdateMode, ColumnsAutoSizeMode
from st_aggrid.grid_options_builder import GridOptionsBuilder
import time
import base64
import os
from dotenv import load_dotenv, find_dotenv
from pathlib import Path
import tempfile

# read local .env file
_ = load_dotenv(find_dotenv())

openai.api_key = st.secrets["OPENAI_API_KEY"]

delimiter_1 = """####"""
delimiter_2 = """---"""


# Function to return system prompt
def get_system_prompt(document):
    documentation = document

    # print(documentation)

    system_message = f"""
    You are a test engineer working within a software development team that specializes in creating applications for the
    management and tracking of the air cargo value chain. One of the key functions of the application is to facilitate 
    cargo booking processes.
    Today, you have been presented with a documentation for a new feature that the team is planning to develop.
    Your task is to thoroughly understand the documentation provided, which is delimited with XML tags markers. 
    This documentation will outline the details of the new feature, its functionalities, 
    inputs, outputs, and any relevant information necessary for its implementation.
    Once you have grasped the documentation, your role also involves addressing queries related to the newly proposed 
    feature.These queries will be presented to you delimited by {delimiter_2} characters.
    the documentation you find below    
    <document>{documentation}</document>
    """

    return system_message


# Function to return testcase prompt
def get_testcase_prompt():

    user_message_1 = """
    Your task is to thoroughly understand the documentation provided and follow a series of steps below\
    1. Documentation Review: Begin by scanning the document to identify the user stories, 
    the preconditions or post-conditions or the steps related are present in the document.
    2. Test Case Generation: Based on the user stories, your role involves generating a list of different test cases 
    specifically tailored to the application. 
    Please note that you only need to list the different test cases; 
    there is no requirement to outline the steps involved in each test case. 
    The first test case should be to view the temperature requirement in Counter app and Outbound tracking sheet so that 
    the required temperature can be set in the truck for a multi segment flight. 
    The second test case should be to view the temperature requirement in Counter app and Outbound tracking sheet so that 
    the required temperature can be set in the truck a single segment flight. 
    Then list the other test cases from the based on only the user stories.
    No need to list anything under Preconditons and Process flow    
    3. Testing Scope: Keep in mind that you are not required to test every aspect of the software. 
    Instead, focus on the test cases that are relevant to the user stories.

    Your final response should be formatted as a JSON array, with each element containing 
    a test number ("test_no") and the corresponding test ("test"). For example:

    [
      {
        "test_no": "Test 1",
        "test": "Test case A", 
      },
      {
        "test_no": "Test 2",
        "test": "Test case B",
      }
    ]
    """
    return user_message_1


# Function to return test steps prompt
def get_testcase_steps_prompt(steps):
    # table_dict = "{precondtions:[precondtions from documentation]," \
    #              "table:[{step-no:,Type:,Step-description:,expected-result:}]"

    # prompt with pre-defined test steps
    user_message_2 = f"""
    Your current task involves generating a test scenario with steps based on the test no {steps} provided above. 
    This scenario will be formatted as a JSON array, adhering to the specified key-value pairs:

    Test Scenario Steps to be followed:
    1.Generate a brief description based on the user stories in the document
    2.Access the preconditions mentioned in the documentation and list the preconditions as first set of steps.
    3.For the test1 steps refer the Process flow for Multi Segment Flight  mentioned in the document itself. 
    Generate steps based on that process flow and for the test2 refer the Process flow for single Segment Flight  
    mentioned in the document itself. Generate steps based on that process flow
    4.While listing set of steps, review each step in the test scenario and classify them accordingly:
        If the step involves verification or verify step, assign the step type as "verification point."
        If the step involves a procedure other than verification , designate the step type as "test step."
    5. Also generate the expected result of each step accordingly
    6. As you proceed through each step, ensure that you assign accurate step numbers and appropriate step types.
    7.Organize the steps into a JSON structure using the following format:

     {{
        "description": "description generated",
       "precondtions":[{{step_number-no:,step_type:precondtion,step_description:each precondition,expected_result:}}],
       "table_dict": [
         {{
           "step_number":"continuation from preconditions" ,
           "step_type": "test-step",
           "step_description": "test step",
          "expected_result":"expected result of the step"
         }},
         {{
           "step_number": "next number",
           "step_type": "verification-point",
           "step_description": "verify ...",
            "expected_result":"expected result of the step"
         }},
         Include additional steps here...
       ]
       }}
     """
    return user_message_2


# Function to generate a response from ChatGPT
def get_completion_from_messages(messages, model="gpt-3.5-turbo-16k", temperature=0):
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,  # this is the degree of randomness of the model's output
    )
    return response.choices[0].message["content"]


# Function to parse the document
def retrieve_pdf_text(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = """  """
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text


def show_pdf(file_path):
        with open(file_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="800" height="800" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)

@st.cache_data
def convert_df(df):
    # IMPORTANT: Cache the conversion to prevent computation on every rerun
    return df.to_csv().encode('utf-8')


# creating a streamlit app
st.set_page_config(page_title='Home', layout='wide', page_icon='img/logo.png')


st.title('💬 Test Genie')
with st.sidebar:
    # add_vertical_space(1)
    add_logo("img/ibs_logo.png")

st.subheader("Step 1:  Upload Documents")
st.write("""Upload all documents that hold relevant information required for the test case generation. 
Remember, less is not good, but too much is bad as well. So, use your expertise to decide what is relevant. 
Do some trials and watch how the input is affecting the outcome.""")
st.write("Supported Formats: Searchable PDFs, Microsoft Word Documents, Plain Text Files")
st.write("Note: Document preview is currently supported only in PDF format.")
# create a upload file widget for a pdf
pdf_file = st.file_uploader("Upload a PDF file", type=["pdf"])

# if a pdf file is uploaded
if pdf_file:
    # retrieve the text from the pdf
    if "document" not in st.session_state:
        with st.spinner(text="In progress..."):
            time.sleep(1)
            st.session_state.document = retrieve_pdf_text(pdf_file)
        st.session_state.document_path = pdf_file.name


# if there's document, proceed to generate testcases
if "document" in st.session_state:
    time.sleep(0.1)
    with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
        fp = Path(tmp_file.name)
        fp.write_bytes(pdf_file.getvalue())
    col1, col2 = st.columns(2)
    with col1:
        if st.button('View File', key='1'):
            show_pdf(st.session_state.document_path)
    with col2:
        st.button('Close File', key='2')

    if 'messages' not in st.session_state:
        system_prompt = get_system_prompt(st.session_state.document)
        user_message_1 = get_testcase_prompt()
        st.session_state['messages'] = [
            {"role": "system", "content": system_prompt},
            {'role': 'user',
             'content': f"{delimiter_2}{user_message_1}{delimiter_2}"},
        ]
    # print(st.session_state.messages)

    st.subheader("Step 2:  Generate Test Cases")
    st.write("""Once the "Generate Test Cases" button is pressed, the application goes through 
    the content inside uploaded documents and generates test cases based on the set application persona. 
    This persona is kept non-editable for the R&D phase and is set for a test engineer role. 
    This can be made editable in later phases.""")
    st.write("Note: There could be some test cases that do not need further processing. "
             "From the generated test cases, select only those that you need to convert to test steps.")

    if st.button("Generate Test cases"):
        # print(st.session_state['messages'])
        with st.spinner('Generating test cases'):
            testcase_response = get_completion_from_messages(st.session_state['messages'])
        st.session_state['messages'].append({'role': 'assistant', 'content': f"{testcase_response}"})

        if "testcase_response" not in st.session_state:
            st.session_state["testcase_response"] = testcase_response
        else:
            st.session_state["testcase_response"] = testcase_response

# display the testcases
if "testcase_response" in st.session_state:
    # st.write(st.session_state.testcase_response)
    # print(st.session_state)
    data_list = json.loads(st.session_state.testcase_response.replace('\n},\n{', '},\n{'))
    df1 = pd.DataFrame(data_list, columns=['test_no', 'test'])

    # Display generated test cases with checkboxes
    st.subheader("Generated Test Cases")
    gd = GridOptionsBuilder.from_dataframe(df1)
    gd.configure_selection(selection_mode='multiple', use_checkbox=True)
    gridoptions = gd.build()

    grid_table = AgGrid(df1, gridOptions=gridoptions,
                        update_mode=GridUpdateMode.SELECTION_CHANGED,
                        columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS)
    # st.subheader('Test Case selected for test step generation')
    selected_row = grid_table["selected_rows"]
    if not selected_row:
        st.info("Please select the test cases")
        st.stop()

    st.subheader("Step 3: Generate Test Steps")
    st.write("""This is the final step in the R&D version. Once the “Generate Test Steps” button is pressed, 
    the application converts the selected test cases from the above step into detailed 
    test steps in a table format.""")

    if "testcase_response" not in st.session_state:
        st.session_state.selected_rows = selected_row

    else:
        st.session_state.selected_rows = selected_row

    if st.button("Generate Test steps"):
        steps = []
        for items in st.session_state.selected_rows:
            steps.append(items['test_no'])
        user_message_2 = get_testcase_steps_prompt(steps)
        st.session_state['messages'].append({'role': 'user', 'content': f"{delimiter_2}{user_message_2}{delimiter_2}"})

        with st.spinner('Generating test steps'):
            teststeps_response = get_completion_from_messages(st.session_state['messages'])

        if "teststeps_response" not in st.session_state:
            st.session_state.teststeps_response = teststeps_response

        else:
            st.session_state.teststeps_response = teststeps_response

# display the test steps
if "teststeps_response" in st.session_state:
    st.subheader("Generated Test steps")
    st.markdown("#### Description:")

    # st.markdown("#### Pre Conditions:")

    string_data2 = st.session_state.teststeps_response.replace('\n},\n{', '},\n{')
    data_list2 = json.loads(string_data2)
    st.write(data_list2['description'])
    # print(data_list2)
    data_list_final = data_list2['preconditions']
    data_list_final.extend(data_list2['table_dict'])
    print(data_list_final)
    # for item in data_list2.get('preconditions'):
    #     st.markdown(f"- {item}")
    st.markdown("#### Test steps:")
    df2 = pd.DataFrame(data_list_final, columns=["step_number", "step_type", "step_description", "expected_result"])
    df2 = df2.set_index("step_number")
    st.dataframe(df2)

    csv = convert_df(df2)
    st.download_button(
        label="Download the steps",
        data=csv,
        file_name='testcase_steps.csv',
        mime='text/csv',
    )
    st.write("Note: There could be shortcomings in any of the previous steps."
             " Make sure to make a detailed note of your observations in the comments section provided. "
             "This is key to improving the application’s performance. More is always good!")
    # st.subheader("Please leave your comments here")
    # comments = st.text_area(label="Comments", help="Please leave your comments here", label_visibility="hidden")
    # if st.button("Submit"):
    #     print(comments)
    #     st.success('Your suggestions has been noted!', icon="✅")

    with st.form("my_form"):
        st.subheader("Please leave your comments here")
        comments1 = st.text_area(label="Comments about Uploading Documents",
                                 help="Please leave your comments here about Uploading Documents")#, label_visibility="hidden")
        comments2 = st.text_area(label="Comments about Generate Test Cases",
                                 help="Please leave your comments here about Generate Test Cases")#, label_visibility="hidden")
        comments3 = st.text_area(label="Comments about Generate Test steps",
                                 help="Please leave your comments here about Generate Test steps")#, label_visibility="hidden")

        submitted = st.form_submit_button("Submit")
        if submitted:
            st.success('Your suggestions has been noted!', icon="✅")



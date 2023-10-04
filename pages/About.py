import streamlit as st
from streamlit_extras.add_vertical_space import add_vertical_space

st.set_page_config(page_title='About', layout='wide', page_icon='img/logo.png', )


with st.sidebar:
    add_vertical_space(5)

st.title('About')
st.subheader("Welcome to Test Genie - Unleashing the Power of AI in Testing!")

st.write("With Test Genie, we are embarking on an incredible journey towards "
         "revolutionizing the world of software testing. "
         "This AI-driven application is a visionary solution that aims to "
         "transform how test scenarios are created and executed, bringing unprecedented efficiency "
         "and accuracy to the testing process.")
st.write("As we stand at the cutting edge of innovation, "
         "Test Genie accepts user inputs and harnesses "
         "the power of artificial intelligence to automatically generate test scenarios. "
         "Our goal is to empower test engineers with a comprehensive and "
         "ready-to-use format that streamlines their testing efforts.")
st.write("Currently in its early R&D phase, Test Genie is driven by a dynamic and "
         "spirited cross-functional team of ITQ and Digital Innovation experts. "
         "We believe in the potential of this groundbreaking technology, "
         "and initial results have already been promising.")
st.write("We acknowledge that perfection doesn't happen overnight, "
         "and our application is no exception. "
         "As we venture through this exciting phase, "
         "expect some imperfections along the way, but fear not - "
         "we are committed to constant testing, refinement, and improvement.")
st.write("Your feedback is invaluable to us! We encourage you to "
         "share your thoughts and experiences with Test Genie. "
         "Your meaningful feedback will be heard and incorporated to make this solution even more exceptional.")
add_vertical_space(2)
st.write("Dream. Innovate. Inspire.  \n  Test Genie Team")
# st.write("Test Genie Team")




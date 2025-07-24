import streamlit as st

st.set_page_config(
    page_title="IRDAI RAG Chatbot - Test",
    page_icon="🏛️",
    layout="wide"
)

st.title("🏛️ IRDAI RAG Chatbot - Simple Test")

st.write("✅ Streamlit is working!")

if st.button("Test Button"):
    st.success("Button clicked! Streamlit is functioning correctly.")

st.sidebar.title("Test Sidebar")
st.sidebar.write("This is a sidebar test.")

# Test basic chat interface
st.subheader("Test Chat Interface")

if "test_messages" not in st.session_state:
    st.session_state.test_messages = []

if prompt := st.chat_input("Type a test message..."):
    st.session_state.test_messages.append({"role": "user", "content": prompt})
    st.session_state.test_messages.append({"role": "assistant", "content": f"Echo: {prompt}"})

for message in st.session_state.test_messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

st.write("If you can see this, Streamlit is working properly!")

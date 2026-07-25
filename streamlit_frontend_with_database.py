import streamlit as st
from langgraph_backend_with_database import chatbot, extract_all_threads
from langchain_core.messages import HumanMessage
import uuid

# --------------------------------- UTILITY FUNCTIONS ------------------------------------------

def generate_thread_id():    #generates new thread id every time for new chat
    thread_id = uuid.uuid4()
    return thread_id

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(st.session_state['thread_id'])
    st.session_state['message_history'] = []

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id):
    state = chatbot.get_state(config= {'configurable': {'thread_id': thread_id}})
    if not state or 'messages' not in state.values:
        return[]
    else:
        return state.values['messages']

# --------------------------------- SESSION SETUP ------------------------------------------

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:     #thread id added in session
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = extract_all_threads()

add_thread(st.session_state['thread_id'])
# --------------------------------- SIDEBAR UI ------------------------------------------

st.sidebar.title('LANGGRAPH CHATBOT')

if st.sidebar.button('New Chat'):
    reset_chat()

st.sidebar.header('My Conversation')

for thread_id in st.session_state['chat_threads'][::-1]:
    if st.sidebar.button(str(thread_id)):
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id)

        temp_messages = []
        for message in messages:
            if isinstance(message, HumanMessage):
                role= 'User'
            else:
                role= 'AI'
            temp_messages.append({'role': role, 'content': message.content})

        st.session_state['message_history'] = temp_messages

# --------------------------------- MAIN UI ------------------------------------------

# Loading Conversation History
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input('Type Here')

if user_input:

    #first add message to message history
    st.session_state['message_history'].append({'role': 'User', 'content': user_input})
    with st.chat_message('User'):
        st.text(user_input)



    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}

    with st.chat_message('AI'):
        ai_message = st.write_stream(
            message_chunk.content for message_chunk, metadata in chatbot.stream(
                {'messages': [HumanMessage(content=user_input)]},
                config =CONFIG,
                stream_mode = 'messages' 
            )
        )

    #first add message to message history
    st.session_state['message_history'].append({'role': 'AI', 'content': ai_message})
        
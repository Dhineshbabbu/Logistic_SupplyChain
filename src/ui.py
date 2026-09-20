import streamlit as st
import uuid
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage

from src.agent.orchestrator import graph


# =====================================================
# 1. LOAD ENVIRONMENT VARIABLES
# =====================================================

project_root = Path(__file__).resolve().parent.parent

load_dotenv(
    dotenv_path=project_root / ".env"
)


# =====================================================
# 2. PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="Supply Chain Dispatch Console",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =====================================================
# 3. DARK MODE CSS
# =====================================================

st.markdown(
    """
    <style>

    /* ========================================= */
    /* GLOBAL APPLICATION */
    /* ========================================= */

    .stApp {
        background-color: #343541;
        color: #ffffff;
    }

    .main .block-container {
        max-width: 1000px;
        padding-top: 2rem;
        padding-bottom: 7rem;
    }

    /* ========================================= */
    /* SIDEBAR */
    /* ========================================= */

    section[data-testid="stSidebar"] {
        background-color: #202123;
        border-right: 1px solid #444654;
    }

    section[data-testid="stSidebar"] * {
        color: #ffffff !important;
    }

    section[data-testid="stSidebar"] button {
        background-color: #343541;
        border: 1px solid #444654;
        border-radius: 8px;
        margin-bottom: 5px;
        transition: background-color 0.2s ease;
    }

    section[data-testid="stSidebar"] button p {
        color: #ffffff !important;
        font-weight: 500;
    }

    section[data-testid="stSidebar"] button:hover {
        background-color: #444654;
    }

    /* ========================================= */
    /* TITLE */
    /* ========================================= */

    .chat-title {
        color: #ffffff !important;
        font-size: 28px;
        font-weight: 600;
        margin-bottom: 8px;
    }

    .chat-subtitle {
        color: #c5c5d2 !important;
        font-size: 15px;
        margin-bottom: 30px;
    }

    /* ========================================= */
    /* CHAT AREA */
    /* ========================================= */

    div[data-testid="stChatMessage"] {
        background-color: transparent;
        color: #ffffff !important;
    }

    div[data-testid="stChatMessage"] * {
        color: #ffffff !important;
    }

    /* ========================================= */
    /* CHAT INPUT */
    /* ========================================= */

    div[data-testid="stChatInput"] {
        background-color: #343541;
        border-top: 1px solid #444654;
    }

    div[data-testid="stChatInput"] textarea {
        color: #ffffff !important;
        background-color: #40414f !important;
        border: 1px solid #565869 !important;
        border-radius: 10px !important;
    }

    div[data-testid="stChatInput"] textarea::placeholder {
        color: #b5b5c5 !important;
    }

    /* ========================================= */
    /* MARKDOWN */
    /* ========================================= */

    .stMarkdown {
        color: #ffffff;
    }

    /* ========================================= */
    /* DIVIDERS */
    /* ========================================= */

    hr {
        border-color: #444654 !important;
    }

    /* ========================================= */
    /* FOOTER */
    /* ========================================= */

    footer {
        visibility: hidden;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# =====================================================
# 4. SESSION STATE INITIALIZATION
# =====================================================

if "chats" not in st.session_state:
    st.session_state.chats = {}


if "active_chat_id" not in st.session_state:

    first_chat_id = str(uuid.uuid4())

    st.session_state.active_chat_id = first_chat_id

    st.session_state.chats[first_chat_id] = {
        "title": "New Chat",
        "messages": [],
        "thread_id": str(uuid.uuid4())
    }


# =====================================================
# 5. HELPER FUNCTIONS
# =====================================================

def create_new_chat():
    """
    Create a new chat with a unique LangGraph thread.
    """

    chat_id = str(uuid.uuid4())

    st.session_state.chats[chat_id] = {
        "title": "New Chat",
        "messages": [],
        "thread_id": str(uuid.uuid4())
    }

    st.session_state.active_chat_id = chat_id


def get_active_chat():
    """
    Return the currently selected chat.
    """

    return st.session_state.chats[
        st.session_state.active_chat_id
    ]


def get_message_content(message):
    """
    Extract text safely from a LangChain message.
    """

    content = message.content

    if isinstance(content, str):
        return content

    if isinstance(content, list):

        text_parts = []

        for item in content:

            if isinstance(item, dict):

                if "text" in item:
                    text_parts.append(item["text"])

            else:
                text_parts.append(str(item))

        return "\n".join(text_parts)

    return str(content)


def get_final_ai_response(result):
    """
    Return the last AI response that contains text.
    """

    messages = result.get("messages", [])

    for message in reversed(messages):

        if isinstance(message, AIMessage):

            content = get_message_content(message)

            if content.strip():
                return content

    return "I could not generate a response."


def display_message(role, content):

    if role == "user":

        with st.chat_message("user", avatar="👤"):
            st.markdown(content)

    else:

        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(content)


# =====================================================
# 6. SIDEBAR
# =====================================================

with st.sidebar:

    st.markdown(
        """
        <h2 style="color:#ffffff;">
            🚚 Logistics AI
        </h2>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <p style="color:#c5c5d2;">
            Supply Chain Dispatch Console
        </p>
        """,
        unsafe_allow_html=True
    )

    st.divider()

    # New chat
    if st.button(
        "＋ New Chat",
        use_container_width=True
    ):

        create_new_chat()
        st.rerun()

    st.markdown("### All Chats")

    # Chat history
    for chat_id, chat in st.session_state.chats.items():

        title = chat["title"]

        if len(title) > 30:
            title = title[:30] + "..."

        if chat_id == st.session_state.active_chat_id:
            button_label = f"● {title}"
        else:
            button_label = f"  {title}"

        if st.button(
            button_label,
            key=f"chat_button_{chat_id}",
            use_container_width=True
        ):

            st.session_state.active_chat_id = chat_id
            st.rerun()

    st.divider()

    # Clear current chat
    if st.button(
        "🗑️ Clear Current Chat",
        use_container_width=True
    ):

        active_chat = get_active_chat()

        active_chat["messages"] = []
        active_chat["title"] = "New Chat"

        st.rerun()


# =====================================================
# 7. MAIN CHAT INTERFACE
# =====================================================

active_chat = get_active_chat()


st.markdown(
    """
    <div class="chat-title">
        Supply Chain Dispatch Console
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="chat-subtitle">
        Ask questions about logistics, shipments, routes,
        inventory, and disruptions.
    </div>
    """,
    unsafe_allow_html=True
)


# =====================================================
# 8. DISPLAY PREVIOUS MESSAGES
# =====================================================

for message in active_chat["messages"]:

    display_message(
        message["role"],
        message["content"]
    )


# =====================================================
# 9. CHAT INPUT
# =====================================================

user_query = st.chat_input(
    "Ask about your logistics data..."
)


if user_query:

    # Set title from first question
    if len(active_chat["messages"]) == 0:

        active_chat["title"] = user_query[:35]

    # Save user message
    active_chat["messages"].append(
        {
            "role": "user",
            "content": user_query
        }
    )

    # Display user message
    display_message(
        "user",
        user_query
    )

    # LangGraph thread configuration
    thread_config = {
        "configurable": {
            "thread_id": active_chat["thread_id"]
        }
    }

    # Invoke LangGraph
    with st.chat_message("assistant", avatar="🤖"):

        with st.spinner("Analyzing logistics data..."):

            try:

                result = graph.invoke(
                    {
                        "messages": [
                            HumanMessage(
                                content=user_query
                            )
                        ]
                    },
                    config=thread_config
                )

                # Extract final response
                assistant_response = get_final_ai_response(
                    result
                )

                # Display response
                st.markdown(assistant_response)

                # Save assistant response
                active_chat["messages"].append(
                    {
                        "role": "assistant",
                        "content": assistant_response
                    }
                )

            except Exception as error:

                st.error(
                    f"Error while processing your request: {error}"
                )
# config/styles.py

STYLE = """
    <style>
    /* 1. Set the Sidebar Background */
    [data-testid="stSidebar"] {
        background-color: rgb(56, 0, 60) !important;
    }

    /* 2. Set global sidebar text to white/bold (default state) */
    [data-testid="stSidebar"] * {
        color: white !important;
        font-weight: bold !important;
    }

    /* 3. FIX: Target the Selected Value inside the Selectbox */
    [data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] div {
        color: black !important;
        font-weight: normal !important;
    }

    /* Fix number input stepper (+/-) button color in sidebar */
    [data-testid="stSidebar"] .stNumberInput button svg {
        fill: black !important;
    }

    /* Fix selectbox dropdown arrow color in sidebar */
    [data-testid="stSidebar"] .stSelectbox svg {
        fill: black !important;
    }

    /* 4. Target the Dropdown Options (the list that appears when clicked) */
    div[role="listbox"] div {
        color: black !important;
        font-weight: normal !important;
    }

    /* 5. Fix Text in Input/Textarea boxes */
    [data-testid="stSidebar"] input, [data-testid="stSidebar"] textarea {
        color: black !important;
        font-weight: normal !important;
    }
    
    /* 6. Style st.chat_input textarea background to cyan, text to black */
    [data-testid="stChatInput"] textarea {
        color: black !important;
        border-color: rgb(4, 245, 255) !important;
    }
    
    /* 7. Style st.chat_input send button */
    [data-testid="stChatInput"] button {
        background-color: rgb(0, 255, 133) !important;
        color: black !important;
        border: none !important;
        font-weight: bold !important;
    }

    /* --- Chat message bubble background colors --- */


    /* USER messages (Bubble) */
    [data-testid="stChatMessage-user"] {
        background-color: rgb(233, 0, 82) !important;
        border-radius: 12px !important;
        padding: 12px !important;
    }

    /* USER messages (Avatar/Icon Box) */
    [data-testid="stChatMessage-user"] [data-testid="stChatMessageAvatar"] {
        background-color: rgb(233, 0, 82) !important;
        outline: 1px solid white;
    }

    /* ASSISTANT / BOT messages (Bubble) */
    [data-testid="stChatMessage-assistant"] {
        background-color: rgb(4, 245, 255) !important;
        border-radius: 12px !important;
        padding: 12px !important;
    }

    /* ASSISTANT / BOT messages (Avatar/Icon Box) */
    [data-testid="stChatMessage-assistant"] [data-testid="stChatMessageAvatar"] {
        background-color: rgb(4, 245, 255) !important;
    }

    /* Optional: change text color for contrast */
    [data-testid="stChatMessage-user"] * {
        color: white !important;
    }

    [data-testid="stChatMessage-assistant"] * {
        color: black !important;
    }

    /* Fix: Ensure the icon SVG inside the avatar box is visible (e.g. force white or black) */
    [data-testid="stChatMessage"][data-testid="stChatMessage-user"] [data-testid="stChatMessageAvatar"] svg {
        fill: white !important;
    }
    [data-testid="stChatMessage"][data-testid="stChatMessage-assistant"] [data-testid="stChatMessageAvatar"] svg {
        fill: black !important;
    }

    </style>
    """

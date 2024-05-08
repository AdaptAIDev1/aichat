import streamlit as st
import requests
import pyrebase
from openai import OpenAI

# Configure Firebase
firebase_config = {
    "apiKey": "AIzaSyAL9L7uLqlO2Z2RVny6uFAr4j72ix2LoI8",
    "authDomain": "streamlit-test-5ff43.firebaseapp.com",
    "databaseURL": "https://streamlit-test-5ff43.firebaseio.com",
    "projectId": "streamlit-test-5ff43",
    "storageBucket": "streamlit-test-5ff43.appspot.com",
    "messagingSenderId": "356923002998",
    "appId": "1:356923002998:web:71792a47dc65acfd4a4f57",
    "measurementId": "G-M964V5LBPQ"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

# Set up the client for OpenAI
client = OpenAI(base_url="https://api.groq.com/openai/v1/", api_key="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")

def fetch_models():
    url = "http://199.204.135.71:11434/api/tags"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            # Extract model names and only take the first part before the colon
            models = [model["model"].split(':')[0] for model in data.get("models", [])]
            return models
        else:
            return ["Error: Could not retrieve models - HTTP Status " + str(response.status_code)]
    except requests.RequestException as e:
        return ["Error: Request failed - " + str(e)]

def login():
    username = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Password", type='password')
    login_btn = st.sidebar.button("Login")
    if login_btn:
        try:
            user = auth.sign_in_with_email_and_password(username, password)
            st.session_state['user'] = user
            st.success("Logged in successfully")
            st.experimental_rerun()
        except Exception as e:
            st.error("Login failed: {}".format(e))

def logout():
    if st.sidebar.button("Logout"):
        del st.session_state['user']
        st.success("Logged out successfully")
        st.experimental_rerun()

# Configure Streamlit to hide deprecation warnings
st.set_option('deprecation.showPyplotGlobalUse', False)

def send_prompt_to_local_llm(prompt, model_name):
    url = "http://199.204.135.71:11434/api/generate"
    payload = {
        "model": model_name,  # Dynamically set the model based on user selection
        "prompt": prompt,
        "stream": False
    }
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            response_data = response.json()
            if 'response' in response_data:
                return response_data['response']
            else:
                return "Response key is missing in the API response."
        else:
            return f"Error: {response.status_code} - {response.text}"
    except requests.RequestException as e:
        return f"Error sending POST request: {e}"

def main():
    # Display logo if available
    logo_path = "logo.png"
    st.sidebar.image(logo_path, width=300, use_column_width=True)

    if 'user' in st.session_state:
        st.sidebar.text("Logged in as: {}".format(st.session_state['user']['email']))
        # Fetch available models from endpoint
        models = fetch_models()

        if 'messages' not in st.session_state:
            st.session_state.messages = {model: [] for model in models}

        if 'hist_prompt' not in st.session_state:
            st.session_state.hist_prompt = {model: [] for model in models}    
        
        # Create dynamic tabs for each selected model
        tabs = st.tabs(models)

        for tab, model in zip(tabs, models):
            with tab:
                tab_container = st.container()
                chat_container = st.container()

                with tab_container:
                    with chat_container:
                        for message in st.session_state.messages[model]:
                            with st.chat_message(message["role"]):
                                st.markdown(message["content"])

                st.expander("", expanded=True)            

                input_disabled = st.session_state.get('input_disabled', False)
                user_input = st.chat_input(f"Message {model}...", key=f"chat_input_{model}", disabled=input_disabled)

                if prompt := user_input:
                    # Append user message to the current model's history
                    st.session_state.messages[model].append({"role": "user", "content": prompt})
                    with chat_container:
                        with st.chat_message("user"):
                            st.markdown(prompt)

                    # Disable the text input
                    st.session_state['input_disabled'] = True

                    # Call LLM function and get response
                    with st.spinner("Processing..."):
                        prompt_text = ' '.join(st.session_state.hist_prompt[model]) 
                        response = send_prompt_to_local_llm("use this as context of the propmting:  " + prompt_text + " Last user propmt:  "+ prompt, model)
                        st.session_state.hist_prompt[model].append(" user prompt: " + prompt + " your response: " + response)

                    # Display LLM response and update message history
                    with chat_container:
                        with st.chat_message("assistant"):
                            st.markdown(response)
                    st.session_state.messages[model].append({"role": "assistant", "content": response})

                    # Re-enable the text input immediately
                    st.session_state['input_disabled'] = False

        logout()
    else:
        login()

if __name__ == '__main__':
    main()
import os
import streamlit as st  
import api_util as api 
import logging 
import warnings
warnings.filterwarnings("ignore")

logging.basicConfig(level=logging.INFO)

st.set_page_config(
    initial_sidebar_state="collapsed")

## helper strings
help_msg_model_option = "Controls which OpenAI model(s) to use. GPT-4 is more capable, but more expensive."
help_msg_show_usage = "Display token usage and cost estimates for each query."
help_msg_api_key = "This app runs by default on GPT 3.5-turbo, for free. To add the option to retreive responses using GPT-4, add your own key. If you add your own key, both GPT-3.5 and GPT-4 will use your key."
help_msg_model_temperature = "Controls how creativity in AI's response"
help_msg_model_top_p = "Prevents AI from giving certain answers that are too obvious"
help_msg_model_freq_penalty = "Encourages AI to be more diverse in its answers"
help_msg_model_presence_penalty = "Prevents AI from repeating itself too much"
help_msg_max_token = "OpenAI sets a limit on the number of tokens, or individual units of text, that each language model can generate in a single response. For example, text-davinci-003 has a limit of 4000 tokens, while other models have a limit of 2000 tokens. It's important to note that this limit is inclusive of the length of the initial prompt and all messages in the chat session. To ensure the best results, adjust the max token per response based on your specific use case and anticipated dialogue count and length in a session."
helper_app_start = '''This micro-app allows you to generate multiple-choice questions quickly and consistently. 

It work with either GPT-3.5 Turbo, GPT-4, or both.

Optionally, users can modify the AI configuration by opening the left sidebar.
'''
helper_app_need_api_key = "Welcome! This app allows you to test the effectiveness of your prompts using OpenAI's text models: gpt-3.5-turbo, and gpt-4 (if you have access to it). To get started, simply enter your OpenAI API Key below."
helper_api_key_prompt = "The model comparison tool works best with pay-as-you-go API keys. Free trial API keys are limited to 3 requests a minute, not enough to test your prompts. For more information on OpenAI API rate limits, check [this link](https://platform.openai.com/docs/guides/rate-limits/overview).\n\n- Don't have an API key? No worries! Create one [here](https://platform.openai.com/account/api-keys).\n- Want to upgrade your free-trial API key? Just enter your billing information [here](https://platform.openai.com/account/billing/overview)."
helper_api_key_placeholder = "Paste your OpenAI API key here (sk-...)"

## Temporary testing values
test_vals = {
    "test": "Test",
    "content": "Quantum mechanics is a fundamental theory in physics that describes the behavior of nature at and below the scale of atoms.[2]: 1.1  It is the foundation of all quantum physics including quantum chemistry, quantum field theory, quantum technology, and quantum information science. Classical physics, the collection of theories that existed before the advent of quantum mechanics, describes many aspects of nature at an ordinary (macroscopic) scale, but is not sufficient for describing them at small (atomic and subatomic) scales. Most theories in classical physics can be derived from quantum mechanics as an approximation valid at large (macroscopic) scale.[3] Unlike classical systems, quantum systems have bound states quantized to discrete values of energy, momentum, angular momentum, and other quantities; measurements of systems show characteristics of both particles and waves (wave–particle duality); and there are limits to how accurately the value of a physical quantity can be predicted prior to its measurement, given a complete set of initial conditions (the uncertainty principle). Quantum mechanics arose gradually from theories to explain observations that could not be reconciled with classical physics, such as Max Planck's solution in 1900 to the black-body radiation problem, and the correspondence between energy and frequency in Albert Einstein's 1905 paper, which explained the photoelectric effect. These early attempts to understand microscopic phenomena, now known as the old quantum theory, led to the full development of quantum mechanics in the mid-1920s by Niels Bohr, Erwin Schrödinger, Werner Heisenberg, Max Born, Paul Dirac and others. The modern theory is formulated in various specially developed mathematical formalisms. In one of them, a mathematical entity called the wave function provides information, in the form of probability amplitudes, about what measurements of a particle's energy, momentum, and other physical properties may yield.",
    "learning_objective": "Compare quantum mechanics to other explanations of the universe that came before"
}

# Handlers 
def handler_verify_key():
    """Handle OpenAI key verification"""
    # oai_api_key = st.session_state.open_ai_key_input
    oai_api_key = os.getenv('OPENAI_API_KEY')
    o = api.open_ai(api_key=oai_api_key, restart_sequence='|UR|', stop_sequence='|SP|')
    try: 
        # make a call to get available models 
        open_ai_models = o.get_models()
        st.session_state.openai_model_params = [('gpt-3.5-turbo', 4096)]

        # # check to see if the API key has access to gpt-4
        # for m in open_ai_models['data']: 
        #     if m['id'] == 'gpt-4':
        #         st.session_state.openai_model_params = [('gpt-4', 8000), ('gpt-3.5-turbo', 4096)]
        
        st.session_state.openai_models=[model_name for model_name, _ in st.session_state.openai_model_params]            
        st.session_state.openai_models_str = ', '.join(st.session_state.openai_models)

        st.session_state.chat_histories = {model: [] for model in st.session_state.openai_models}
        st.session_state.total_tokens = {model: 0 for model in st.session_state.openai_models}
        st.session_state.prompt_tokens = {model: 0 for model in st.session_state.openai_models}
        st.session_state.completion_tokens = {model: 0 for model in st.session_state.openai_models}
        st.session_state.conversation_cost = {model: 0 for model in st.session_state.openai_models}


        # store OpenAI API key in session states 
        st.session_state.oai_api_key = oai_api_key

        # enable the test
        st.session_state.test_disabled = False 

    except Exception as e: 
        with openai_key_container: 
            st.error(f"{e}")
        logging.error(f"{e}")

def handler_verify_gpt4_key():
    """Handle OpenAI key verification"""
    # oai_api_key = st.session_state.open_ai_key_input
    oai_api_key = st.session_state.custom_question_level
    o = api.open_ai(api_key=oai_api_key, restart_sequence='|UR|', stop_sequence='|SP|')

    try: 
        # make a call to get available models 
        open_ai_models = o.get_models()
        st.session_state.openai_model_params = [('gpt-3.5-turbo', 4096), ('gpt-4', 8000)]

        # check to see if the API key has access to gpt-4
        for m in open_ai_models['data']: 
            if m['id'] == 'gpt-4':
                if st.session_state.model_options == ["GPT-4"]:
                    st.session_state.openai_model_params = [('gpt-4', 8000)]
                elif st.session_state.model_options == ["GPT 3.5-turbo"]:
                    st.session_state.openai_model_params = [('gpt-3.5-turbo', 4096)]
                elif st.session_state.model_options == ["GPT-4", "GPT 3.5-turbo"] or ["GPT 3.5-turbo", "GPT-4"]:
                    st.session_state.openai_model_params = [('gpt-3.5-turbo', 4096),('gpt-4', 8000)]
        
        st.session_state.openai_models=[model_name for model_name, _ in st.session_state.openai_model_params]            
        st.session_state.openai_models_str = ', '.join(st.session_state.openai_models)

        st.session_state.chat_histories = {model: [] for model in st.session_state.openai_models}
        st.session_state.total_tokens = {model: 0 for model in st.session_state.openai_models}
        st.session_state.prompt_tokens = {model: 0 for model in st.session_state.openai_models}
        st.session_state.completion_tokens = {model: 0 for model in st.session_state.openai_models}
        st.session_state.conversation_cost = {model: 0 for model in st.session_state.openai_models}


        # store OpenAI API key in session states 
        st.session_state.oai_api_key = oai_api_key

        # enable the test
        st.session_state.test_disabled = False 

    except Exception as e: 
        with openai_key_container: 
            st.error(f"{e}")
        logging.error(f"{e}")


def handler_fetch_model_responses():
    handler_verify_key()
    # Fetches model responses

    model_config_template = {
        'max_tokens': st.session_state.model_max_tokens,
        'temperature': st.session_state.model_temperature,
        'top_p': st.session_state.model_top_p,
        'frequency_penalty': st.session_state.model_frequency_penalty,
        'presence_penalty': st.session_state.model_presence_penalty
    }

    o = api.open_ai(api_key=st.session_state.oai_api_key, restart_sequence='|UR|', stop_sequence='|SP|')
    progress = 0 
    user_query_moderated = True

    init_prompt = st.session_state.init_prompt

    # Moderate prompt  
    if init_prompt and init_prompt != '':
        try:
            moderation_result = o.get_moderation(user_message = init_prompt)
            if moderation_result['flagged'] == True:
                user_query_moderated = False 
                flagged_categories_str = ", ".join(moderation_result['flagged_categories'])
                with openai_key_container:
                    st.error(f"⚠️ Your prompt has been flagged by OpenAI's content moderation endpoint due to the following categories: {flagged_categories_str}.  \n" +
                    "In order to comply with [OpenAI's usage policy](https://openai.com/policies/usage-policies), we cannot send this prompt to the models. Please modify your prompt and try again.")
        except Exception as e: 
            logging.error(f"{e}")
            with openai_key_container:
                st.error(f"{e}")


    if init_prompt and init_prompt != '' and user_query_moderated == True:
        for index, m in enumerate(st.session_state.openai_models): 
            progress_bar_container.progress(progress, text=f"Getting {m} responses")
            
            try:
                b_r = o.get_ai_response(
                    model_config_dict={**model_config_template, 'model':m}, 
                    init_prompt_msg=mcq_prompt, 
                    messages=st.session_state.chat_histories[m]
                )

                st.session_state.chat_histories[m].append(b_r['messages'][-1])
                st.session_state.total_tokens[m]=b_r['total_tokens']
                st.session_state.prompt_tokens[m]=b_r['prompt_tokens']
                st.session_state.completion_tokens[m]=b_r['completion_tokens']

                if m == 'gpt-4':
                    # $0.03 / 1K prompt tokens + $0.06 / 1K completion tokens
                    st.session_state.conversation_cost[m] = 0.03 * st.session_state.prompt_tokens[m] / 1000 + 0.06 * st.session_state.completion_tokens[m] / 1000
                elif m == 'gpt-3.5-turbo':
                    # 0.5 / 1M prompt tokens + $1.50 / 1M output tokens
                    # st.session_state.conversation_cost[m] = 0.002 * st.session_state.total_tokens[m] / 1000
                    st.session_state.conversation_cost[m] = 0.5 * st.session_state.prompt_tokens[m] / 1000000 + 1.5 * st.session_state.completion_tokens[m] / 1000000

                # update the progress bar 
                progress = (index + 1) / len(st.session_state.openai_models)
                progress_bar_container.progress(progress, text=f"Getting {m} responses")

            except o.OpenAIError as e:
                logging.error(f"{e}")
                with openai_key_container:
                    if e.error_type == "RateLimitError" and str(e) == "OpenAI API Error: You exceeded your current quota, please check your plan and billing details.":
                        st.error(f"{e}  \n  \n**Friendly reminder:** If you are using a free-trial OpenAI API key, this error is caused by the limited rate limits associated with the key. To optimize your experience, we recommend upgrading to the pay-as-you-go OpenAI plan.")
                    else:
                        st.error(f"{e}")

            except Exception as e: 
                with openai_key_container:
                    st.error(f"{e}")
                logging.error(f"{e}")
                    
    progress_bar_container.empty()


def handler_fetch_gpt4_model_responses():
    handler_verify_gpt4_key()
    # Fetches model responses

    model_config_template = {
        'max_tokens': st.session_state.model_max_tokens,
        'temperature': st.session_state.model_temperature,
        'top_p': st.session_state.model_top_p,
        'frequency_penalty': st.session_state.model_frequency_penalty,
        'presence_penalty': st.session_state.model_presence_penalty
    }

    o = api.open_ai(api_key=st.session_state.oai_api_key, restart_sequence='|UR|', stop_sequence='|SP|')
    progress = 0 
    user_query_moderated = True

    init_prompt = st.session_state.init_prompt

    # Moderate prompt  
    if init_prompt and init_prompt != '':
        try:
            moderation_result = o.get_moderation(user_message = init_prompt)
            if moderation_result['flagged'] == True:
                user_query_moderated = False 
                flagged_categories_str = ", ".join(moderation_result['flagged_categories'])
                with openai_key_container:
                    st.error(f"⚠️ Your prompt has been flagged by OpenAI's content moderation endpoint due to the following categories: {flagged_categories_str}.  \n" +
                    "In order to comply with [OpenAI's usage policy](https://openai.com/policies/usage-policies), we cannot send this prompt to the models. Please modify your prompt and try again.")
        except Exception as e: 
            logging.error(f"{e}")
            with openai_key_container:
                st.error(f"{e}")


    if init_prompt and init_prompt != '' and user_query_moderated == True:
        for index, m in enumerate(st.session_state.openai_models): 
            progress_bar_container.progress(progress, text=f"Getting {m} responses")
            
            try:
                b_r = o.get_ai_response(
                    model_config_dict={**model_config_template, 'model':m}, 
                    init_prompt_msg=mcq_prompt, 
                    messages=st.session_state.chat_histories[m]
                )

                st.session_state.chat_histories[m].append(b_r['messages'][-1])
                st.session_state.total_tokens[m]=b_r['total_tokens']
                st.session_state.prompt_tokens[m]=b_r['prompt_tokens']
                st.session_state.completion_tokens[m]=b_r['completion_tokens']

                if m == 'gpt-4':
                    # $0.03 / 1K prompt tokens + $0.06 / 1K completion tokens
                    st.session_state.conversation_cost[m] = 0.03 * st.session_state.prompt_tokens[m] / 1000 + 0.06 * st.session_state.completion_tokens[m] / 1000
                elif m == 'gpt-3.5-turbo':
                    # 0.002 / 1K total tokens 
                    st.session_state.conversation_cost[m] = 0.002 * st.session_state.total_tokens[m] / 1000

                # update the progress bar 
                progress = (index + 1) / len(st.session_state.openai_models)
                progress_bar_container.progress(progress, text=f"Getting {m} responses")

            except o.OpenAIError as e:
                logging.error(f"{e}")
                with openai_key_container:
                    if e.error_type == "RateLimitError" and str(e) == "OpenAI API Error: You exceeded your current quota, please check your plan and billing details.":
                        st.error(f"{e}  \n  \n**Friendly reminder:** If you are using a free-trial OpenAI API key, this error is caused by the limited rate limits associated with the key. To optimize your experience, we recommend upgrading to the pay-as-you-go OpenAI plan.")
                    else:
                        st.error(f"{e}")

            except Exception as e: 
                with openai_key_container:
                    st.error(f"{e}")
                logging.error(f"{e}")
                    
    progress_bar_container.empty()


def handler_start_new_test():
    """Start new test"""
    st.session_state.chat_histories = {model: [] for model in st.session_state.openai_models}
    st.session_state.total_tokens = {model: 0 for model in st.session_state.openai_models}
    st.session_state.prompt_tokens = {model: 0 for model in st.session_state.openai_models}
    st.session_state.completion_tokens = {model: 0 for model in st.session_state.openai_models}
    st.session_state.conversation_cost = {model: 0 for model in st.session_state.openai_models}

def ui_sidebar():
    with st.sidebar:

        st.sidebar.title("OpenAI Configuration")

        if "chat_histories" in st.session_state and len(st.session_state.chat_histories[st.session_state.openai_models[-1]]) > 0: 
            st.button(label="Clear Results", on_click=handler_start_new_test)

            st.write("---")




        model_options = st.text_input("Enter API Key to use GPT-4:", key="custom_question_level", on_change=handler_verify_gpt4_key, placeholder=helper_api_key_placeholder, help= help_msg_api_key)


        if model_options:
            st.multiselect(label="OpenAI Models", options=["GPT-4", "GPT 3.5-turbo"], key='model_options', default=['GPT 3.5-turbo','GPT-4'], help=help_msg_model_option, disabled=st.session_state.test_disabled)
        else:
            st.multiselect(label="OpenAI Models", options=["GPT 3.5-turbo"], default="GPT 3.5-turbo", key='model_options', help=help_msg_model_option, disabled=st.session_state.test_disabled)
        

        # # Check if custom_question_level is in model_options is not empty
        # if model_options and model_options in st.session_state.model_options:
        #     st.multiselect(label="OpenAI Models", options=["GPT-4", "GPT 3.5-turbo"], key='model_options', default=['GPT-4'], help=help_msg_model_option, disabled=st.session_state.test_disabled)
        # elif model_options and model_options not in st.session_state.model_options:
        #     st.multiselect(label="OpenAI Models", options=["GPT 3.5-turbo"], default="GPT 3.5-turbo", key='model_options', help=help_msg_model_option, disabled=st.session_state.test_disabled)



        

        st.checkbox(label="Show usage and cost estimate", key='show_usage', value=True, help=help_msg_show_usage, disabled=st.session_state.test_disabled)
        st.number_input(label="Response Token Limit", key='model_max_tokens', min_value=0, max_value=1000, value=1000, step=50, help=help_msg_max_token, disabled=st.session_state.test_disabled)
        st.slider(label="Temperature", min_value=0.0, max_value=1.0, step=0.1, value=0.7, key='model_temperature', help=help_msg_model_temperature, disabled=st.session_state.test_disabled)
        st.slider(label="Top P", min_value=0.0, max_value=1.0, step=0.1, value=1.0, key='model_top_p', help=help_msg_model_top_p, disabled=st.session_state.test_disabled)
        st.slider(label="Frequency penalty", min_value=0.0, max_value=1.0, step=0.1, value=0.0, key='model_frequency_penalty', help=help_msg_model_freq_penalty, disabled=st.session_state.test_disabled)
        st.slider(label="Presence penalty", min_value=0.0, max_value=1.0, step=0.1, value=0.0, key='model_presence_penalty', help=help_msg_model_presence_penalty, disabled=st.session_state.test_disabled)   
        



def ui_introduction():
    col1, col2 = st.columns([6,4])
    col1.text_input(label="Enter OpenAI API Key", key="open_ai_key_input", type="password", autocomplete="current-password", on_change=handler_verify_key, placeholder=helper_api_key_placeholder, help=helper_api_key_prompt)
    

def ui_test_result(progress_bar_container):

    progress_bar_container.empty()

    if "openai_models" in st.session_state:
        columns = st.columns(len(st.session_state.openai_models))

        for index, model_name in enumerate(st.session_state.openai_models):
            if len(st.session_state.chat_histories[model_name])>0:
                with columns[index]:
                    if 'show_usage' in st.session_state and st.session_state.show_usage:
                        st.write(f'_Usage Statistics: {model_name}_')
                        st.write(f'Total tokens: {st.session_state.total_tokens[model_name]}')
                        st.write(f'Prompt tokens: {st.session_state.prompt_tokens[model_name]}')
                        st.write(f'Completion tokens: {st.session_state.completion_tokens[model_name]}')
                        st.write(f'Total cost: ${st.session_state.conversation_cost[model_name]}')
                        st.write("---")
                    for message in st.session_state.chat_histories[model_name]:
                        # st.write(st.session_state.chat_histories[model_name])
                        if message['role'] == 'user': 
                            st.markdown(f"**User:**  \n{message['message']}")
                        else:
                            st.markdown(f"**AI Response:**  \n{message['message']}")


def _ui_link(url, label, font_awesome_icon):
    st.markdown('<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css">', unsafe_allow_html=True)
    button_code = f'''<a href="{url}" target=_blank><i class="fa {font_awesome_icon}"></i>   {label}</a>'''
    return st.markdown(button_code, unsafe_allow_html=True)



## initialize states 
if "test_disabled" not in st.session_state: 
    st.session_state.test_disabled = False    


## UI 
openai_key_container = st.container()
ui_sidebar()

# st.title('MCQ Generator')
# if "oai_api_key" not in st.session_state: 
#     st.write(helper_app_need_api_key)
#     ui_introduction()

#     st.write("---")



with openai_key_container:
    st.empty()

st.title('MCQ Generator')
st.write("---")
st.markdown(helper_app_start)
st.write("---")

# User input sections
topic_content = st.text_area("Enter the content for question generation:", max_chars=50000, key="topic_content")
original_content_only = st.checkbox("Focus only on the provided text", key="original_content_only")
focus_text = "Please create questions based solely on the provided text." if original_content_only else "Please create questions that incorporate both the provided text as well as your knowledge of the topic."
learning_objective = st.text_area("Specify a learning objective (optional):", max_chars=1000, key="learning_objective")

# Question configuration inputs
questions_num = st.selectbox("Number of questions:", [1, 2, 3, 4, 5], key="questions_num")
correct_ans_num = st.selectbox("Correct answers per question:", [1, 2, 3, 4], key="correct_ans_num")
question_level = st.selectbox("Question difficulty level:", ['Grade School', 'High School', 'University', 'Other'], index=2, key="question_level")
custom_level = st.text_input("Specify other level:", key="custom_level") if question_level == 'Other' else None
if custom_level:
    question_level = custom_level

# Distractors configuration
distractors_num = st.selectbox("Number of distractors:", [1, 2, 3, 4, 5], index=2, key="distractors_num")
distractors_difficulty = st.selectbox("Distractors difficulty" , ['Normal', 'Obvious', 'Challenging'], key="distractors_difficulty")

# Additional Options for feedback and hints
learner_feedback = st.checkbox("Include Learner Feedback?", key="learner_feedback")
hints = st.checkbox("Include hints?", key="hints")
output_format = st.selectbox("Output format:", ['Plain Text', 'OLX'], key="output_format")

mcq_prompt2 = ""
mcq_prompt2 = (
    "Please write " 
    + str(questions_num) + " " 
    + question_level + " level multiple-choice question(s), each with " 
    + str(correct_ans_num) + " correct answer(s) and " 
    + str(distractors_num) + " distractors, "
    + "based on text that I will provide. \n"
)

if original_content_only:
    mcq_prompt2 += "Please create questions based solely on the provided text. \n"
else:
    mcq_prompt2 += "Please create questions that incorporate both the provided text as well as your knowledge of the topic. \n"

if distractors_difficulty == "Obvious":
    mcq_prompt2 += "Distractors should be obviously incorrect options. \n"
elif distractors_difficulty == "Challenging":
    mcq_prompt2 += "Distractors should sound like they could be plausible, but are ultimately incorrect. \n"


if learning_objective:
    mcq_prompt2 += "Focus on meeting the following learning objective(s) : " + learning_objective + ".\n"

if learner_feedback:
    mcq_prompt2 += "Please provide a feedback section for each question that says why the correct answer is the best answer and the other options are incorrect. \n"

if hints:
    mcq_prompt2 += "Also, include a hint for each question.\n"

if output_format == "OLX":
    mcq_prompt2 += "Please write your MCQs in Open edX OLX format"

mcq_prompt2 += """
Format each question like the following:
Question: [Question Text] \n
A) [Answer A] \n
B) [Answer B] \n
....
N) [Answer N] \n

Solution: [Answer A, B...N]\n\n
"""

if learner_feedback:
    mcq_prompt2 += "Feedback: [Feedback]\n\n"

if hints:
    mcq_prompt2 += "Hint: [Hint]\n\n"

mcq_prompt2 += (
    "Here is the text: \n"
    + "===============\n"
    + topic_content
    )

with st.expander("View/edit full prompt"):
    mcq_prompt = st.text_area(
            label="Prompt",
            height=100,
            max_chars=2000,
            value=mcq_prompt2,
            key="init_prompt",
            disabled=st.session_state.test_disabled
        )

# Update the st.button line
st.button(
    label="Generate MCQs",
    on_click=handler_fetch_gpt4_model_responses if st.session_state.custom_question_level  else handler_fetch_model_responses,
    disabled=False
)


with openai_key_container:
    st.empty()

st.write("##### AI Response:")

progress_bar_container = st.empty()
ui_test_result(progress_bar_container)


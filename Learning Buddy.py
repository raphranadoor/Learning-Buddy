import os
import time
from flask import Flask, request, jsonify, render_template
from openai import OpenAI

# Ensure the openai module is imported correctly and is installed.
try:
    import openai
except ModuleNotFoundError:
    raise ModuleNotFoundError("The openai module is not installed. Please install it using 'pip install openai'.")

app = Flask(__name__)

# Initialize the OpenAI client with your API key
api_key = "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"
assistant_id = "asst_DAHO4hzTbddJvCbek8P4s9zj"
if not api_key:
    raise ValueError("OpenAI API key not found. Please set it in your environment variables.")
client = OpenAI(api_key=api_key)

def convert_format(text):
    text= text.replace("\n", "<br>")
    # modify the text so that the markdown ** in converted to bold html text
    bold_open = True
    while "**" in text:
        if bold_open:
            text = text.replace("**", "<b>", 1)
        else:
            text = text.replace("**", "</b>", 1)
        bold_open = not bold_open
    return text

def create_thread():
    thread = client.beta.threads.create()
    return thread

def add_message(thread_id, role, content):
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role=role,
        content=content
    )
    return message

def run_assistant(thread_id, assistant_id):
    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id,
    )
    return run

def get_assistant_response(thread_id, run_id):
    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_id,
        )
        if run_status.status == "completed":
            break
        elif run_status.status == "failed":
            raise Exception("Assistant run failed.")
        time.sleep(2)

    messages_response = client.beta.threads.messages.list(thread_id=thread_id)
    assistant_message = next(
        (msg for msg in messages_response.data if msg.role == "assistant"),
        None
    )
    if assistant_message is None:
        raise Exception("No assistant response found.")
    return assistant_message.content[0].text.value

def call_existing_assistant(assistant_id, user_message):
    thread = create_thread()
    add_message(thread.id, "user", user_message)
    run = run_assistant(thread.id, assistant_id)
    response = get_assistant_response(thread.id, run.id)
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_response', methods=['POST'])
def get_response():
    user_message = request.json['prompt']
    try:
        response = call_existing_assistant(assistant_id, user_message)
        return jsonify({"response": convert_format(response)})
    except Exception as e:
        return jsonify({"error": str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5001)

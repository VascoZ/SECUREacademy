# app/controllers/main_controller.py

from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from app import app, db
from app.models import User, Question, user_question_association
from sqlalchemy import func

import os
from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()
client = OpenAI(
    # defaults to os.environ.get("OPENAI_API_KEY")
    api_key= os.environ.get("OPENAI_API_KEY"),
)

@app.route('/dashboard')
@login_required
def dashboard():
    questions = Question.query.all()
    for question in questions:
        question.completed_by_current_user = current_user in question.completed_by

    return render_template('dashboard.html', questions=questions)

@app.route('/scoreboard')
def scoreboard():
    users = User.query.all()
    question_count = db.session.query(Question).count()
    
    user_data = []
    for user in users:
        completions = db.session.query(user_question_association).filter_by(user_id=user.id).all()
        user_data.append({
            'user': user,
            'progress': len(completions) / question_count,
            'last_completion': max([completion.completion_time for completion in completions], default=None)
        })

    sorted_users = sorted(user_data, key=lambda x: (x['progress'], reversor(x['last_completion']) or datetime.min ), reverse=True)

    return render_template('scoreboard.html', users=sorted_users)

@app.route('/code_scanner')
def code_scanner():
    return render_template('code_scanner.html')

@app.route('/api/scan_code', methods=['POST'])
def scan_code():
    code_to_scan = request.json.get('code', '')

    conversation = [
        {"role": "system", "content": "You are a code scanner for an online learning platform called SECURE Academy. You are scanning the submitted code for vulnerabilities."},
        {"role": "system", "content": "Receive a code to be scanned for vulnerability"},
        {"role": "system", "content": "Give overall vulnerability status of the code, vulnerable or not vulnerable"},
        {"role": "system", "content": "Give brief summary for what the code is"},
        {"role": "system", "content": "Give bugs and their simple explanations of the effect and how to fix"},
        {"role": "system", "content": "Give the code recommendation to fix the found bugs. Do not explain, just fix the code and give the result"},
        {"role": "system", "content": "Return a response for each (status, summary, bugs, and recommendation) using json format {status: vulnerable/not vulnerable, code_summary: blalba, bugs_found: blabla, code_recommendation: blablabla } "},
        {"role": "system", "content": "Do not add addtional sentence. Escpecially one the fixed code part, just send the code right away"},
        {"role": "system", "content": "Wrong fixed code example:\n\nBelow is the revised code snippet with a more robust validation function.\n\n```python\n@app.route('/register', methods=['GET', 'POST'])\ndef register():\n....\n\nRight fixed code example:\n\n@app.route('/register', methods=['GET', 'POST'])\ndef register():\n...."},
        {"role": "system", "content": "Receive prompt from user if and only if it is a source code. Not a question, an instruction or even saying high. Anything received other than a source code, reject the request by responding 'INVALID INPUT'"},
        {"role": "user", "content": code_to_scan},
    ]

    completion = client.chat.completions.create(
        model="gpt-4", 
        messages=conversation,
    )

    response_text = completion.choices[0].message.content.strip()
    
    if response_text.strip() == 'INVALID INPUT':
        return "Invalid input", 400
    
    # Parse the JSON response
    try:
        response_json = json.loads(response_text)
        code_summary = response_json.get('code_summary', '')
        bugs_found = response_json.get('bugs_found', '')
        code_recommendation = response_json.get('code_recommendation', '')
        status = response_json.get('status', '')
    except:
        print(response_text)
        return "Invalid response format from GPT", 500

    response = {
        'status': status.strip(),
        'code_summary': code_summary.strip(),
        'bugs_found': bugs_found.strip(),
        'code_recommendation': code_recommendation.strip(),
    }

    return jsonify(response)

class reversor:
    def __init__(self, obj):
        self.obj = obj

    def __eq__(self, other):
        return other.obj == self.obj

    def __lt__(self, other):
        return other.obj < self.obj
    
    def __gt__(self, other):
        return other.obj > self.obj
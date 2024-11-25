from flask import Flask, render_template, request, jsonify, Response
from main import CurationCrew
import os
from dotenv import load_dotenv
import json

load_dotenv()

app = Flask(__name__)
curator_crew = CurationCrew()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.json.get('query')
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    try:
        crew_output = curator_crew.run_crew(query)
        
        # Ensure we're returning a properly formatted response
        if isinstance(crew_output, dict) and 'error' in crew_output:
            return jsonify({'error': crew_output['error']}), 500
            
        return jsonify(crew_output)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
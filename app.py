from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime

from utils.resume_parser import ResumeParser
from utils.job_matcher import JobMatcher
from utils.skill_extractor import SkillExtractor
from models.database import Database

app = Flask(__name__)
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}

# Initialize components
resume_parser = ResumeParser()
job_matcher = JobMatcher()
skill_extractor = SkillExtractor()
db = Database()

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return jsonify({
        "message": "AI Resume Screener API",
        "version": "1.0",
        "endpoints": {
            "upload_resume": "/api/upload-resume",
            "get_jobs": "/api/jobs",
            "match_jobs": "/api/match-jobs",
            "get_analytics": "/api/analytics"
        }
    })

@app.route('/api/upload-resume', methods=['POST'])
def upload_resume():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # Parse resume
            parsed_data = resume_parser.parse_resume(filepath)

            # Extract skills
            skills = skill_extractor.extract_skills(parsed_data['text'])
            parsed_data['extracted_skills'] = skills

            # Save to database
            resume_id = db.save_resume(parsed_data)
            parsed_data['id'] = resume_id

            # Clean up uploaded file
            os.remove(filepath)

            return jsonify({
                'success': True,
                'data': parsed_data,
                'message': 'Resume parsed successfully'
            })

        return jsonify({'error': 'Invalid file type'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    try:
        jobs = db.get_all_jobs()
        return jsonify({
            'success': True,
            'data': jobs,
            'count': len(jobs)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/match-jobs', methods=['POST'])
def match_jobs():
    try:
        data = request.json
        resume_data = data.get('resume')

        if not resume_data:
            return jsonify({'error': 'Resume data required'}), 400

        # Get all jobs from database
        jobs = db.get_all_jobs()

        # Match resume with jobs
        matches = job_matcher.match_resume_to_jobs(resume_data, jobs)

        return jsonify({
            'success': True,
            'data': matches,
            'count': len(matches)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    try:
        analytics = db.get_analytics()
        return jsonify({
            'success': True,
            'data': analytics
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/add-job', methods=['POST'])
def add_job():
    try:
        job_data = request.json
        job_id = db.save_job(job_data)
        return jsonify({
            'success': True,
            'job_id': job_id,
            'message': 'Job added successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

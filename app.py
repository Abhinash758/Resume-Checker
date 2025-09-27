from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import re
import PyPDF2
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx'}

# Create upload folder
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    """Extract text from PDF file"""
    try:
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        return f"Error reading PDF: {str(e)}"

def extract_text_from_txt(file_path):
    """Extract text from TXT file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        return f"Error reading TXT: {str(e)}"

def analyze_resume_basic(text):
    """Basic AI analysis of resume text"""
    analysis = {
        'name': extract_name(text),
        'email': extract_email(text),
        'phone': extract_phone(text),
        'skills': extract_skills(text),
        'experience_years': estimate_experience(text),
        'education': extract_education(text),
        'summary': generate_summary(text)
    }
    return analysis

def extract_name(text):
    """Extract candidate name from text"""
    lines = text.split('\n')[:5]  # Check first 5 lines
    for line in lines:
        line = line.strip()
        # Skip common header words
        if line and not any(keyword in line.lower() for keyword in 
                          ['resume', 'cv', 'curriculum', 'email', 'phone', 'address']):
            # If line has 2-4 words and reasonable length, it's likely a name
            words = line.split()
            if 2 <= len(words) <= 4 and len(line) < 50:
                return line
    return "Name not found"

def extract_email(text):
    """Extract email address from text"""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    return emails[0] if emails else "Email not found"

def extract_phone(text):
    """Extract phone number from text"""
    phone_patterns = [
        r'\b(?:\+?91[-.\s]?)?[789]\d{9}\b',  # Indian mobile
        r'\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'  # US format
    ]
    
    for pattern in phone_patterns:
        phones = re.findall(pattern, text)
        if phones:
            return phones[0]
    return "Phone not found"

def extract_skills(text):
    """Extract skills from resume text"""
    # Common technical skills database
    skills_database = [
        'Python', 'Java', 'JavaScript', 'React', 'Angular', 'Node.js',
        'HTML', 'CSS', 'SQL', 'MongoDB', 'MySQL', 'PostgreSQL',
        'AWS', 'Azure', 'Docker', 'Kubernetes', 'Git', 'Linux',
        'Machine Learning', 'Data Science', 'AI', 'TensorFlow',
        'Django', 'Flask', 'Spring Boot', 'Express.js',
        'Photoshop', 'Illustrator', 'Figma', 'UI/UX Design',
        'Project Management', 'Agile', 'Scrum', 'Leadership'
    ]
    
    text_lower = text.lower()
    found_skills = []
    
    for skill in skills_database:
        if skill.lower() in text_lower:
            found_skills.append(skill)
    
    return found_skills[:10]  # Return top 10 skills

def estimate_experience(text):
    """Estimate years of experience"""
    # Look for experience patterns
    experience_patterns = [
        r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
        r'experience.*?(\d+)\+?\s*years?',
        r'(\d+)\+?\s*years?\s*in\s*\w+'
    ]
    
    text_lower = text.lower()
    years = []
    
    for pattern in experience_patterns:
        matches = re.findall(pattern, text_lower)
        years.extend([int(match) for match in matches])
    
    if years:
        return f"{max(years)} years"
    else:
        # Count job experiences as rough estimate
        job_keywords = ['worked', 'employed', 'position', 'role', 'company']
        job_count = sum(1 for keyword in job_keywords if keyword in text_lower)
        return f"~{job_count} years (estimated)"

def extract_education(text):
    """Extract education information"""
    education_keywords = [
        'bachelor', 'master', 'phd', 'doctorate', 'degree', 'university', 
        'college', 'b.tech', 'm.tech', 'bca', 'mca', 'be', 'me', 'bsc', 'msc'
    ]
    
    text_lower = text.lower()
    education = []
    lines = text.split('\n')
    
    for line in lines:
        if any(keyword in line.lower() for keyword in education_keywords):
            education.append(line.strip())
    
    return education[:3] if education else ["Education not specified"]

def generate_summary(text):
    """Generate a simple summary"""
    word_count = len(text.split())
    line_count = len(text.split('\n'))
    
    return {
        'total_words': word_count,
        'total_lines': line_count,
        'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'file_analyzed': True
    }

@app.route('/')
def home():
    return jsonify({
        "message": "🤖 AI Resume Screener Backend",
        "status": "READY FOR AI ANALYSIS!",
        "version": "AI Analysis Version",
        "features": [
            "PDF Text Extraction",
            "Contact Information Extraction", 
            "Skills Analysis",
            "Experience Estimation",
            "Education Detection"
        ]
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
            
            # Extract text from file
            if filename.lower().endswith('.pdf'):
                extracted_text = extract_text_from_pdf(filepath)
            elif filename.lower().endswith('.txt'):
                extracted_text = extract_text_from_txt(filepath)
            else:
                extracted_text = "File type not fully supported yet. PDF and TXT work best."
            
            # Perform AI analysis
            if "Error" not in extracted_text:
                ai_analysis = analyze_resume_basic(extracted_text)
                
                # Clean up uploaded file
                os.remove(filepath)
                
                return jsonify({
                    'success': True,
                    'message': '🎉 Resume analyzed successfully!',
                    'data': {
                        'filename': filename,
                        'analysis': ai_analysis,
                        'extracted_text_preview': extracted_text[:200] + "..." if len(extracted_text) > 200 else extracted_text
                    }
                })
            else:
                # Clean up uploaded file
                os.remove(filepath)
                return jsonify({'error': extracted_text}), 500
        
        return jsonify({'error': 'Invalid file type. Upload PDF or TXT files'}), 400
        
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

if __name__ == '__main__':
    print("🚀 Starting AI Resume Screener with Advanced Analysis...")
    print("🧠 Features: PDF extraction, Skills analysis, Contact detection")
    print("🌐 Backend running on: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)

import PyPDF2
import docx
import re
import spacy
from datetime import datetime

class ResumeParser:
    def __init__(self):
        try:
            # Load spaCy English model
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("spaCy English model not found. Install with: python -m spacy download en_core_web_sm")
            self.nlp = None

    def parse_resume(self, file_path):
        """
        Parse resume from various file formats and extract structured information
        """
        try:
            # Extract text based on file type
            if file_path.endswith('.pdf'):
                text = self._extract_text_from_pdf(file_path)
            elif file_path.endswith(('.doc', '.docx')):
                text = self._extract_text_from_docx(file_path)
            elif file_path.endswith('.txt'):
                text = self._extract_text_from_txt(file_path)
            else:
                raise ValueError("Unsupported file format")

            # Parse structured information
            parsed_info = {
                'text': text,
                'name': self._extract_name(text),
                'email': self._extract_email(text),
                'phone': self._extract_phone(text),
                'education': self._extract_education(text),
                'experience': self._extract_experience(text),
                'skills': self._extract_skills_basic(text),
                'parsed_at': datetime.now().isoformat()
            }

            return parsed_info

        except Exception as e:
            raise Exception(f"Error parsing resume: {str(e)}")

    def _extract_text_from_pdf(self, file_path):
        """Extract text from PDF file"""
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")
        return text

    def _extract_text_from_docx(self, file_path):
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            raise Exception(f"Error reading DOCX: {str(e)}")

    def _extract_text_from_txt(self, file_path):
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            raise Exception(f"Error reading TXT: {str(e)}")

    def _extract_name(self, text):
        """Extract candidate name from text"""
        if self.nlp:
            doc = self.nlp(text[:500])  # Check first 500 characters
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    return ent.text.strip()

        # Fallback: extract from first few lines
        lines = text.split('\n')
        for line in lines[:5]:
            line = line.strip()
            if line and not any(keyword in line.lower() for keyword in 
                              ['resume', 'cv', 'curriculum', 'email', 'phone', 'address']):
                if len(line.split()) >= 2 and len(line) < 50:
                    return line
        return "Not Found"

    def _extract_email(self, text):
        """Extract email address from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        return emails[0] if emails else "Not Found"

    def _extract_phone(self, text):
        """Extract phone number from text"""
        phone_patterns = [
            r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b',
            r'\b(?:\+91[-.]?)?([0-9]{10})\b',
            r'\b(?:\+?1[-. ])?\(([0-9]{3})\)[-. ]([0-9]{3})[-. ]([0-9]{4})\b'
        ]

        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            if phones:
                return ''.join(phones[0]) if isinstance(phones[0], tuple) else phones[0]
        return "Not Found"

    def _extract_education(self, text):
        """Extract education information"""
        education_keywords = [
            'bachelor', 'master', 'phd', 'doctorate', 'degree', 'university', 
            'college', 'institute', 'school', 'b.tech', 'm.tech', 'bca', 'mca',
            'be', 'me', 'bsc', 'msc', 'ba', 'ma', 'diploma'
        ]

        education = []
        lines = text.split('\n')

        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in education_keywords):
                # Include context (previous and next lines)
                context = []
                if i > 0:
                    context.append(lines[i-1].strip())
                context.append(line.strip())
                if i < len(lines) - 1:
                    context.append(lines[i+1].strip())

                education.append(' '.join(filter(None, context)))

        return education[:3]  # Return top 3 education entries

    def _extract_experience(self, text):
        """Extract work experience information"""
        experience_keywords = [
            'experience', 'work', 'job', 'position', 'role', 'employed',
            'company', 'organization', 'intern', 'trainee'
        ]

        # Look for date patterns (years)
        date_pattern = r'\b(19|20)\d{2}\b'

        experience = []
        lines = text.split('\n')

        for i, line in enumerate(lines):
            line_lower = line.lower()
            if (any(keyword in line_lower for keyword in experience_keywords) and 
                re.search(date_pattern, line)):

                # Include context
                context = []
                if i > 0:
                    context.append(lines[i-1].strip())
                context.append(line.strip())
                if i < len(lines) - 1:
                    context.append(lines[i+1].strip())

                experience.append(' '.join(filter(None, context)))

        return experience[:5]  # Return top 5 experience entries

    def _extract_skills_basic(self, text):
        """Basic skill extraction (will be enhanced by SkillExtractor)"""
        # Common technical skills
        common_skills = [
            'python', 'java', 'javascript', 'react', 'angular', 'node.js',
            'sql', 'mongodb', 'aws', 'azure', 'docker', 'kubernetes',
            'git', 'linux', 'windows', 'html', 'css', 'bootstrap',
            'machine learning', 'data science', 'ai', 'tensorflow',
            'pytorch', 'flask', 'django', 'spring', 'hibernate'
        ]

        text_lower = text.lower()
        found_skills = []

        for skill in common_skills:
            if skill in text_lower:
                found_skills.append(skill.title())

        return found_skills

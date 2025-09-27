import re
import spacy
from transformers import pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
import json

class SkillExtractor:
    def __init__(self):
        # Initialize spaCy model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("spaCy model not found. Using basic extraction.")
            self.nlp = None

        # Initialize BERT-based NER pipeline for better skill extraction
        try:
            self.ner_pipeline = pipeline("ner", 
                                       model="dbmdz/bert-large-cased-finetuned-conll03-english",
                                       aggregation_strategy="simple")
        except Exception:
            print("BERT model not available. Using rule-based extraction.")
            self.ner_pipeline = None

        # Comprehensive skills database
        self.skills_database = {
            'programming_languages': [
                'Python', 'Java', 'JavaScript', 'TypeScript', 'C++', 'C#', 'C',
                'PHP', 'Ruby', 'Go', 'Rust', 'Swift', 'Kotlin', 'Scala',
                'R', 'MATLAB', 'Perl', 'Shell', 'PowerShell'
            ],
            'web_technologies': [
                'HTML', 'CSS', 'React', 'Angular', 'Vue.js', 'Node.js',
                'Express.js', 'Django', 'Flask', 'Spring Boot', 'ASP.NET',
                'Bootstrap', 'Tailwind CSS', 'jQuery', 'Redux', 'Webpack'
            ],
            'databases': [
                'MySQL', 'PostgreSQL', 'MongoDB', 'Redis', 'SQLite',
                'Oracle', 'SQL Server', 'DynamoDB', 'Cassandra', 'Neo4j',
                'Elasticsearch', 'Firebase', 'Supabase'
            ],
            'cloud_platforms': [
                'AWS', 'Azure', 'Google Cloud', 'Heroku', 'DigitalOcean',
                'Vercel', 'Netlify', 'Firebase', 'IBM Cloud'
            ],
            'tools_frameworks': [
                'Git', 'Docker', 'Kubernetes', 'Jenkins', 'Terraform',
                'Ansible', 'Linux', 'Windows', 'MacOS', 'VS Code',
                'IntelliJ', 'Eclipse', 'Postman', 'Jira', 'Slack'
            ],
            'data_science_ml': [
                'Machine Learning', 'Deep Learning', 'Data Science',
                'Artificial Intelligence', 'TensorFlow', 'PyTorch',
                'Scikit-learn', 'Pandas', 'NumPy', 'Matplotlib',
                'Seaborn', 'Jupyter', 'Apache Spark', 'Hadoop'
            ],
            'soft_skills': [
                'Leadership', 'Communication', 'Problem Solving',
                'Team Work', 'Project Management', 'Agile', 'Scrum',
                'Critical Thinking', 'Creativity', 'Time Management'
            ]
        }

        # Flatten all skills for quick lookup
        self.all_skills = []
        for category, skills in self.skills_database.items():
            self.all_skills.extend([skill.lower() for skill in skills])

    def extract_skills(self, text):
        """
        Extract skills from text using multiple approaches
        """
        extracted_skills = {
            'technical_skills': [],
            'soft_skills': [],
            'all_skills': [],
            'skill_categories': {},
            'confidence_scores': {}
        }

        # Method 1: Rule-based extraction
        rule_based_skills = self._extract_skills_rule_based(text)

        # Method 2: NLP-based extraction
        nlp_skills = self._extract_skills_nlp(text)

        # Method 3: Pattern-based extraction
        pattern_skills = self._extract_skills_patterns(text)

        # Combine and deduplicate results
        all_found_skills = set(rule_based_skills + nlp_skills + pattern_skills)

        # Categorize skills
        for skill in all_found_skills:
            category = self._categorize_skill(skill)
            if category:
                if category not in extracted_skills['skill_categories']:
                    extracted_skills['skill_categories'][category] = []
                extracted_skills['skill_categories'][category].append(skill)

                if category == 'soft_skills':
                    extracted_skills['soft_skills'].append(skill)
                else:
                    extracted_skills['technical_skills'].append(skill)

                extracted_skills['all_skills'].append(skill)

        # Remove duplicates and sort
        extracted_skills['technical_skills'] = sorted(list(set(extracted_skills['technical_skills'])))
        extracted_skills['soft_skills'] = sorted(list(set(extracted_skills['soft_skills'])))
        extracted_skills['all_skills'] = sorted(list(set(extracted_skills['all_skills'])))

        return extracted_skills

    def _extract_skills_rule_based(self, text):
        """Extract skills using rule-based approach"""
        text_lower = text.lower()
        found_skills = []

        # Direct matching
        for skill in self.all_skills:
            if skill in text_lower:
                # Find the original case in skills database
                original_skill = self._find_original_case(skill)
                if original_skill:
                    found_skills.append(original_skill)

        return found_skills

    def _extract_skills_nlp(self, text):
        """Extract skills using NLP techniques"""
        found_skills = []

        if self.nlp:
            doc = self.nlp(text)

            # Extract entities that might be skills
            for ent in doc.ents:
                if ent.label_ in ['ORG', 'PRODUCT', 'LANGUAGE']:
                    skill = ent.text.strip()
                    if self._is_likely_skill(skill):
                        found_skills.append(skill)

        return found_skills

    def _extract_skills_patterns(self, text):
        """Extract skills using common patterns"""
        found_skills = []

        # Patterns for skills sections
        skill_patterns = [
            r'(?i)skills?[:\s-]*([^\n]+)',
            r'(?i)technologies?[:\s-]*([^\n]+)',
            r'(?i)programming languages?[:\s-]*([^\n]+)',
            r'(?i)tools?[:\s-]*([^\n]+)',
            r'(?i)frameworks?[:\s-]*([^\n]+)'
        ]

        for pattern in skill_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                # Split by common delimiters
                skills = re.split(r'[,;|•·]', match)
                for skill in skills:
                    skill = skill.strip()
                    if skill and len(skill) > 1:
                        found_skills.append(skill)

        return found_skills

    def _categorize_skill(self, skill):
        """Categorize a skill into its type"""
        skill_lower = skill.lower()

        for category, skills in self.skills_database.items():
            if any(skill_lower == s.lower() or skill_lower in s.lower() or s.lower() in skill_lower 
                   for s in skills):
                return category

        return None

    def _find_original_case(self, skill_lower):
        """Find the original case of a skill"""
        for category, skills in self.skills_database.items():
            for original_skill in skills:
                if skill_lower == original_skill.lower():
                    return original_skill
        return skill_lower.title()

    def _is_likely_skill(self, text):
        """Check if text is likely to be a skill"""
        # Filter out common non-skill words
        non_skills = ['company', 'university', 'college', 'school', 'department',
                     'team', 'project', 'role', 'position', 'experience']

        text_lower = text.lower()
        if any(non_skill in text_lower for non_skill in non_skills):
            return False

        # Check if it's a known skill
        return text_lower in self.all_skills

    def get_skill_recommendations(self, current_skills, job_skills):
        """Recommend skills based on job requirements"""
        current_skills_lower = [skill.lower() for skill in current_skills]
        missing_skills = []

        for job_skill in job_skills:
            if job_skill.lower() not in current_skills_lower:
                missing_skills.append(job_skill)

        return {
            'missing_skills': missing_skills,
            'skill_gap_percentage': (len(missing_skills) / len(job_skills) * 100) if job_skills else 0,
            'matching_skills': [skill for skill in job_skills if skill.lower() in current_skills_lower]
        }

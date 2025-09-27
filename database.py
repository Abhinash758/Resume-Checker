import json
import os
from datetime import datetime
import uuid

class Database:
    def __init__(self, db_path='data'):
        self.db_path = db_path
        self.ensure_db_structure()

    def ensure_db_structure(self):
        """Create database directories and files if they don't exist"""
        os.makedirs(self.db_path, exist_ok=True)

        # Initialize JSON files
        files = ['resumes.json', 'jobs.json', 'analytics.json']
        for file in files:
            filepath = os.path.join(self.db_path, file)
            if not os.path.exists(filepath):
                with open(filepath, 'w') as f:
                    json.dump([], f)

    def save_resume(self, resume_data):
        """Save parsed resume data"""
        resume_id = str(uuid.uuid4())
        resume_data['id'] = resume_id
        resume_data['created_at'] = datetime.now().isoformat()

        resumes = self._load_json('resumes.json')
        resumes.append(resume_data)
        self._save_json('resumes.json', resumes)

        # Update analytics
        self._update_analytics('resume_uploaded')

        return resume_id

    def save_job(self, job_data):
        """Save job posting data"""
        job_id = str(uuid.uuid4())
        job_data['id'] = job_id
        job_data['created_at'] = datetime.now().isoformat()

        jobs = self._load_json('jobs.json')
        jobs.append(job_data)
        self._save_json('jobs.json', jobs)

        return job_id

    def get_all_jobs(self):
        """Get all job postings"""
        jobs = self._load_json('jobs.json')

        # If no jobs exist, create sample jobs
        if not jobs:
            jobs = self._create_sample_jobs()
            self._save_json('jobs.json', jobs)

        return jobs

    def get_all_resumes(self):
        """Get all resumes"""
        return self._load_json('resumes.json')

    def get_analytics(self):
        """Get system analytics"""
        analytics = self._load_json('analytics.json')

        if not analytics:
            analytics = {
                'total_resumes': 0,
                'total_jobs': len(self.get_all_jobs()),
                'total_matches': 0,
                'popular_skills': {},
                'created_at': datetime.now().isoformat()
            }

        # Update with current data
        analytics['total_resumes'] = len(self.get_all_resumes())
        analytics['total_jobs'] = len(self.get_all_jobs())

        return analytics

    def _update_analytics(self, event_type):
        """Update analytics based on events"""
        analytics = self._load_json('analytics.json')

        if not analytics:
            analytics = {
                'total_resumes': 0,
                'total_jobs': 0,
                'total_matches': 0,
                'popular_skills': {},
                'events': []
            }

        # Update counters
        if event_type == 'resume_uploaded':
            analytics['total_resumes'] = analytics.get('total_resumes', 0) + 1
        elif event_type == 'job_matched':
            analytics['total_matches'] = analytics.get('total_matches', 0) + 1

        # Add event
        analytics.setdefault('events', []).append({
            'type': event_type,
            'timestamp': datetime.now().isoformat()
        })

        # Keep only last 100 events
        analytics['events'] = analytics['events'][-100:]

        self._save_json('analytics.json', analytics)

    def _create_sample_jobs(self):
        """Create sample job postings for demonstration"""
        sample_jobs = [
            {
                'id': 'job1',
                'title': 'Full Stack Developer',
                'company': 'Tech Innovations Inc.',
                'location': 'San Francisco, CA',
                'type': 'Full-time',
                'experience_level': 'Mid-level',
                'salary': '$80,000 - $120,000',
                'description': 'We are looking for a talented Full Stack Developer to join our team. You will be responsible for developing and maintaining web applications using modern technologies.',
                'requirements': 'Bachelor\'s degree in Computer Science or related field. 3+ years of experience in web development. Strong knowledge of JavaScript, React, Node.js, and databases.',
                'skills': [
                    'JavaScript', 'React', 'Node.js', 'HTML', 'CSS', 'MongoDB',
                    'Express.js', 'Git', 'AWS', 'RESTful APIs'
                ],
                'posted_date': '2025-09-15',
                'created_at': datetime.now().isoformat()
            },
            {
                'id': 'job2',
                'title': 'Data Scientist',
                'company': 'Analytics Pro',
                'location': 'New York, NY',
                'type': 'Full-time',
                'experience_level': 'Senior',
                'salary': '$100,000 - $150,000',
                'description': 'Join our data science team to build predictive models and analyze large datasets. You will work on machine learning projects and provide insights to business stakeholders.',
                'requirements': 'Master\'s degree in Data Science, Statistics, or related field. 5+ years of experience in data science. Strong programming skills in Python and R.',
                'skills': [
                    'Python', 'R', 'Machine Learning', 'TensorFlow', 'Scikit-learn',
                    'Pandas', 'NumPy', 'SQL', 'Tableau', 'Statistics'
                ],
                'posted_date': '2025-09-10',
                'created_at': datetime.now().isoformat()
            },
            {
                'id': 'job3',
                'title': 'DevOps Engineer',
                'company': 'CloudTech Solutions',
                'location': 'Austin, TX',
                'type': 'Full-time',
                'experience_level': 'Mid-level',
                'salary': '$90,000 - $130,000',
                'description': 'We need a DevOps Engineer to manage our cloud infrastructure and CI/CD pipelines. You will work with containerization technologies and automate deployment processes.',
                'requirements': 'Bachelor\'s degree in Engineering or related field. 4+ years of DevOps experience. Experience with AWS, Docker, and Kubernetes.',
                'skills': [
                    'AWS', 'Docker', 'Kubernetes', 'Jenkins', 'Terraform',
                    'Linux', 'Python', 'Git', 'CI/CD', 'Monitoring'
                ],
                'posted_date': '2025-09-12',
                'created_at': datetime.now().isoformat()
            },
            {
                'id': 'job4',
                'title': 'Frontend Developer',
                'company': 'UI/UX Masters',
                'location': 'Los Angeles, CA',
                'type': 'Full-time',
                'experience_level': 'Junior',
                'salary': '$60,000 - $85,000',
                'description': 'Looking for a creative Frontend Developer to build beautiful and responsive user interfaces. You will work closely with designers to implement modern web applications.',
                'requirements': 'Bachelor\'s degree preferred. 2+ years of frontend development experience. Strong skills in JavaScript, React, and CSS.',
                'skills': [
                    'JavaScript', 'React', 'HTML', 'CSS', 'Sass', 'Bootstrap',
                    'TypeScript', 'Git', 'Responsive Design', 'Redux'
                ],
                'posted_date': '2025-09-18',
                'created_at': datetime.now().isoformat()
            },
            {
                'id': 'job5',
                'title': 'Mobile App Developer',
                'company': 'Mobile First Co.',
                'location': 'Seattle, WA',
                'type': 'Contract',
                'experience_level': 'Mid-level',
                'salary': '$70 - $90 per hour',
                'description': 'Develop cross-platform mobile applications using React Native or Flutter. You will be responsible for the entire mobile app development lifecycle.',
                'requirements': '3+ years of mobile app development experience. Knowledge of React Native or Flutter. Experience with mobile app deployment.',
                'skills': [
                    'React Native', 'Flutter', 'JavaScript', 'Dart',
                    'iOS Development', 'Android Development', 'Mobile UI/UX',
                    'API Integration', 'Firebase', 'Git'
                ],
                'posted_date': '2025-09-20',
                'created_at': datetime.now().isoformat()
            }
        ]

        return sample_jobs

    def _load_json(self, filename):
        """Load data from JSON file"""
        filepath = os.path.join(self.db_path, filename)
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_json(self, filename, data):
        """Save data to JSON file"""
        filepath = os.path.join(self.db_path, filename)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

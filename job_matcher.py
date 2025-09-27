import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import re

class JobMatcher:
    def __init__(self):
        # Initialize TF-IDF vectorizer for text similarity
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )

        # Initialize Sentence Transformer for semantic similarity
        try:
            self.sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        except Exception:
            print("Sentence Transformer not available. Using TF-IDF only.")
            self.sentence_model = None

    def match_resume_to_jobs(self, resume_data, jobs, top_k=10):
        """
        Match a resume to multiple job postings and return ranked results
        """
        matches = []

        for job in jobs:
            match_score = self._calculate_match_score(resume_data, job)
            matches.append({
                'job': job,
                'match_score': match_score['overall_score'],
                'skill_match': match_score['skill_score'],
                'experience_match': match_score['experience_score'],
                'education_match': match_score['education_score'],
                'text_similarity': match_score['text_similarity'],
                'matching_skills': match_score['matching_skills'],
                'missing_skills': match_score['missing_skills'],
                'recommendations': match_score['recommendations']
            })

        # Sort by match score (descending)
        matches.sort(key=lambda x: x['match_score'], reverse=True)

        return matches[:top_k]

    def _calculate_match_score(self, resume_data, job):
        """
        Calculate comprehensive match score between resume and job
        """
        # Extract job information
        job_text = self._extract_job_text(job)
        resume_text = resume_data.get('text', '')

        # 1. Text Similarity Score (30% weight)
        text_similarity = self._calculate_text_similarity(resume_text, job_text)

        # 2. Skill Match Score (40% weight)
        skill_score, skill_details = self._calculate_skill_match(resume_data, job)

        # 3. Experience Match Score (20% weight)
        experience_score = self._calculate_experience_match(resume_data, job)

        # 4. Education Match Score (10% weight)
        education_score = self._calculate_education_match(resume_data, job)

        # Calculate weighted overall score
        overall_score = (
            text_similarity * 0.3 +
            skill_score * 0.4 +
            experience_score * 0.2 +
            education_score * 0.1
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            resume_data, job, skill_details, overall_score
        )

        return {
            'overall_score': round(overall_score * 100, 2),
            'text_similarity': round(text_similarity * 100, 2),
            'skill_score': round(skill_score * 100, 2),
            'experience_score': round(experience_score * 100, 2),
            'education_score': round(education_score * 100, 2),
            'matching_skills': skill_details['matching_skills'],
            'missing_skills': skill_details['missing_skills'],
            'recommendations': recommendations
        }

    def _extract_job_text(self, job):
        """Extract all text from job posting"""
        text_parts = []

        if 'title' in job:
            text_parts.append(job['title'])
        if 'description' in job:
            text_parts.append(job['description'])
        if 'requirements' in job:
            text_parts.append(job['requirements'])
        if 'skills' in job:
            text_parts.extend(job['skills'])

        return ' '.join(text_parts)

    def _calculate_text_similarity(self, resume_text, job_text):
        """Calculate text similarity using multiple methods"""
        if not resume_text or not job_text:
            return 0.0

        # Method 1: TF-IDF Cosine Similarity
        try:
            tfidf_matrix = self.tfidf_vectorizer.fit_transform([resume_text, job_text])
            tfidf_similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        except Exception:
            tfidf_similarity = 0.0

        # Method 2: Sentence Transformer Similarity (if available)
        if self.sentence_model:
            try:
                embeddings = self.sentence_model.encode([resume_text, job_text])
                semantic_similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
            except Exception:
                semantic_similarity = 0.0
        else:
            semantic_similarity = 0.0

        # Combine both similarities (weighted average)
        if semantic_similarity > 0:
            return (tfidf_similarity * 0.4 + semantic_similarity * 0.6)
        else:
            return tfidf_similarity

    def _calculate_skill_match(self, resume_data, job):
        """Calculate skill matching score"""
        resume_skills = self._extract_resume_skills(resume_data)
        job_skills = job.get('skills', [])

        if not job_skills:
            return 0.5, {'matching_skills': [], 'missing_skills': []}

        # Normalize skills for comparison
        resume_skills_lower = [skill.lower().strip() for skill in resume_skills]
        job_skills_lower = [skill.lower().strip() for skill in job_skills]

        # Find matching skills
        matching_skills = []
        for job_skill in job_skills:
            if job_skill.lower().strip() in resume_skills_lower:
                matching_skills.append(job_skill)

        # Find missing skills
        missing_skills = []
        for job_skill in job_skills:
            if job_skill.lower().strip() not in resume_skills_lower:
                missing_skills.append(job_skill)

        # Calculate score
        skill_score = len(matching_skills) / len(job_skills) if job_skills else 0

        return skill_score, {
            'matching_skills': matching_skills,
            'missing_skills': missing_skills
        }

    def _calculate_experience_match(self, resume_data, job):
        """Calculate experience matching score"""
        resume_experience = resume_data.get('experience', [])
        job_requirements = job.get('requirements', '')

        if not job_requirements:
            return 0.5

        # Extract years of experience from job requirements
        required_years = self._extract_years_from_text(job_requirements)

        # Estimate years from resume (simple heuristic)
        resume_years = len(resume_experience) * 1.5  # Rough estimate

        if required_years == 0:
            return 0.7  # Neutral score if no experience requirement

        # Calculate score based on experience match
        if resume_years >= required_years:
            return 1.0
        else:
            return max(0.0, resume_years / required_years)

    def _calculate_education_match(self, resume_data, job):
        """Calculate education matching score"""
        resume_education = resume_data.get('education', [])
        job_requirements = job.get('requirements', '')

        if not job_requirements:
            return 0.7

        # Check for degree requirements
        education_keywords = ['bachelor', 'master', 'phd', 'degree', 'b.tech', 'm.tech']

        job_req_lower = job_requirements.lower()
        has_education_req = any(keyword in job_req_lower for keyword in education_keywords)

        if not has_education_req:
            return 0.7  # Neutral if no specific education requirement

        # Check if resume has matching education
        resume_text = ' '.join(resume_education).lower()
        has_matching_education = any(keyword in resume_text for keyword in education_keywords)

        return 1.0 if has_matching_education else 0.3

    def _extract_resume_skills(self, resume_data):
        """Extract all skills from resume data"""
        skills = []

        # From extracted skills
        if 'extracted_skills' in resume_data:
            if isinstance(resume_data['extracted_skills'], dict):
                skills.extend(resume_data['extracted_skills'].get('all_skills', []))
            else:
                skills.extend(resume_data['extracted_skills'])

        # From basic skills
        if 'skills' in resume_data:
            skills.extend(resume_data['skills'])

        return list(set(skills))  # Remove duplicates

    def _extract_years_from_text(self, text):
        """Extract years of experience from text"""
        patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
            r'(\d+)\+?\s*years?\s*(?:of\s*)?work',
            r'minimum\s*(\d+)\s*years?',
            r'at\s*least\s*(\d+)\s*years?'
        ]

        text_lower = text.lower()
        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                return int(matches[0])

        return 0

    def _generate_recommendations(self, resume_data, job, skill_details, overall_score):
        """Generate recommendations for improving match"""
        recommendations = []

        # Skill-based recommendations
        if skill_details['missing_skills']:
            recommendations.append({
                'type': 'skills',
                'priority': 'high',
                'message': f"Consider learning these skills: {', '.join(skill_details['missing_skills'][:5])}"
            })

        # Overall match recommendations
        if overall_score < 50:
            recommendations.append({
                'type': 'general',
                'priority': 'medium',
                'message': "Consider tailoring your resume to better match this job description"
            })
        elif overall_score < 70:
            recommendations.append({
                'type': 'general',
                'priority': 'low',
                'message': "Good match! Highlight relevant experience in your cover letter"
            })
        else:
            recommendations.append({
                'type': 'general',
                'priority': 'low',
                'message': "Excellent match! You're well-qualified for this position"
            })

        return recommendations

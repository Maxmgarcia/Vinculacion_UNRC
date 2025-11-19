"""
Matching module for scoring alumnos based on vacante requirements.
Uses NLTK for hard skills matching and TF-IDF with scikit-learn for soft skills.
"""

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import string
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Download required NLTK data (only first time)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('tokenizers/punkt_tab')
except LookupError:
    nltk.download('punkt_tab')

# Initialize components
stemmer = PorterStemmer()
stop_words = set(stopwords.words('spanish') + stopwords.words('english'))


def preprocess_text(text):
    """
    Preprocesses text for NLP analysis.
    - Converts to lowercase
    - Tokenizes
    - Removes punctuation and stopwords
    - Applies stemming
    """
    if not text or not isinstance(text, str):
        return []

    # Lowercase
    text = text.lower()

    # Tokenize
    tokens = word_tokenize(text)

    # Remove punctuation and stopwords, then stem
    processed = []
    for token in tokens:
        if token not in string.punctuation and token not in stop_words:
            stemmed = stemmer.stem(token)
            processed.append(stemmed)

    return processed


def calculate_hard_skills_score(vacante_skills, alumno_skills):
    """
    Calculates hard skills matching score using NLTK tokenization.

    Args:
        vacante_skills: List of hard skills required by vacante
        alumno_skills: List of hard skills possessed by alumno

    Returns:
        Float score between 0 and 10
    """
    if not vacante_skills or len(vacante_skills) == 0:
        return 10.0  # If no skills required, perfect score

    if not alumno_skills or len(alumno_skills) == 0:
        return 0.0  # If alumno has no skills, zero score

    # Preprocess all skills
    vacante_processed = []
    for skill in vacante_skills:
        tokens = preprocess_text(skill)
        vacante_processed.extend(tokens)

    alumno_processed = []
    for skill in alumno_skills:
        tokens = preprocess_text(skill)
        alumno_processed.extend(tokens)

    if not vacante_processed:
        return 10.0

    if not alumno_processed:
        return 0.0

    # Convert to sets for comparison
    vacante_set = set(vacante_processed)
    alumno_set = set(alumno_processed)

    # Calculate Jaccard similarity
    intersection = len(vacante_set.intersection(alumno_set))
    union = len(vacante_set.union(alumno_set))

    if union == 0:
        return 0.0

    jaccard_score = intersection / union

    # Also calculate coverage (how many required skills are covered)
    coverage = intersection / len(vacante_set) if len(vacante_set) > 0 else 0

    # Weighted combination: 60% coverage, 40% jaccard
    final_score = (coverage * 0.6 + jaccard_score * 0.4) * 10

    return round(final_score, 2)


def calculate_soft_skills_score(vacante_skills, alumno_skills):
    """
    Calculates soft skills matching score using TF-IDF and cosine similarity.

    Args:
        vacante_skills: List of soft skills required by vacante
        alumno_skills: List of soft skills possessed by alumno

    Returns:
        Float score between 0 and 10
    """
    if not vacante_skills or len(vacante_skills) == 0:
        return 10.0  # If no skills required, perfect score

    if not alumno_skills or len(alumno_skills) == 0:
        return 0.0  # If alumno has no skills, zero score

    try:
        # Combine all skills into documents
        all_skills = vacante_skills + alumno_skills

        # Create TF-IDF vectorizer
        # Using character n-grams to capture partial word matches
        vectorizer = TfidfVectorizer(
            lowercase=True,
            analyzer='char_wb',  # Character n-grams within word boundaries
            ngram_range=(2, 4),  # 2-4 character n-grams
            max_features=100
        )

        # Fit and transform all skills
        tfidf_matrix = vectorizer.fit_transform(all_skills)

        # Split into vacante and alumno vectors
        vacante_vectors = tfidf_matrix[:len(vacante_skills)]
        alumno_vectors = tfidf_matrix[len(vacante_skills):]

        # Calculate cosine similarity between each vacante skill and all alumno skills
        similarities = cosine_similarity(vacante_vectors, alumno_vectors)

        # For each required skill, find the best match
        max_similarities = []
        for i in range(len(vacante_skills)):
            max_sim = similarities[i].max()
            max_similarities.append(max_sim)

        # Average of best matches
        avg_similarity = np.mean(max_similarities)

        # Convert to 0-10 scale
        # Cosine similarity ranges from 0 to 1 for TF-IDF
        score = avg_similarity * 10

        return round(score, 2)

    except Exception as e:
        print(f"Error calculating soft skills score: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to simple matching
        return calculate_hard_skills_score(vacante_skills, alumno_skills)


def calculate_matching_score(vacante_data, alumno_data):
    """
    Calculates overall matching score between a vacante and an alumno.

    Args:
        vacante_data: Dictionary with vacante information including:
            - habilidadesDuras: list of hard skills
            - habilidadesBlandas: list of soft skills (if exists)
        alumno_data: Dictionary with alumno information including:
            - habilidades_tecnicas: string or list of hard skills
            - habilidades_blandas: string or list of soft skills

    Returns:
        Dictionary with:
            - hard_skills_score: Score for hard skills (0-10)
            - soft_skills_score: Score for soft skills (0-10)
            - final_score: Weighted final score (0-10)
    """
    # Extract and normalize vacante skills
    vacante_hard_skills = vacante_data.get('habilidadesDuras', [])
    vacante_soft_skills = vacante_data.get('habilidadesBlandas', [])

    # If vacante doesn't have soft skills defined, use hard skills as reference
    # This allows flexibility in the matching process
    if not vacante_soft_skills or len(vacante_soft_skills) == 0:
        # No soft skills defined in vacante - only use hard skills
        use_soft_skills = False
    else:
        use_soft_skills = True

    # Extract and normalize alumno skills
    alumno_hard_skills = alumno_data.get('habilidades_tecnicas', '')
    alumno_soft_skills = alumno_data.get('habilidades_blandas', '')

    # Convert string to list if needed (comma-separated)
    if isinstance(alumno_hard_skills, str):
        alumno_hard_skills = [s.strip() for s in alumno_hard_skills.split(',') if s.strip()]

    if isinstance(alumno_soft_skills, str):
        alumno_soft_skills = [s.strip() for s in alumno_soft_skills.split(',') if s.strip()]

    # Calculate hard skills score
    hard_score = calculate_hard_skills_score(vacante_hard_skills, alumno_hard_skills)

    # Calculate soft skills score only if vacante has soft skills defined
    if use_soft_skills:
        soft_score = calculate_soft_skills_score(vacante_soft_skills, alumno_soft_skills)
        # Calculate weighted final score (80% hard, 20% soft)
        final_score = (hard_score * 0.8) + (soft_score * 0.2)
    else:
        # Only hard skills - soft skills get perfect score
        soft_score = 10.0
        # 100% hard skills (since soft skills are not required)
        final_score = hard_score

    return {
        'hard_skills_score': round(hard_score, 2),
        'soft_skills_score': round(soft_score, 2),
        'final_score': round(final_score, 2)
    }


def match_vacante_with_alumnos(vacante_data, alumnos_list):
    """
    Matches a vacante with multiple alumnos and returns scored results.

    Args:
        vacante_data: Dictionary with vacante information
        alumnos_list: List of alumno dictionaries with their data

    Returns:
        List of dictionaries with alumno_id and scores, sorted by final_score descending
    """
    results = []

    for alumno in alumnos_list:
        alumno_id = alumno.get('doc_id')

        if not alumno_id:
            continue

        scores = calculate_matching_score(vacante_data, alumno)

        results.append({
            'alumno_id': alumno_id,
            'alumno_nombre': alumno.get('nombre', 'N/A'),
            'alumno_correo': alumno.get('correo', 'N/A'),
            'hard_skills_score': scores['hard_skills_score'],
            'soft_skills_score': scores['soft_skills_score'],
            'final_score': scores['final_score']
        })

    # Sort by final score descending
    results.sort(key=lambda x: x['final_score'], reverse=True)

    return results


def match_vacante_with_postulantes(vacante_data, postulaciones_list, alumnos_dict):
    """
    Matches a vacante with its postulantes (applicants).

    Args:
        vacante_data: Dictionary with vacante information
        postulaciones_list: List of postulacion documents
        alumnos_dict: Dictionary mapping alumno_id to alumno data

    Returns:
        Dictionary mapping alumno_id to scores
    """
    results = {}

    for postulacion in postulaciones_list:
        # Extract alumno reference
        alumno_ref = postulacion.get('alumnoID')

        if not alumno_ref:
            continue

        # Get alumno_id from reference
        if hasattr(alumno_ref, 'id'):
            alumno_id = alumno_ref.id
        else:
            alumno_id = str(alumno_ref)

        # Get alumno data
        alumno_data = alumnos_dict.get(alumno_id)

        if not alumno_data:
            continue

        # Calculate scores
        scores = calculate_matching_score(vacante_data, alumno_data)

        results[alumno_id] = scores

    return results

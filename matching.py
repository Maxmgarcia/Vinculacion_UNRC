"""
Módulo de matching para puntuar alumnos basado en los requisitos de vacantes.
Usa NLTK para matching de habilidades duras y embeddings de oraciones para análisis semántico de habilidades blandas.
"""

import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import string
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Descargar datos NLTK requeridos (solo la primera vez)
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

# Inicializar componentes
stemmer = PorterStemmer()
stop_words = set(stopwords.words('spanish') + stopwords.words('english'))

# Inicializar modelo de embedding para habilidades blandas
_embedding_model = None

def get_embedding_model():
    """
    Carga de forma y retorna el modelo de sentence transformer.
    Usa un modelo multilingüe que funciona tanto con español como con inglés.
    """
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    return _embedding_model


def preprocess_text(text):
    """
    Preprocesa texto para análisis de NLP.
    - Convierte a minúsculas
    - Tokeniza
    - Remueve puntuación y palabras vacías
    - Aplica stemming
    """
    if not text or not isinstance(text, str):
        return []

    # Convertir a minúsculas
    text = text.lower()

    # Tokenizar
    tokens = word_tokenize(text)

    # Remover puntuación y palabras vacías, luego aplicar stemming
    processed = []
    for token in tokens:
        if token not in string.punctuation and token not in stop_words:
            stemmed = stemmer.stem(token)
            processed.append(stemmed)

    return processed


def calculate_hard_skills_score(vacante_skills, alumno_skills):
    """
    Calcula el puntaje de matching de habilidades duras usando tokenización NLTK.

    Args:
        vacante_skills: Lista de habilidades duras requeridas por la vacante
        alumno_skills: Lista de habilidades duras que posee el alumno

    Returns:
        Puntaje flotante entre 0 y 10
    """
    if not vacante_skills or len(vacante_skills) == 0:
        return 10.0  # Si no se requieren habilidades, puntaje perfecto

    if not alumno_skills or len(alumno_skills) == 0:
        return 0.0  # Si el alumno no tiene habilidades, puntaje cero

    # Preprocesar todas las habilidades
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

    # Convertir a conjuntos para comparación
    vacante_set = set(vacante_processed)
    alumno_set = set(alumno_processed)

    # Calcular similitud de Jaccard
    intersection = len(vacante_set.intersection(alumno_set))
    union = len(vacante_set.union(alumno_set))

    if union == 0:
        return 0.0

    jaccard_score = intersection / union

    # También calcular cobertura (cuántas habilidades requeridas están cubiertas)
    coverage = intersection / len(vacante_set) if len(vacante_set) > 0 else 0

    # Combinación ponderada: 60% cobertura, 40% jaccard
    final_score = (coverage * 0.6 + jaccard_score * 0.4) * 10

    return float(round(final_score, 2))


def calculate_soft_skills_score(vacante_skills, alumno_skills):
    """
    Calcula el puntaje de matching de habilidades blandas usando embeddings semánticos.
    Usa sentence-transformers para comprensión semántica profunda de habilidades.

    Args:
        vacante_skills: Lista de habilidades blandas requeridas por la vacante
        alumno_skills: Lista de habilidades blandas que posee el alumno

    Returns:
        Puntaje flotante entre 0 y 10
    """
    if not vacante_skills or len(vacante_skills) == 0:
        return 10.0  # Si no se requieren habilidades, puntaje perfecto

    if not alumno_skills or len(alumno_skills) == 0:
        return 0.0  # Si el alumno no tiene habilidades, puntaje cero

    try:
        # Obtener el modelo de embedding
        model = get_embedding_model()

        # Generar embeddings para todas las habilidades
        vacante_embeddings = model.encode(vacante_skills, convert_to_tensor=False)
        alumno_embeddings = model.encode(alumno_skills, convert_to_tensor=False)

        # Calcular similitud de coseno entre cada habilidad de vacante y todas las habilidades del alumno
        # Esto nos da similitud semántica, no solo coincidencia léxica
        similarities = cosine_similarity(vacante_embeddings, alumno_embeddings)

        # Para cada habilidad requerida, encontrar la habilidad del alumno con mejor match
        max_similarities = []
        for i in range(len(vacante_skills)):
            max_sim = similarities[i].max()
            max_similarities.append(max_sim)

        # Promedio de los mejores matches entre todas las habilidades requeridas
        avg_similarity = np.mean(max_similarities)

        # Convertir a escala 0-10
        # La similitud de coseno con embeddings va de -1 a 1, pero típicamente de 0 a 1
        # Normalizamos para asegurar que esté en el rango [0, 1] y luego escalamos a 10
        normalized_score = (avg_similarity + 1) / 2  # Mapear [-1, 1] a [0, 1]
        score = normalized_score * 10

        return float(round(score, 2))

    except Exception as e:
        print(f"Error al calcular puntaje de habilidades blandas con embeddings: {e}")
        import traceback
        traceback.print_exc()
        # Recurrir a matching de habilidades duras si falla embeddings
        return calculate_hard_skills_score(vacante_skills, alumno_skills)


def calculate_matching_score(vacante_data, alumno_data):
    """
    Calcula el puntaje general de matching entre una vacante y un alumno.

    Args:
        vacante_data: Diccionario con información de vacante incluyendo:
            - habilidadesDuras: lista de habilidades duras
            - habilidadesBlandas: lista de habilidades blandas (si existe)
        alumno_data: Diccionario con información del alumno incluyendo:
            - habilidades_tecnicas: string o lista de habilidades duras
            - habilidades_blandas: string o lista de habilidades blandas

    Returns:
        Diccionario con:
            - hard_skills_score: Puntaje para habilidades duras (0-10)
            - soft_skills_score: Puntaje para habilidades blandas (0-10)
            - final_score: Puntaje final ponderado (0-10)
    """
    # Extraer y normalizar habilidades de vacante
    vacante_hard_skills = vacante_data.get('habilidadesDuras', [])
    vacante_soft_skills = vacante_data.get('habilidadesBlandas', [])

    # Si la vacante no tiene habilidades blandas definidas, usar habilidades duras como referencia
    # Esto permite flexibilidad en el proceso de matching
    if not vacante_soft_skills or len(vacante_soft_skills) == 0:
        # No hay habilidades blandas definidas en vacante - solo usar habilidades duras
        use_soft_skills = False
    else:
        use_soft_skills = True

    # Extraer y normalizar habilidades del alumno
    alumno_hard_skills = alumno_data.get('habilidades_tecnicas', '')
    alumno_soft_skills = alumno_data.get('habilidades_blandas', '')

    # Convertir string a lista si es necesario (separado por comas)
    if isinstance(alumno_hard_skills, str):
        alumno_hard_skills = [s.strip() for s in alumno_hard_skills.split(',') if s.strip()]

    if isinstance(alumno_soft_skills, str):
        alumno_soft_skills = [s.strip() for s in alumno_soft_skills.split(',') if s.strip()]

    # Calcular puntaje de habilidades duras
    hard_score = calculate_hard_skills_score(vacante_hard_skills, alumno_hard_skills)

    # Calcular puntaje de habilidades blandas solo si la vacante tiene habilidades blandas definidas
    if use_soft_skills:
        soft_score = calculate_soft_skills_score(vacante_soft_skills, alumno_soft_skills)
        # Calcular puntaje final ponderado (80% duras, 20% blandas)
        final_score = (hard_score * 0.8) + (soft_score * 0.2)
    else:
        # Solo habilidades duras - las habilidades blandas obtienen puntaje perfecto
        soft_score = 10.0
        # 100% habilidades duras (ya que no se requieren habilidades blandas)
        final_score = hard_score

    return {
        'hard_skills_score': float(round(hard_score, 2)),
        'soft_skills_score': float(round(soft_score, 2)),
        'final_score': float(round(final_score, 2))
    }


def match_vacante_with_alumnos(vacante_data, alumnos_list):
    """
    Hace match de una vacante con múltiples alumnos y retorna resultados con puntajes.

    Args:
        vacante_data: Diccionario con información de vacante
        alumnos_list: Lista de diccionarios de alumnos con sus datos

    Returns:
        Lista de diccionarios con alumno_id y puntajes, ordenados por final_score descendente
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

    # Ordenar por puntaje final descendente
    results.sort(key=lambda x: x['final_score'], reverse=True)

    return results


def match_vacante_with_postulantes(vacante_data, postulaciones_list, alumnos_dict):
    """
    Hace match de una vacante con sus postulantes (aplicantes).

    Args:
        vacante_data: Diccionario con información de vacante
        postulaciones_list: Lista de documentos de postulación
        alumnos_dict: Diccionario que mapea alumno_id a datos del alumno

    Returns:
        Diccionario que mapea alumno_id a puntajes
    """
    results = {}

    for postulacion in postulaciones_list:
        # Extraer referencia del alumno
        alumno_ref = postulacion.get('alumnoID')

        if not alumno_ref:
            continue

        # Obtener alumno_id de la referencia
        if hasattr(alumno_ref, 'id'):
            alumno_id = alumno_ref.id
        else:
            alumno_id = str(alumno_ref)

        # Obtener datos del alumno
        alumno_data = alumnos_dict.get(alumno_id)

        if not alumno_data:
            continue

        # Calcular puntajes
        scores = calculate_matching_score(vacante_data, alumno_data)

        results[alumno_id] = scores

    return results

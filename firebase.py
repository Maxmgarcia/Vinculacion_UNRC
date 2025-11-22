import firebase_admin
from firebase_admin import credentials, auth, firestore
import os


def initialize_firebase():
    """
    Initializes the Firebase Admin SDK using a service account.
    """
    try:
        # Get the path to the service account key from environment variables
        service_account_key_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

        if not service_account_key_path:
            raise ValueError(
                "GOOGLE_APPLICATION_CREDENTIALS environment variable not set."
            )

        # Ensure the path is absolute or relative to the project root
        if not os.path.isabs(service_account_key_path):
            service_account_key_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)), service_account_key_path
            )

        cred = credentials.Certificate(service_account_key_path)
        firebase_admin.initialize_app(cred)
        print("Firebase Admin SDK initialized successfully.")
    except Exception as e:
        print(f"Error initializing Firebase Admin SDK: {e}")


def get_empresa_by_correo(correo):
    """
    Retrieves empresa document by correo (email).
    Returns the document data if found, otherwise None.
    """
    try:
        db = firestore.client()
        empresas_ref = db.collection("empresas")

        # Query by correo field
        query = empresas_ref.where("correo", "==", correo).limit(1)
        docs = query.stream()

        for doc in docs:
            data = doc.to_dict()
            data["doc_id"] = doc.id  # Include document ID for updates
            return data

        return None
    except Exception as e:
        print(f"Error retrieving empresa by correo: {e}")
        return None


def create_empresa(correo):
    """
    Creates a new empresa document with just the correo field.
    Uses automatic document ID assignment.
    Returns the document ID if successful, otherwise None.
    """
    try:
        db = firestore.client()
        empresas_ref = db.collection("empresas")

        # Create new document with auto-generated ID
        doc_ref = empresas_ref.document()
        doc_ref.set(
            {
                "correo": correo,
                "contactoPrincipal": None,
                "estado": None,
                "giro": None,
                "mun_alcaldia": None,
                "nombre": None,
                "suscripcionActiva": False,
                "created_at": firestore.SERVER_TIMESTAMP,
                "updated_at": firestore.SERVER_TIMESTAMP,
            }
        )

        print(f"New empresa created with correo: {correo}, doc_id: {doc_ref.id}")
        return doc_ref.id
    except Exception as e:
        print(f"Error creating empresa: {e}")
        return None


def update_empresa(doc_id, data):
    """
    Updates an existing empresa document.
    data should be a dict with the fields to update.
    Returns True if successful, False otherwise.
    """
    try:
        db = firestore.client()
        empresas_ref = db.collection("empresas")

        # Add timestamp to the update
        data["updated_at"] = firestore.SERVER_TIMESTAMP

        # Update the document
        empresas_ref.document(doc_id).update(data)

        print(f"Empresa document {doc_id} updated successfully")
        return True
    except Exception as e:
        print(f"Error updating empresa: {e}")
        return False


def get_vacantes_by_empresa_id(empresa_doc_id, include_inactive=False):
    """
    Retrieves all vacantes (job opportunities) for a specific empresa.
    By default, only returns active vacantes (activa=True).

    Args:
        empresa_doc_id: The document ID of the empresa
        include_inactive: If True, returns all vacantes including inactive ones

    Returns a list of vacante documents.
    """
    try:
        db = firestore.client()
        vacantes_ref = db.collection("vacantes")
        empresas_ref = db.collection("empresas")

        # Create a reference to the empresa document
        empresa_ref = empresas_ref.document(empresa_doc_id)

        # Query vacantes where empresaId equals the empresa reference
        query = vacantes_ref.where("empresaId", "==", empresa_ref)

        # Filter by active status if needed
        if not include_inactive:
            query = query.where("activa", "==", True)

        docs = query.stream()

        vacantes = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id  # Include document ID
            vacantes.append(data)

        return vacantes
    except Exception as e:
        print(f"Error retrieving vacantes by empresa ID: {e}")
        return []


def verify_google_id_token(id_token):
    """
    Verifies the Google ID token sent from the client.
    Returns the decoded token (user info) if valid, otherwise None.
    """
    try:
        # Add clock skew tolerance of 60 seconds to handle minor time differences
        decoded_token = auth.verify_id_token(id_token, clock_skew_seconds=60)
        return decoded_token
    except Exception as e:
        print(f"Error verifying ID token: {e}")
        return None


def create_vacante(empresa_doc_id, vacante_data):
    """
    Creates a new vacante document in the vacantes collection.

    Args:
        empresa_doc_id: The document ID of the empresa
        vacante_data: Dictionary containing vacante fields

    Returns:
        The document ID if successful, otherwise None.
    """
    try:
        db = firestore.client()
        vacantes_ref = db.collection("vacantes")
        empresas_ref = db.collection("empresas")

        # Create a reference to the empresa document
        empresa_ref = empresas_ref.document(empresa_doc_id)

        # Create the vacante document with auto-generated ID
        doc_ref = vacantes_ref.document()

        # Prepare the data with empresa reference
        correoEmpresa = vacante_data.get("correoEmpresa", "")
        print(f"DEBUG - correoEmpresa from vacante_data: '{correoEmpresa}'")
        print(f"DEBUG - Full vacante_data keys: {vacante_data.keys()}")

        data = {
            "empresaId": empresa_ref,
            "titulo": vacante_data.get("titulo", ""),
            "descripcion": vacante_data.get("descripcion", ""),
            "requisitos": vacante_data.get("requisitos", ""),
            "modalidad": vacante_data.get("modalidad", ""),
            "tipoContrato": vacante_data.get("tipoContrato", ""),
            "duracion": vacante_data.get("duracion", ""),
            "horario": vacante_data.get("horario", ""),
            "sueldo": vacante_data.get("sueldo"),
            "educación": vacante_data.get("educacion", ""),
            "experienciaRequerida": vacante_data.get("experienciaRequerida", ""),
            "habilidadesDuras": vacante_data.get("habilidadesDuras", []),
            "idiomas": vacante_data.get("idiomas", []),
            "nombreEmpresa": vacante_data.get("nombreEmpresa", ""),
            "correoEmpresa": correoEmpresa,
            "activa": True,
            "created_at": firestore.SERVER_TIMESTAMP,
            "updated_at": firestore.SERVER_TIMESTAMP,
        }

        print(f"DEBUG - Data to be saved to Firestore: {data}")
        doc_ref.set(data)

        print(f"New vacante created with ID: {doc_ref.id}")
        return doc_ref.id
    except Exception as e:
        print(f"Error creating vacante: {e}")
        return None


def get_empresa_by_id(empresa_doc_id):
    """
    Retrieves empresa document by document ID.
    Returns the document data if found, otherwise None.
    """
    try:
        db = firestore.client()
        empresas_ref = db.collection("empresas")
        doc = empresas_ref.document(empresa_doc_id).get()

        if doc.exists:
            data = doc.to_dict()
            data["doc_id"] = doc.id
            return data

        return None
    except Exception as e:
        print(f"Error retrieving empresa by ID: {e}")
        return None


def get_vacante_by_id(vacante_id):
    """
    Retrieves a vacante document by ID.
    Returns the document data if found, otherwise None.
    """
    try:
        db = firestore.client()
        vacantes_ref = db.collection("vacantes")
        doc = vacantes_ref.document(vacante_id).get()

        if doc.exists:
            data = doc.to_dict()
            data["id"] = doc.id
            return data

        return None
    except Exception as e:
        print(f"Error retrieving vacante by ID: {e}")
        return None


def update_vacante(vacante_id, vacante_data):
    """
    Updates an existing vacante document.

    Args:
        vacante_id: The document ID of the vacante
        vacante_data: Dictionary containing fields to update

    Returns:
        True if successful, False otherwise.
    """
    try:
        db = firestore.client()
        vacantes_ref = db.collection("vacantes")

        # Prepare update data (only include fields that are provided)
        update_data = {}

        allowed_fields = [
            "titulo",
            "descripcion",
            "requisitos",
            "modalidad",
            "tipoContrato",
            "duracion",
            "horario",
            "sueldo",
            "educación",
            "experienciaRequerida",
            "habilidadesDuras",
            "idiomas",
            "nombreEmpresa",
            "activa",
        ]

        for field in allowed_fields:
            if field in vacante_data:
                update_data[field] = vacante_data[field]

        # Add updated timestamp
        update_data["updated_at"] = firestore.SERVER_TIMESTAMP

        # Update the document
        vacantes_ref.document(vacante_id).update(update_data)

        print(f"Vacante {vacante_id} updated successfully")
        return True
    except Exception as e:
        print(f"Error updating vacante: {e}")
        return False


def delete_vacante(vacante_id):
    """
    Deletes a vacante document.

    Args:
        vacante_id: The document ID of the vacante to delete

    Returns:
        True if successful, False otherwise.
    """
    try:
        db = firestore.client()
        vacantes_ref = db.collection("vacantes")

        vacantes_ref.document(vacante_id).delete()

        print(f"Vacante {vacante_id} deleted successfully")
        return True
    except Exception as e:
        print(f"Error deleting vacante: {e}")
        return False


def verify_vacante_belongs_to_empresa(vacante_id, empresa_doc_id):
    """
    Verifies that a vacante belongs to a specific empresa.

    Args:
        vacante_id: The document ID of the vacante
        empresa_doc_id: The document ID of the empresa

    Returns:
        True if the vacante belongs to the empresa, False otherwise.
    """
    try:
        vacante = get_vacante_by_id(vacante_id)

        if not vacante:
            return False

        # Get the empresa reference from the vacante
        empresa_ref = vacante.get("empresaId")

        if not empresa_ref:
            return False

        # Compare the empresa document IDs
        return empresa_ref.id == empresa_doc_id
    except Exception as e:
        print(f"Error verifying vacante ownership: {e}")
        return False


def get_all_empresas():
    """
    Retrieves all empresa documents from the empresas collection.
    Returns a list of all empresa documents.
    """
    try:
        db = firestore.client()
        empresas_ref = db.collection("empresas")
        docs = empresas_ref.stream()

        empresas = []
        for doc in docs:
            data = doc.to_dict()
            data["doc_id"] = doc.id  # Include document ID
            empresas.append(data)

        return empresas
    except Exception as e:
        print(f"Error retrieving all empresas: {e}")
        return []


def update_empresa_subscription(doc_id, suscripcion_activa):
    """
    Updates the suscripcionActiva field of an empresa document.

    Args:
        doc_id: The document ID of the empresa
        suscripcion_activa: Boolean value for suscripcionActiva

    Returns:
        True if successful, False otherwise.
    """
    try:
        db = firestore.client()
        empresas_ref = db.collection("empresas")

        # Update only the suscripcionActiva field
        empresas_ref.document(doc_id).update(
            {
                "suscripcionActiva": suscripcion_activa,
                "updated_at": firestore.SERVER_TIMESTAMP,
            }
        )

        print(f"Empresa {doc_id} subscription updated to {suscripcion_activa}")
        return True
    except Exception as e:
        print(f"Error updating empresa subscription: {e}")
        return False

def get_postulaciones_by_alumno_id(alumno_doc_id):
    """
    Retrieves all postulaciones for a specific alumno, including vacante details.
    """
    try:
        db = firestore.client()
        postulaciones_ref = db.collection("postulaciones")
        alumno_ref = db.collection("alumnos").document(alumno_doc_id)

        # Query by alumnoID field
        query = postulaciones_ref.where("alumnoID", "==", alumno_ref)
        docs = query.stream()

        postulaciones = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            
            # Fetch vacante details to get the modalidad
            vacante_ref = data.get("vacanteID")
            if vacante_ref:
                vacante_doc = vacante_ref.get()
                if vacante_doc.exists:
                    vacante_data = vacante_doc.to_dict()
                    # Add modalidad to the postulation data
                    data['modalidad_vacante'] = vacante_data.get('modalidad', 'No especificada')
            
            postulaciones.append(data)
        return postulaciones
    except Exception as e:
        print(f"Error retrieving postulaciones by alumno ID: {e}")
        return []

def count_postulaciones_by_vacante_id(vacante_id):
    """
    Counts the number of postulaciones for a specific vacante.
    """
    try:
        db = firestore.client()
        postulaciones_ref = db.collection("postulaciones")
        vacante_ref = db.collection("vacantes").document(vacante_id)

        # Query by vacanteID field
        query = postulaciones_ref.where("vacanteID", "==", vacante_ref)
        docs = query.stream()

        # Count documents
        count = sum(1 for _ in docs)
        return count
    except Exception as e:
        print(f"Error counting postulaciones by vacante ID: {e}")
        return 0


def create_postulacion(postulacion_data):
    """
    Creates a new postulacion document in Firestore.

    Args:
        postulacion_data: Dictionary containing postulacion information including:
            - alumnoID: ID of the alumno
            - vacanteID: ID of the vacante
            - empresaID: ID of the empresa
            - nombreAlumno, correoAlumno, nombreEmpresa, correoEmpresa, nombreVacante
            - fechaPostulacion: Timestamp
            - mensaje: Optional message from alumno

    Returns:
        The document ID of the created postulacion, or None if error
    """
    try:
        db = firestore.client()
        postulaciones_ref = db.collection("postulaciones")

        # Create references for IDs
        alumno_ref = db.collection("alumnos").document(postulacion_data['alumnoID'])
        vacante_ref = db.collection("vacantes").document(postulacion_data['vacanteID'])
        empresa_ref = db.collection("empresas").document(postulacion_data['empresaID'])

        # Prepare document data with references
        doc_data = {
            'alumnoID': alumno_ref,
            'vacanteID': vacante_ref,
            'empresaID': empresa_ref,
            'nombreAlumno': postulacion_data.get('nombreAlumno', ''),
            'correoAlumno': postulacion_data.get('correoAlumno', ''),
            'nombreEmpresa': postulacion_data.get('nombreEmpresa', ''),
            'correoEmpresa': postulacion_data.get('correoEmpresa', ''),
            'nombreVacante': postulacion_data.get('nombreVacante', ''),
            'fechaPostulacion': postulacion_data.get('fechaPostulacion'),
            'mensaje': postulacion_data.get('mensaje', '')
        }

        # Add the document
        doc_ref = postulaciones_ref.add(doc_data)
        doc_id = doc_ref[1].id

        print(f"Postulacion created successfully with ID: {doc_id}")
        return doc_id

    except Exception as e:
        print(f"Error creating postulacion: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_alumno_by_correo(correo):
    """
    Retrieves alumno document by correo (email).
    Returns the document data if found, otherwise None.
    """
    try:
        db = firestore.client()
        alumnos_ref = db.collection("alumnos")

        # Query by correo field
        query = alumnos_ref.where("correo", "==", correo).limit(1)
        docs = query.stream()

        for doc in docs:
            data = doc.to_dict()
            data["doc_id"] = doc.id  # Include document ID for updates
            return data

        return None
    except Exception as e:
        print(f"Error retrieving alumno by correo: {e}")
        return None


def create_alumno(correo, initial_data=None):
    """
    Creates a new alumno document.
    Uses automatic document ID assignment.
    If initial_data is provided, it's used to populate the document.
    Returns the document ID if successful, otherwise None.
    """
    try:
        db = firestore.client()
        alumnos_ref = db.collection("alumnos")

        # Default data structure
        data = {
            "correo": correo,
            "nombre": None,
            "edad": None,
            "estatus": None,
            "semestre": None,
            "promedio": None,
            "areas_interes": None,
            "habilidades_tecnicas": None,
            "habilidades_blandas": None,
            "idiomas": None,
            "created_at": firestore.SERVER_TIMESTAMP,
        }

        # If initial data is provided, merge it
        if initial_data:
            data.update(initial_data)

        data["updated_at"] = firestore.SERVER_TIMESTAMP

        # Create new document with auto-generated ID
        doc_ref = alumnos_ref.document()
        doc_ref.set(data)

        print(f"New alumno created with correo: {correo}, doc_id: {doc_ref.id}")
        return doc_ref.id
    except Exception as e:
        print(f"Error creating alumno: {e}")
        return None


def update_alumno(doc_id, data):
    """
    Updates an existing alumno document.
    data should be a dict with the fields to update.
    Returns True if successful, False otherwise.
    """
    try:
        db = firestore.client()
        alumnos_ref = db.collection("alumnos")

        # Add timestamp to the update
        data["updated_at"] = firestore.SERVER_TIMESTAMP

        # Update the document
        alumnos_ref.document(doc_id).update(data)

        print(f"Alumno document {doc_id} updated successfully")
        return True
    except Exception as e:
        print(f"Error updating alumno: {e}")
        return False


def get_all_alumnos():
    """
    Retrieves all alumno documents from the alumnos collection.
    Returns a list of all alumno documents.
    """
    try:
        db = firestore.client()
        alumnos_ref = db.collection("alumnos")
        docs = alumnos_ref.stream()

        alumnos = []
        for doc in docs:
            data = doc.to_dict()
            data["doc_id"] = doc.id  # Include document ID
            alumnos.append(data)

        return alumnos
    except Exception as e:
        print(f"Error retrieving all alumnos: {e}")
        return []


def get_alumno_by_id(alumno_doc_id):
    """
    Retrieves alumno document by document ID.
    Returns the document data if found, otherwise None.
    """
    try:
        db = firestore.client()
        alumnos_ref = db.collection("alumnos")
        doc = alumnos_ref.document(alumno_doc_id).get()

        if doc.exists:
            data = doc.to_dict()
            data["doc_id"] = doc.id
            return data

        return None
    except Exception as e:
        print(f"Error retrieving alumno by ID: {e}")
        return None


def save_matching_scores(vacante_id, scores_dict):
    """
    Saves matching scores for a vacante in a subcollection.

    Args:
        vacante_id: The document ID of the vacante
        scores_dict: Dictionary mapping alumno_id to score data

    Returns:
        True if successful, False otherwise.
    """
    try:
        db = firestore.client()
        vacantes_ref = db.collection("vacantes")
        vacante_doc = vacantes_ref.document(vacante_id)

        # Store scores in a subcollection
        scores_ref = vacante_doc.collection("matching_scores")

        # Delete existing scores first
        existing_scores = scores_ref.stream()
        for doc in existing_scores:
            doc.reference.delete()

        # Add new scores
        for alumno_id, score_data in scores_dict.items():
            score_doc = scores_ref.document(alumno_id)
            score_doc.set({
                **score_data,
                "computed_at": firestore.SERVER_TIMESTAMP
            })

        print(f"Matching scores saved for vacante {vacante_id}")
        return True
    except Exception as e:
        print(f"Error saving matching scores: {e}")
        return False


def get_matching_scores(vacante_id):
    """
    Retrieves matching scores for a vacante.

    Args:
        vacante_id: The document ID of the vacante

    Returns:
        Dictionary mapping alumno_id to score data
    """
    try:
        db = firestore.client()
        vacantes_ref = db.collection("vacantes")
        vacante_doc = vacantes_ref.document(vacante_id)
        scores_ref = vacante_doc.collection("matching_scores")

        scores_dict = {}
        docs = scores_ref.stream()

        for doc in docs:
            scores_dict[doc.id] = doc.to_dict()

        return scores_dict
    except Exception as e:
        print(f"Error retrieving matching scores: {e}")
        return {}


def calculate_and_save_single_score(vacante_id, alumno_id):
    """
    Calculates and saves the matching score for a single alumno-vacante pair.

    Args:
        vacante_id: The document ID of the vacante
        alumno_id: The document ID of the alumno

    Returns:
        The calculated scores dict, or None if error
    """
    try:
        from matching import calculate_matching_score

        # Get vacante data
        vacante_data = get_vacante_by_id(vacante_id)
        if not vacante_data:
            print(f"Vacante {vacante_id} not found")
            return None

        # Get alumno data
        alumno_data = get_alumno_by_id(alumno_id)
        if not alumno_data:
            print(f"Alumno {alumno_id} not found")
            return None

        # Calculate score
        scores = calculate_matching_score(vacante_data, alumno_data)

        # Save score to database
        db = firestore.client()
        vacantes_ref = db.collection("vacantes")
        vacante_doc = vacantes_ref.document(vacante_id)
        scores_ref = vacante_doc.collection("matching_scores")

        score_doc = scores_ref.document(alumno_id)
        score_doc.set({
            **scores,
            "computed_at": firestore.SERVER_TIMESTAMP
        })

        print(f"Score calculated and saved for alumno {alumno_id} on vacante {vacante_id}: {scores['final_score']}/10")
        return scores

    except Exception as e:
        print(f"Error calculating and saving single score: {e}")
        import traceback
        traceback.print_exc()
        return None

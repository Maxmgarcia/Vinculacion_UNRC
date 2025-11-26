"""
app.py - Lógica del Asistente de Habilidades
Este archivo contiene el modelo y la lógica de negocio del chatbot.
Importa este archivo desde chat.py para la interfaz.
"""

from transformers import pipeline, set_seed
import json
import re # Necesario para limpiar la respuesta de GPT-2

class AsistenteHabilidades:
    """
    Clase principal que maneja la lógica del asistente de habilidades.
    Procesa preguntas y devuelve sugerencias de habilidades técnicas y blandas.
    """
    
    # Nuevo: Instrucciones para GPT-2 (Prompt Engineering)
    SYSTEM_PROMPT = (
        "Eres un asistente de reclutamiento experto. Tu única tarea es ofrecer sugerencias "
        "concisas y claras sobre las habilidades blandas y técnicas que un profesional "
        "debe incluir en su perfil para la carrera mencionada en la pregunta. Responde en español y de manera profesional."
    )

    def __init__(self, usar_gpt2=True):
        """
        Inicializa el asistente de habilidades.
        
        Args:
            usar_gpt2 (bool): Si es True, carga el modelo GPT-2 de Hugging Face.
                            Por defecto False para inicio más rápido.
        """
        self.usar_gpt2 = usar_gpt2
        self.generator = None
        
        if usar_gpt2:
            print("⏳ Cargando modelo GPT-2 de Hugging Face...")
            try:
                # Modificando max_length a un valor más flexible para respuestas largas
                self.generator = pipeline(
                    'text-generation', 
                    model='gpt2',
                    max_length=150, # Aumentado a 150
                    device=-1     # Usar CPU, cambia a 0 para GPU
                )
                set_seed(42)
                print("✅ Modelo GPT-2 cargado exitosamente")
            except Exception as e:
                print(f"⚠️ No se pudo cargar GPT-2: {e}")
                print("Continuando sin generación de texto...")
                self.usar_gpt2 = False
        
        # Base de conocimiento de habilidades
        self.conocimiento = {
            "habilidades_tecnicas": {
                "programacion": [
                    "Python", "JavaScript", "Java", "C++", "C#", 
                    "PHP", "Ruby", "Go", "Rust", "TypeScript"
                ],
                "web": [
                    "HTML/CSS", "React", "Angular", "Vue.js", "Node.js", 
                    "Django", "Flask", "FastAPI", "Express", "Tailwind CSS"
                ],
                "datos": [
                    "SQL", "MongoDB", "PostgreSQL", "MySQL", "Redis",
                    "Data Analysis", "Machine Learning", "Pandas", "NumPy"
                ],
                "herramientas": [
                    "Git", "Docker", "Kubernetes", "AWS", "Azure", 
                    "Linux", "APIs REST", "CI/CD", "Jenkins", "GitHub Actions"
                ],
                "mobile": [
                    "Android", "iOS", "React Native", "Flutter", 
                    "Kotlin", "Swift", "Xamarin"
                ],
                "otros": [
                    "Excel Avanzado", "Power BI", "Tableau", "Figma",
                    "Photoshop", "Testing", "Selenium", "Jest"
                ]
            },
            "habilidades_blandas": {
                "comunicacion": [
                    "Comunicación efectiva", "Presentaciones públicas", 
                    "Escucha activa", "Redacción profesional", "Storytelling"
                ],
                "colaboracion": [
                    "Trabajo en equipo", "Colaboración remota", 
                    "Networking", "Empatía", "Resolución de conflictos"
                ],
                "liderazgo": [
                    "Liderazgo", "Toma de decisiones", "Delegación", 
                    "Motivación de equipos", "Visión estratégica"
                ],
                "personales": [
                    "Adaptabilidad", "Creatividad", "Pensamiento crítico", 
                    "Resolución de problemas", "Iniciativa", "Resiliencia"
                ],
                "organizacion": [
                    "Gestión del tiempo", "Organización", "Planificación", 
                    "Proactividad", "Atención al detalle", "Multitasking"
                ]
            }
        }
    
    def obtener_todas_habilidades(self, tipo):
        """
        Obtiene todas las habilidades de un tipo específico.
        """
        if tipo == "tecnicas":
            return [
                h for categoria in self.conocimiento["habilidades_tecnicas"].values() 
                for h in categoria
            ]
        else:
            return [
                h for categoria in self.conocimiento["habilidades_blandas"].values() 
                for h in categoria
            ]
    
    def obtener_habilidades_por_categoria(self, categoria):
        """
        Obtiene habilidades de una categoría específica.
        """
        # Buscar en técnicas
        if categoria in self.conocimiento["habilidades_tecnicas"]:
            return self.conocimiento["habilidades_tecnicas"][categoria]
        
        # Buscar en blandas
        if categoria in self.conocimiento["habilidades_blandas"]:
            return self.conocimiento["habilidades_blandas"][categoria]
        
        return []
    
    def generar_respuesta_gpt2(self, prompt):
        """
        Genera una respuesta usando GPT-2 (si está habilitado) y la limpia.
        """
        if not self.usar_gpt2 or not self.generator:
            return "GPT-2 no está disponible en este momento."
        
        try:
            # Combinar el prompt de sistema con la pregunta real
            full_prompt = f"{self.SYSTEM_PROMPT} Pregunta del alumno: {prompt}"
            
            resultado = self.generator(full_prompt, max_length=150, num_return_sequences=1)
            generated_text = resultado[0]['generated_text']
            
            # Limpieza: Intentar eliminar el prompt del sistema de la respuesta
            response_text = generated_text.replace(full_prompt, "").strip()
            
            # A veces GPT-2 repite parte del prompt de entrada, lo limpiamos de nuevo
            response_text = re.sub(r'^(Pregunta del alumno:\s?.*)', '', response_text, flags=re.IGNORECASE).strip()
            
            if len(response_text) < 20: # Si la respuesta es demasiado corta, devolver algo genérico
                 return "Disculpa, el modelo generativo tuvo una respuesta muy corta. Intenta ser más específico."
                 
            return response_text
            
        except Exception as e:
            print(f"Error en GPT-2: {e}")
            return f"Error al generar respuesta: {str(e)}"
    
    def procesar_pregunta(self, pregunta):
        """
        Procesa una pregunta del usuario y devuelve la respuesta apropiada.
        """
        pregunta_lower = pregunta.lower()
        
        # --- Lógica de Coincidencia (rápida) ---
        
        # Intenciones: Habilidades técnicas
        if any(palabra in pregunta_lower for palabra in ["técnica", "tecnica", "programación", "programacion", "tecnolog"]):
            habilidades = self.obtener_todas_habilidades("tecnicas")
            return {
                "tipo": "lista_tecnicas",
                "mensaje": "🔧 Aquí tienes habilidades técnicas que podrías incluir en tu perfil:",
                "habilidades": habilidades[:15]
            }
        
        # Intenciones: Habilidades blandas
        elif any(palabra in pregunta_lower for palabra in ["blanda", "soft", "personal", "interpersonal"]):
            habilidades = self.obtener_todas_habilidades("blandas")
            return {
                "tipo": "lista_blandas",
                "mensaje": "💡 Estas son algunas habilidades blandas importantes para tu perfil:",
                "habilidades": habilidades[:15]
            }
        
        # Intenciones: Diferencias
        elif "diferencia" in pregunta_lower:
            return {
                "tipo": "explicacion",
                "mensaje": "📚 **Diferencias entre habilidades:**\n\n" +
                             "🔧 **Habilidades Técnicas (Hard Skills)**\n" +
                             "Son conocimientos específicos y medibles que se aprenden mediante " +
                             "estudio o práctica. Ejemplos: lenguajes de programación, herramientas, " +
                             "software específico.\n\n" +
                             "💡 **Habilidades Blandas (Soft Skills)**\n" +
                             "Son cualidades personales e interpersonales que afectan cómo trabajas. " +
                             "Ejemplos: comunicación, liderazgo, trabajo en equipo, adaptabilidad.\n\n" +
                             "💼 Ambas son importantes para las empresas."
            }
        
        # Categorías específicas - Web
        elif any(palabra in pregunta_lower for palabra in ["web", "frontend", "backend", "fullstack"]):
            return {
                "tipo": "categoria",
                "mensaje": "🌐 Habilidades para desarrollo web:",
                "habilidades": self.conocimiento["habilidades_tecnicas"]["web"]
            }
        
        # Categorías específicas - Datos
        elif any(palabra in pregunta_lower for palabra in ["dato", "data", "database", "base de datos", "analytics"]):
            return {
                "tipo": "categoria",
                "mensaje": "📊 Habilidades para trabajo con datos:",
                "habilidades": self.conocimiento["habilidades_tecnicas"]["datos"]
            }
        
        # Categorías específicas - Mobile
        elif any(palabra in pregunta_lower for palabra in ["móvil", "movil", "mobile", "app", "android", "ios"]):
            return {
                "tipo": "categoria",
                "mensaje": "📱 Habilidades para desarrollo móvil:",
                "habilidades": self.conocimiento["habilidades_tecnicas"]["mobile"]
            }
        
        # Categorías específicas - Comunicación
        elif "comunicación" in pregunta_lower or "comunicacion" in pregunta_lower:
            return {
                "tipo": "categoria",
                "mensaje": "🗣️ Habilidades de comunicación:",
                "habilidades": self.conocimiento["habilidades_blandas"]["comunicacion"]
            }
        
        # Categorías específicas - Liderazgo
        elif "liderazgo" in pregunta_lower or "líder" in pregunta_lower or "lider" in pregunta_lower:
            return {
                "tipo": "categoria",
                "mensaje": "👥 Habilidades de liderazgo:",
                "habilidades": self.conocimiento["habilidades_blandas"]["liderazgo"]
            }
        
        # Ayuda / No entiendo
        elif any(palabra in pregunta_lower for palabra in ["ejemplo", "ayuda", "help", "qué puedes", "que puedes"]):
            return {
                "tipo": "ayuda",
                "mensaje": "💬 **¿Cómo puedo ayudarte?**\n\n" +
                             "Puedo asistirte con:\n\n" +
                             "📌 **Por tipo:**\n" +
                             "• Habilidades técnicas generales\n" +
                             "• Habilidades blandas importantes\n" +
                             "• Diferencias entre ambas\n\n" +
                             "📌 **Por área específica:**\n" +
                             "• Desarrollo web (frontend/backend)\n" +
                             "• Análisis de datos\n" +
                             "• Desarrollo móvil\n" +
                             "• Comunicación y liderazgo\n\n" +
                             "💡 Solo pregúntame sobre el área que te interesa."
            }
        
        # --- Generación de Texto con GPT-2 (Fallback para Preguntas no mapeadas) ---
        
        elif self.usar_gpt2 and self.generator:
            print(f"🧠 Usando GPT-2 para pregunta: '{pregunta}'")
            respuesta_gpt = self.generar_respuesta_gpt2(pregunta)
            
            # Devolvemos la respuesta generada
            return {
                "tipo": "generativo",
                "mensaje": f"🤖 Respondiendo con IA generativa:\n\n{respuesta_gpt}"
            }
            
        # Respuesta genérica si GPT-2 está deshabilitado o la pregunta es irrelevante
        else:
            return {
                "tipo": "generico",
                "mensaje": "🤔 No estoy seguro de entender tu pregunta.\n\n" +
                             "Intenta preguntarme sobre:\n" +
                             "• Habilidades técnicas o blandas\n" +
                             "• Áreas específicas (web, datos, mobile)\n" +
                             "• Diferencias entre tipos de habilidades\n\n" +
                             "O escribe 'ayuda' para ver todas mis opciones."
            }
    
    def exportar_habilidades(self, tecnicas, blandas):
        """
        Formatea las habilidades seleccionadas para enviar a la API.
        """
        return {
            "habilidades_tecnicas": ", ".join(tecnicas) if tecnicas else "",
            "habilidades_blandas": ", ".join(blandas) if blandas else ""
        }
    
    def validar_habilidades(self, habilidades, tipo):
        """
        Valida que las habilidades sean del tipo correcto.
        """
        todas = self.obtener_todas_habilidades(tipo)
        validas = [h for h in habilidades if h in todas]
        invalidas = [h for h in habilidades if h not in todas]
        
        return validas, invalidas


# Función auxiliar para testing
def probar_asistente():
    """Función para probar el asistente sin interfaz gráfica"""
    print("🧪 Probando AsistenteHabilidades...\n")
    
    # Probar con GPT-2 deshabilitado (lógica original)
    asistente_fijo = AsistenteHabilidades(usar_gpt2=False)
    
    # Probar diferentes preguntas (Lógica fija)
    preguntas_test_fijo = [
        "Muéstrame habilidades técnicas",
        "¿Cuál es la diferencia entre técnicas y blandas?",
        "Habilidades para desarrollo web",
        "Pregunta que no entiende el modelo fijo"
    ]
    
    print("\n--- TEST: Lógica Fija (GPT-2 OFF) ---\n")
    for pregunta in preguntas_test_fijo:
        print(f"❓ Pregunta: {pregunta}")
        respuesta = asistente_fijo.procesar_pregunta(pregunta)
        print(f"💬 Tipo: {respuesta['tipo']}")
        print(f"📝 Mensaje: {respuesta['mensaje'].splitlines()[0]}...")
        if 'habilidades' in respuesta:
             print(f"🎯 Habilidades: {respuesta['habilidades'][:3]}...")
        print("\n" + "="*60 + "\n")
        
    # Probar con GPT-2 habilitado
    # Importante: GPT-2 tardará en cargar si es la primera vez.
    asistente_generativo = AsistenteHabilidades(usar_gpt2=True)
    
    # Probar una pregunta que solo resolverá GPT-2
    pregunta_generativa = "¿Cuáles son las habilidades clave para un especialista en Blockchain?"
    print(f"\n--- TEST: Lógica Generativa (GPT-2 ON) ---\n")
    print(f"❓ Pregunta Generativa: {pregunta_generativa}")
    respuesta_generativa = asistente_generativo.procesar_pregunta(pregunta_generativa)
    print(f"💬 Tipo: {respuesta_generativa['tipo']}")
    print(f"📝 Mensaje: {respuesta_generativa['mensaje'].splitlines()[0]}...")
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    probar_asistente()
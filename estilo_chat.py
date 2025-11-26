"""
chat.py - Interfaz Flet para el Asistente de Habilidades
Este archivo contiene toda la interfaz de usuario usando Flet.
Importa la lógica desde app.py (AsistenteHabilidades debe estar disponible)

Para ejecutar:
    python chat.py
"""

import flet as ft
from flet import Colors, Icons
# Importa la lógica. Asume que 'app.py' existe y tiene la clase AsistenteHabilidades
from app import AsistenteHabilidades 
import json
import sys

# ******************************************************************************
# NOTA: HE CREADO UNA CLASE MOCK (FALSA) PARA AsistenteHabilidades 
# PARA QUE ESTE CÓDIGO SEA EJECUTABLE DE FORMA INDEPENDIENTE. 
# DEBES REEMPLAZAR ESTA CLASE CON TU IMPORTACIÓN REAL DE 'app.py'.
# ******************************************************************************
class AsistenteHabilidades:
    def __init__(self, usar_gpt2=False):
        print(f"Asistente inicializado. Usando GPT-2: {usar_gpt2}")
        pass
    
    def procesar_pregunta(self, pregunta):
        # Lógica de respuesta simulada
        if "web" in pregunta.lower():
            return {
                "mensaje": "Para desarrollo web, te sugiero las siguientes habilidades técnicas y blandas:",
                "habilidades": ["HTML5", "CSS3", "JavaScript", "React", "Python", "Git", "Resolución de problemas", "Colaboración"],
                "tipo": ["tecnicas", "blandas"]
            }
        elif "blandas" in pregunta.lower():
             return {
                "mensaje": "Aquí tienes algunas habilidades blandas clave. ¡Selecciona las que te identifiquen!",
                "habilidades": ["Comunicación", "Liderazgo", "Empatía", "Gestión del tiempo", "Pensamiento crítico"],
                "tipo": ["blandas"]
            }
        else:
            return {"mensaje": f"He recibido tu pregunta: '{pregunta}'. Intenta preguntar por habilidades técnicas o blandas para una carrera específica."}

    def exportar_habilidades(self, tecnicas, blandas):
        return {
            "habilidades_tecnicas": ", ".join(tecnicas),
            "habilidades_blandas": ", ".join(blandas)
        }
# ******************************************************************************


class ChatbotUI:
    """Clase que maneja toda la interfaz de usuario del chatbot"""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.configurar_pagina()
        
        # Inicializar el asistente 
        self.asistente = AsistenteHabilidades(usar_gpt2=False)
        
        # Estado de habilidades seleccionadas
        self.habilidades_seleccionadas = {
            "tecnicas": [],
            "blandas": []
        }
        
        # Diálogo del chatbot (No se inicializa aquí, sino en abrir_chatbot)
        self.dialog_chatbot = None
        
        # Inicializar componentes
        self.inicializar_componentes()
        self.construir_boton_flotante()
        
        # Mostrar el Snackbar inicial (Solicitado en el prompt anterior)
        self.mostrar_snackbar_inicial()
        
    def configurar_pagina(self):
        """Configura las propiedades de la página"""
        self.page.title = "Sistema de Vinculación Empresarial"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.padding = 20
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER
        
    def mostrar_snackbar_inicial(self):
        """Muestra el mensaje inicial 'Si necesitas ayuda...'"""
        self.page.snack_bar = ft.SnackBar(
            content=ft.Row([
                ft.Text("Si necesitas ayuda, ¡me puedes preguntar!", weight=ft.FontWeight.BOLD),
                ft.Icon(Icons.HELP_OUTLINE, color=Colors.WHITE)
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            action="OK",
            duration=5000 # 5 segundos
        )
        self.page.snack_bar.open = True
        self.page.update()

    def inicializar_componentes(self):
        """Inicializa los componentes de la interfaz"""
        # ListView para mensajes del chat
        self.chat_messages = ft.ListView(
            expand=True,
            spacing=10,
            auto_scroll=True,
            padding=10
        )
        
        # Campo de texto para mensajes
        self.mensaje_input = ft.TextField(
            hint_text="Escribe tu pregunta aquí...",
            expand=True,
            on_submit=self.enviar_mensaje,
            border_radius=25,
            filled=True,
            border_color=Colors.BLUE_200,
            focused_border_color=Colors.BLUE_700
        )
        
        # Contador de habilidades
        self.contador_texto = ft.Text(
            "✅ Seleccionadas: 0 técnicas, 0 blandas",
            size=14,
            weight=ft.FontWeight.BOLD,
            color=Colors.BLUE_700
        )
    
    def actualizar_contador(self):
        """Actualiza el contador de habilidades seleccionadas"""
        total_tecnicas = len(self.habilidades_seleccionadas["tecnicas"])
        total_blandas = len(self.habilidades_seleccionadas["blandas"])
        
        self.contador_texto.value = (
            f"✅ Seleccionadas: {total_tecnicas} técnicas, {total_blandas} blandas"
        )
        # Solo actualizar el diálogo si está abierto
        if self.dialog_chatbot and self.dialog_chatbot.open:
            self.dialog_chatbot.update()
        
    def abrir_chatbot(self, e):
        """Abre la ventana emergente del chatbot"""
        # Asegurar que los componentes estén inicializados
        if not hasattr(self, 'chat_messages'):
            self.inicializar_componentes()
        
        self.dialog_chatbot = ft.AlertDialog(
            # width=750, # Flet maneja mejor las dimensiones del AlertDialog sin fijarlas
            # height=700,
            modal=False, # Se cambia a False para que no bloquee el resto de la interfaz (aunque AlertDialog es el formato estándar para modales)
            title=ft.Row([
                ft.Icon(Icons.CHAT_BUBBLE_OUTLINE, color=Colors.BLUE_700, size=30),
                ft.Text("Asistente de Habilidades", size=24, weight=ft.FontWeight.BOLD),
            ], spacing=10),
            content=self.construir_contenido_chat(),
            actions=[
                ft.TextButton("Cerrar", on_click=self.cerrar_chatbot)
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = self.dialog_chatbot
        self.dialog_chatbot.open = True
        self.page.update()
        
        # Mostrar mensaje flash al abrir el chat (segundo requisito del prompt anterior)
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text("🤖 Solo se aceptan preguntas sobre habilidades blandas o técnicas.", color=Colors.WHITE),
            bgcolor=Colors.ORANGE_700,
            duration=3000
        )
        self.page.snack_bar.open = True
        self.page.update()

    
    def cerrar_chatbot(self, e):
        """Cierra la ventana emergente del chatbot"""
        self.dialog_chatbot.open = False
        self.page.update()
    
    def construir_contenido_chat(self):
        """Construye el contenido completo del chat para el diálogo"""
        
        # Botones de acción rápida
        botones_rapidos = ft.Container(
            content=ft.Column([
                ft.Text("🚀 Acciones rápidas:", size=12, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.ElevatedButton(
                        "🔧 Técnicas",
                        on_click=lambda e: self._accion_rapida("Muéstrame habilidades técnicas"),
                        icon=Icons.CODE,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                    ),
                    ft.ElevatedButton(
                        "💡 Blandas",
                        on_click=lambda e: self._accion_rapida("Muéstrame habilidades blandas"),
                        icon=Icons.PEOPLE,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER, wrap=True, spacing=10),
                ft.Row([
                    ft.ElevatedButton(
                        "🌐 Web",
                        on_click=lambda e: self._accion_rapida("Habilidades para desarrollo web"),
                        icon=Icons.WEB,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                    ),
                    ft.ElevatedButton(
                        "📊 Datos",
                        on_click=lambda e: self._accion_rapida("Habilidades para análisis de datos"),
                        icon=Icons.ANALYTICS,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                    ),
                ], alignment=ft.MainAxisAlignment.CENTER, wrap=True, spacing=10),
            ], spacing=10),
            padding=10,
            bgcolor=Colors.GREY_100,
            border_radius=10
        )
        
        # Botones de gestión
        botones_gestion = ft.Row([
            ft.ElevatedButton(
                "💾 Exportar",
                on_click=self.exportar_seleccion,
                bgcolor=Colors.GREEN_700,
                color=Colors.WHITE,
                icon=Icons.DOWNLOAD,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
            ),
            ft.OutlinedButton(
                "🔄 Limpiar",
                on_click=self.limpiar_seleccion,
                icon=Icons.REFRESH,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
            ),
            ft.OutlinedButton(
                "❓ Ayuda",
                on_click=lambda e: self._accion_rapida("ayuda"),
                icon=Icons.HELP_OUTLINE,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
            ),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=10, wrap=True)
        
        # Input de mensaje
        input_row = ft.Row([
            self.mensaje_input,
            ft.IconButton(
                icon=Icons.SEND_ROUNDED,
                on_click=self.enviar_mensaje,
                bgcolor=Colors.BLUE_700,
                icon_color=Colors.WHITE,
                tooltip="Enviar mensaje"
            )
        ], spacing=10)
        
        # Container del contador
        contador_container = ft.Container(
            content=self.contador_texto,
            padding=10,
            bgcolor=Colors.BLUE_50,
            border_radius=5
        )
        
        # Contenido completo del diálogo
        return ft.Container(
            content=ft.Column([
                contador_container,
                ft.Divider(height=1),
                ft.Container(
                    content=self.chat_messages,
                    height=400, # Altura fija para el área de chat
                    width=700, # Ancho fijo (el AlertDialog se adapta)
                ),
                botones_rapidos,
                botones_gestion,
                ft.Divider(height=1),
                input_row
            ], spacing=15),
            # Ajustamos el ancho máximo para que el diálogo sea "rectangular y largo"
            width=750, 
            height=700,
        )
    
    def construir_boton_flotante(self):
        """Construye el botón flotante verde para abrir el chat"""
        # Crear botón flotante con texto e ícono
        boton_flotante = ft.FloatingActionButton(
            icon=Icons.CHAT,
            text="Asistente",
            bgcolor=Colors.GREEN_700,
            tooltip="Abrir Asistente de Habilidades",
            on_click=self.abrir_chatbot,
        )
        
        # Asignar el botón flotante a la página
        self.page.floating_action_button = boton_flotante
        
        # Agregar contenido principal (solo la bienvenida)
        self.page.add(
            ft.Container(
                content=ft.Column([
                    ft.Icon(Icons.SCHOOL, size=100, color=Colors.BLUE_300),
                    ft.Text(
                        "Sistema de Vinculación Empresarial",
                        size=32,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.CENTER,
                        color=Colors.BLUE_900
                    ),
                    ft.Container(height=20),
                    ft.Text(
                        "¿Necesitas ayuda para identificar tus habilidades?",
                        size=18,
                        color=Colors.GREY_700,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Container(height=30),
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(Icons.ARROW_DOWNWARD, color=Colors.GREEN_700, size=30),
                            ft.Text(
                                "Haz clic en el botón verde abajo a la derecha",
                                size=16,
                                color=Colors.GREEN_700,
                                weight=ft.FontWeight.BOLD
                            ),
                            ft.Icon(Icons.ARROW_DOWNWARD, color=Colors.GREEN_700, size=30),
                        ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                        bgcolor=Colors.GREEN_50,
                        padding=15,
                        border_radius=10,
                        border=ft.border.all(2, Colors.GREEN_700)
                    ),
                ], 
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10),
                expand=True,
                alignment=ft.alignment.center
            )
        )
        
        self.page.update()
    
    def agregar_mensaje(self, contenido, es_usuario=True):
        """Agrega un mensaje al chat"""
        # ... (código de agregar_mensaje sin cambios) ...
        if es_usuario:
            mensaje_widget = ft.Container(
                content=ft.Text(
                    contenido, 
                    size=14, 
                    color=Colors.WHITE,
                    selectable=True
                ),
                bgcolor=Colors.BLUE_700,
                border_radius=15,
                padding=ft.padding.all(12),
                margin=ft.margin.only(left=150, right=10, top=5, bottom=5),
                alignment=ft.alignment.center_right
            )
        else:
            mensaje_widget = ft.Container(
                content=ft.Text(
                    contenido, 
                    size=14,
                    selectable=True
                ),
                bgcolor=Colors.GREY_200,
                border_radius=15,
                padding=ft.padding.all(12),
                margin=ft.margin.only(left=10, right=150, top=5, bottom=5),
                alignment=ft.alignment.center_left
            )
        
        # Asegurarse de que el componente de chat esté listo (siempre debe estarlo)
        if hasattr(self, 'chat_messages'):
            self.chat_messages.controls.append(mensaje_widget)
            self.chat_messages.update() # Actualiza solo la lista de mensajes
            # El diálogo también necesita actualizarse si ya está abierto
            if self.dialog_chatbot and self.dialog_chatbot.open:
                self.dialog_chatbot.content.update()
        else:
            # En caso de error de inicialización, usar un print de fallback
            print(f"Error: chat_messages no está inicializado. Mensaje: {contenido}")


    def agregar_chips_habilidades(self, habilidades, tipo):
        """Agrega chips interactivos de habilidades al chat"""
        # ... (código de agregar_chips_habilidades sin cambios) ...
        def crear_chip(habilidad):
            def toggle_habilidad(e):
                lista = self.habilidades_seleccionadas[tipo]
                
                if habilidad in lista:
                    lista.remove(habilidad)
                    e.control.bgcolor = Colors.GREY_300
                    e.control.content.color = Colors.BLACK
                else:
                    lista.append(habilidad)
                    e.control.bgcolor = Colors.GREEN_500
                    e.control.content.color = Colors.WHITE
                
                self.actualizar_contador()
                self.page.update() # Se necesita page.update para el contador global y los chips
            
            return ft.Container(
                content=ft.Text(habilidad, size=12, weight=ft.FontWeight.W_500),
                bgcolor=Colors.GREY_300,
                border_radius=20,
                padding=ft.padding.symmetric(horizontal=12, vertical=8),
                on_click=toggle_habilidad,
                ink=True,
                tooltip=f"Click para seleccionar: {habilidad}"
            )
        
        chips_row = ft.Row(
            controls=[crear_chip(h) for h in habilidades],
            wrap=True,
            spacing=8,
            run_spacing=8
        )
        
        instruccion = ft.Text(
            "👆 Haz clic en las habilidades que te identifiquen",
            size=12,
            color=Colors.GREY_700,
            italic=True
        )
        
        chips_container = ft.Container(
            content=ft.Column([
                instruccion,
                chips_row
            ], spacing=10),
            bgcolor=Colors.WHITE,
            border_radius=10,
            padding=15,
            margin=ft.margin.only(left=10, right=100, top=5, bottom=10),
            border=ft.border.all(1, Colors.GREY_300)
        )
        
        self.chat_messages.controls.append(chips_container)
        self.chat_messages.update() # Actualizar el ListView

    
    def enviar_mensaje(self, e):
        """Maneja el envío de mensajes del usuario"""
        pregunta = self.mensaje_input.value.strip()
        if not pregunta:
            return
        
        # Mostrar mensaje del usuario
        self.agregar_mensaje(pregunta, es_usuario=True)
        self.mensaje_input.value = ""
        self.mensaje_input.focus()
        self.page.update()
        
        # Procesar pregunta con el asistente
        respuesta = self.asistente.procesar_pregunta(pregunta)
        
        # Mostrar respuesta del bot
        self.agregar_mensaje(respuesta["mensaje"], es_usuario=False)
        
        # Si hay habilidades, mostrar chips
        if "habilidades" in respuesta:
            # Detectar el tipo de habilidad, asumiendo que si no es "blandas" explícito, es "tecnicas"
            tipo = "blandas" if "blandas" in str(respuesta.get("tipo", [])).lower() else "tecnicas"
            self.agregar_chips_habilidades(respuesta["habilidades"], tipo)
    
    def exportar_seleccion(self, e):
        """Exporta las habilidades seleccionadas"""
        # ... (código de exportar_seleccion sin cambios) ...
        if not self.habilidades_seleccionadas["tecnicas"] and not self.habilidades_seleccionadas["blandas"]:
            self.agregar_mensaje(
                "⚠️ No has seleccionado ninguna habilidad. Primero selecciona algunas habilidades haciendo clic en ellas.",
                es_usuario=False
            )
            return
        
        resultado = self.asistente.exportar_habilidades(
            self.habilidades_seleccionadas["tecnicas"],
            self.habilidades_seleccionadas["blandas"]
        )
        
        mensaje_confirmacion = "✅ **Habilidades guardadas exitosamente:**\n\n"
        
        if self.habilidades_seleccionadas["tecnicas"]:
            mensaje_confirmacion += f"🔧 **Técnicas** ({len(self.habilidades_seleccionadas['tecnicas'])}):\n"
            mensaje_confirmacion += f"{resultado['habilidades_tecnicas']}\n\n"
        
        if self.habilidades_seleccionadas["blandas"]:
            mensaje_confirmacion += f"💡 **Blandas** ({len(self.habilidades_seleccionadas['blandas'])}):\n"
            mensaje_confirmacion += f"{resultado['habilidades_blandas']}"
        
        self.agregar_mensaje(mensaje_confirmacion, es_usuario=False)
    
    def limpiar_seleccion(self, e):
        """Limpia todas las habilidades seleccionadas y la conversación"""
        # ... (código de limpiar_seleccion sin cambios) ...
        self.habilidades_seleccionadas["tecnicas"].clear()
        self.habilidades_seleccionadas["blandas"].clear()
        self.actualizar_contador()
        
        self.chat_messages.controls.clear()
        
        self.agregar_mensaje(
            "🔄 Todo limpiado. Conversación y selecciones reiniciadas. ¡Empecemos de nuevo!",
            es_usuario=False
        )
    
    def _accion_rapida(self, mensaje):
        """Helper para botones de acción rápida"""
        self.mensaje_input.value = mensaje
        self.enviar_mensaje(None)


def main(page: ft.Page):
    """Función principal que inicia la aplicación Flet"""
    ChatbotUI(page)


if __name__ == "__main__":
    print("🚀 Iniciando Asistente de Habilidades...")
    print("📱 Abriendo interfaz Flet...\n")
    
    # ******************************************************
    # SOLUCIÓN: La función ft.app() debe ser llamada aquí.
    # ******************************************************
    ft.app(target=main)
    
    # Nota: El bloque try/except para KeyboardInterrupt es opcional aquí.
    # El app() de Flet se encarga de la gestión del ciclo de vida.
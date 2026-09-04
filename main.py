import os
import csv
import sqlite3
from datetime import date

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.properties import NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.utils import platform


# ==========================================================
# ANDROID: RUTA PRIVADA DE LA APLICACIÓN
# ==========================================================
# En Android se guarda dentro de la carpeta privada de EduSmart.
# No se borra a menos que el usuario desinstale la aplicación.

if platform == "android":
    from android.storage import app_storage_path


def obtener_carpeta_app():
    """
    Devuelve la carpeta principal de datos de EduSmart.

    Android:
    /data/user/0/org.edusmart.app/files/

    Computador:
    carpeta donde está main.py
    """
    if platform == "android":
        carpeta = app_storage_path()
    else:
        carpeta = os.getcwd()

    os.makedirs(carpeta, exist_ok=True)
    return carpeta


CARPETA_APP = obtener_carpeta_app()
RUTA_BD = os.path.join(CARPETA_APP, "edusmart_offline.db")


# ==========================================================
# COLORES INSTITUCIONALES
# ==========================================================
BEIGE = (0.969, 0.961, 0.933, 1)       # #F7F5EE
MADERA = (0.549, 0.353, 0.196, 1)      # #8C5A32
MARRON = (0.361, 0.227, 0.129, 1)      # #5C3A21
VERDE = (0.18, 0.55, 0.28, 1)
ROJO = (0.75, 0.18, 0.18, 1)
AZUL = (0.18, 0.40, 0.70, 1)
NARANJA = (0.88, 0.52, 0.10, 1)
GRIS = (0.42, 0.42, 0.42, 1)


# ==========================================================
# FUNCIONES VISUALES
# ==========================================================
def crear_boton(texto, color=MADERA, callback=None, ancho=None, alto=45):
    boton = Button(
        text=texto,
        background_normal="",
        background_color=color,
        color=(1, 1, 1, 1),
        font_size=dp(13),
        size_hint_y=None,
        height=dp(alto)
    )

    if ancho is not None:
        boton.size_hint_x = None
        boton.width = dp(ancho)

    if callback:
        boton.bind(on_release=callback)

    return boton


def mostrar_aviso(mensaje):
    caja = BoxLayout(
        orientation="vertical",
        padding=dp(15),
        spacing=dp(10)
    )

    caja.add_widget(Label(
        text=mensaje,
        color=MARRON,
        halign="center",
        valign="middle"
    ))

    popup = Popup(
        title="EduSmart",
        content=caja,
        size_hint=(0.82, 0.27),
        auto_dismiss=True
    )

    popup.open()
    Clock.schedule_once(lambda dt: popup.dismiss(), 2)

    # ==========================================================
    # BASE DE DATOS OFFLINE SQLITE
    # ==========================================================
    class BaseDatos:
        def __init__(self):
            self.conexion = sqlite3.connect(RUTA_BD)
            self.cursor = self.conexion.cursor()
            self.crear_tablas()
            self.crear_datos_demo()

        def crear_tablas(self):
            self.cursor.execute("""
                                CREATE TABLE IF NOT EXISTS cursos
                                (
                                    id
                                    INTEGER
                                    PRIMARY
                                    KEY
                                    AUTOINCREMENT,
                                    nombre
                                    TEXT
                                    NOT
                                    NULL,
                                    materia
                                    TEXT
                                    NOT
                                    NULL,
                                    tutor
                                    INTEGER
                                    DEFAULT
                                    0
                                )
                                """)

            self.cursor.execute("""
                                CREATE TABLE IF NOT EXISTS alumnos
                                (
                                    id
                                    INTEGER
                                    PRIMARY
                                    KEY
                                    AUTOINCREMENT,
                                    curso_id
                                    INTEGER
                                    NOT
                                    NULL,
                                    nombre
                                    TEXT
                                    NOT
                                    NULL
                                )
                                """)

            # UNIQUE hace que cada estudiante tenga solamente
            # un estado de asistencia por día.
            self.cursor.execute("""
                                CREATE TABLE IF NOT EXISTS asistencia
                                (
                                    id
                                    INTEGER
                                    PRIMARY
                                    KEY
                                    AUTOINCREMENT,
                                    alumno_id
                                    INTEGER
                                    NOT
                                    NULL,
                                    fecha
                                    TEXT
                                    NOT
                                    NULL,
                                    estado
                                    TEXT
                                    NOT
                                    NULL,
                                    UNIQUE
                                (
                                    alumno_id,
                                    fecha
                                )
                                    )
                                """)

            self.cursor.execute("""
                                CREATE TABLE IF NOT EXISTS actividades
                                (
                                    id
                                    INTEGER
                                    PRIMARY
                                    KEY
                                    AUTOINCREMENT,
                                    curso_id
                                    INTEGER
                                    NOT
                                    NULL,
                                    nombre
                                    TEXT
                                    NOT
                                    NULL
                                )
                                """)

            self.cursor.execute("""
                                CREATE TABLE IF NOT EXISTS calificaciones
                                (
                                    id
                                    INTEGER
                                    PRIMARY
                                    KEY
                                    AUTOINCREMENT,
                                    alumno_id
                                    INTEGER
                                    NOT
                                    NULL,
                                    actividad_id
                                    INTEGER
                                    NOT
                                    NULL,
                                    nota
                                    REAL
                                    DEFAULT
                                    0,
                                    UNIQUE
                                (
                                    alumno_id,
                                    actividad_id
                                )
                                    )
                                """)

            self.conexion.commit()

        def crear_datos_demo(self):
            self.cursor.execute("SELECT COUNT(*) FROM cursos")
            cantidad = self.cursor.fetchone()[0]

            if cantidad == 0:
                self.cursor.execute("""
                                    INSERT INTO cursos(nombre, materia, tutor)
                                    VALUES (?, ?, ?)
                                    """, ("8vo Año EGB A", "Matemática", 1))

                curso_id = self.cursor.lastrowid

                alumnos = [
                    "Ana García",
                    "Carlos Pérez",
                    "Diana López",
                    "Eduardo Torres",
                    "Fernanda Vera"
                ]

                for alumno in alumnos:
                    self.agregar_alumno(curso_id, alumno)

                for numero in range(1, 5):
                    self.cursor.execute("""
                                        INSERT INTO actividades(curso_id, nombre)
                                        VALUES (?, ?)
                                        """, (curso_id, f"Actividad {numero}"))

                self.conexion.commit()

        # ---------------- CURSOS ----------------

        def obtener_cursos(self):
            self.cursor.execute("SELECT * FROM cursos ORDER BY id DESC")
            return self.cursor.fetchall()

        def crear_curso(self, nombre, materia, tutor):
            self.cursor.execute("""
                                INSERT INTO cursos(nombre, materia, tutor)
                                VALUES (?, ?, ?)
                                """, (nombre, materia, tutor))

            curso_id = self.cursor.lastrowid

            for numero in range(1, 5):
                self.cursor.execute("""
                                    INSERT INTO actividades(curso_id, nombre)
                                    VALUES (?, ?)
                                    """, (curso_id, f"Actividad {numero}"))

            self.conexion.commit()
            return curso_id

        # ---------------- ALUMNOS ----------------

        def obtener_alumnos(self, curso_id):
            self.cursor.execute("""
                                SELECT *
                                FROM alumnos
                                WHERE curso_id = ?
                                ORDER BY nombre
                                """, (curso_id,))
            return self.cursor.fetchall()

        def agregar_alumno(self, curso_id, nombre):
            nombre = nombre.strip()

            if nombre:
                self.cursor.execute("""
                                    INSERT INTO alumnos(curso_id, nombre)
                                    VALUES (?, ?)
                                    """, (curso_id, nombre))
                self.conexion.commit()

        # ---------------- ASISTENCIA ----------------

        def guardar_asistencia(self, alumno_id, fecha, estado):
            self.cursor.execute("""
                                SELECT id
                                FROM asistencia
                                WHERE alumno_id = ?
                                  AND fecha = ?
                                """, (alumno_id, fecha))

            existe = self.cursor.fetchone()

            if existe:
                self.cursor.execute("""
                                    UPDATE asistencia
                                    SET estado = ?
                                    WHERE alumno_id = ?
                                      AND fecha = ?
                                    """, (estado, alumno_id, fecha))
            else:
                self.cursor.execute("""
                                    INSERT INTO asistencia(alumno_id, fecha, estado)
                                    VALUES (?, ?, ?)
                                    """, (alumno_id, fecha, estado))

            self.conexion.commit()

        def obtener_estado_asistencia(self, alumno_id, fecha):
            self.cursor.execute("""
                                SELECT estado
                                FROM asistencia
                                WHERE alumno_id = ?
                                  AND fecha = ?
                                """, (alumno_id, fecha))

            resultado = self.cursor.fetchone()

            if resultado:
                return resultado[0]

            return "Sin registrar"

        def obtener_asistencia_fecha(self, curso_id, fecha):
            self.cursor.execute("""
                                SELECT alumnos.nombre, asistencia.estado
                                FROM alumnos
                                         LEFT JOIN asistencia
                                                   ON alumnos.id = asistencia.alumno_id
                                                       AND asistencia.fecha = ?
                                WHERE alumnos.curso_id = ?
                                ORDER BY alumnos.nombre
                                """, (fecha, curso_id))

            return self.cursor.fetchall()

        # ---------------- ACTIVIDADES ----------------

        def obtener_actividades(self, curso_id):
            self.cursor.execute("""
                                SELECT *
                                FROM actividades
                                WHERE curso_id = ?
                                ORDER BY id
                                """, (curso_id,))
            return self.cursor.fetchall()

        def crear_actividad(self, curso_id, nombre):
            self.cursor.execute("""
                                INSERT INTO actividades(curso_id, nombre)
                                VALUES (?, ?)
                                """, (curso_id, nombre))
            self.conexion.commit()

        def actualizar_actividad(self, actividad_id, nombre):
            self.cursor.execute("""
                                UPDATE actividades
                                SET nombre = ?
                                WHERE id = ?
                                """, (nombre.strip(), actividad_id))
            self.conexion.commit()

        # ---------------- NOTAS ----------------

        def obtener_nota(self, alumno_id, actividad_id):
            self.cursor.execute("""
                                SELECT nota
                                FROM calificaciones
                                WHERE alumno_id = ?
                                  AND actividad_id = ?
                                """, (alumno_id, actividad_id))

            resultado = self.cursor.fetchone()
            return resultado[0] if resultado else 0.0

        def guardar_nota(self, alumno_id, actividad_id, nota):
            self.cursor.execute("""
                                SELECT id
                                FROM calificaciones
                                WHERE alumno_id = ?
                                  AND actividad_id = ?
                                """, (alumno_id, actividad_id))

            existe = self.cursor.fetchone()

            if existe:
                self.cursor.execute("""
                                    UPDATE calificaciones
                                    SET nota = ?
                                    WHERE alumno_id = ?
                                      AND actividad_id = ?
                                    """, (nota, alumno_id, actividad_id))
            else:
                self.cursor.execute("""
                                    INSERT INTO calificaciones(alumno_id, actividad_id, nota)
                                    VALUES (?, ?, ?)
                                    """, (alumno_id, actividad_id, nota))

            self.conexion.commit()

    db = BaseDatos()

    # ==========================================================
    # EXPORTAR ASISTENCIA DIARIA EN ARCHIVO CSV
    # ==========================================================
    def exportar_asistencia_csv(curso_id, fecha_asistencia):
        """
        Ejemplo de resultado:

        carpeta de EduSmart/
        └── asistencias_guardadas/
            └── 2026-09-04/
                └── asistencia_curso_1_2026-09-04.csv
        """

        carpeta_principal = os.path.join(
            CARPETA_APP,
            "asistencias_guardadas"
        )

        carpeta_fecha = os.path.join(
            carpeta_principal,
            fecha_asistencia
        )

        os.makedirs(carpeta_fecha, exist_ok=True)

        nombre_archivo = (
            f"asistencia_curso_{curso_id}_{fecha_asistencia}.csv"
        )

        ruta_archivo = os.path.join(carpeta_fecha, nombre_archivo)

        lista = db.obtener_asistencia_fecha(curso_id, fecha_asistencia)

        with open(
                ruta_archivo,
                mode="w",
                newline="",
                encoding="utf-8-sig"
        ) as archivo:

            escritor = csv.writer(archivo)

            escritor.writerow([
                "EduSmart",
                "Unidad Educativa 17 de Septiembre de San Francisco de Milagro"
            ])

            escritor.writerow(["Fecha", fecha_asistencia])
            escritor.writerow([])
            escritor.writerow(["N°", "Estudiante", "Estado"])

            for numero, datos in enumerate(lista, start=1):
                nombre, estado = datos

                if estado is None:
                    estado = "Sin registrar"

                escritor.writerow([numero, nombre, estado])

        return ruta_archivo

    # ==========================================================
    # SPLASH SCREEN
    # ==========================================================
    class PantallaSplash(Screen):
        def on_enter(self):
            Clock.schedule_once(self.abrir_login, 1.5)

        def abrir_login(self, tiempo):
            self.manager.current = "login"

            # ==========================================================
            # LOGIN
            # ==========================================================
            class PantallaLogin(Screen):
                def ingresar(self, correo, clave):
                    if not correo.text.strip() or not clave.text.strip():
                        mostrar_aviso("Escriba el correo institucional y la contraseña.")
                        return

                    self.manager.current = "principal"

            # ==========================================================
            # PANTALLA PRINCIPAL
            # ==========================================================
            class PantallaPrincipal(Screen):
                curso_seleccionado = NumericProperty(1)

                def on_enter(self):
                    self.ver_cursos()

                def limpiar_panel(self):
                    self.panel.clear_widgets()

                # ------------------------------------------------------
                # CURSOS
                # ------------------------------------------------------
                def ver_cursos(self):
                    self.limpiar_panel()

                    caja = BoxLayout(
                        orientation="vertical",
                        padding=dp(10),
                        spacing=dp(10)
                    )

                    caja.add_widget(crear_boton(
                        "📷 AÑADIR NUEVO CURSO",
                        MADERA,
                        self.ventana_nuevo_curso,
                        alto=52
                    ))

                    scroll = ScrollView()

                    lista = GridLayout(
                        cols=1,
                        spacing=dp(8),
                        size_hint_y=None
                    )
                    lista.bind(minimum_height=lista.setter("height"))

                    cursos = db.obtener_cursos()

                    for curso in cursos:
                        curso_id, nombre, materia, tutor = curso
                        alumnos = db.obtener_alumnos(curso_id)

                        etiqueta_tutor = ""
                        if tutor == 1:
                            etiqueta_tutor = "[color=258c47][TUTOR][/color]"

                        tarjeta = Button(
                            text=(
                                f"[b]{nombre}[/b]\n"
                                f"{materia}\n"
                                f"{len(alumnos)} alumnos digitalizados  "
                                f"{etiqueta_tutor}"
                            ),
                            markup=True,
                            halign="left",
                            valign="middle",
                            background_normal="",
                            background_color=(0.92, 0.86, 0.78, 1),
                            color=MARRON,
                            font_size=dp(15),
                            size_hint_y=None,
                            height=dp(95)
                        )

                        tarjeta.bind(
                            on_release=lambda instancia, x=curso_id:
                            self.seleccionar_curso(x)
                        )

                        lista.add_widget(tarjeta)

                    scroll.add_widget(lista)
                    caja.add_widget(scroll)
                    self.panel.add_widget(caja)

                def seleccionar_curso(self, curso_id):
                    self.curso_seleccionado = curso_id
                    mostrar_aviso("Curso seleccionado.")

                def ventana_nuevo_curso(self, instancia):
                    caja = BoxLayout(
                        orientation="vertical",
                        padding=dp(15),
                        spacing=dp(10)
                    )

                    caja.add_widget(Label(
                        text="[b]Crear nuevo curso[/b]",
                        markup=True,
                        color=MARRON,
                        font_size=dp(18),
                        size_hint_y=None,
                        height=dp(30)
                    ))

                    entrada_curso = TextInput(
                        hint_text="Ejemplo: 9no Año EGB A",
                        multiline=False,
                        size_hint_y=None,
                        height=dp(45)
                    )

                    entrada_materia = TextInput(
                        hint_text="Materia principal",
                        multiline=False,
                        size_hint_y=None,
                        height=dp(45)
                    )

                    boton_tutor = ToggleButton(
                        text="Marcar como curso de tutoría",
                        background_normal="",
                        background_color=MADERA,
                        size_hint_y=None,
                        height=dp(42)
                    )

                    caja.add_widget(entrada_curso)
                    caja.add_widget(entrada_materia)
                    caja.add_widget(boton_tutor)

                    popup = Popup(
                        title="EduSmart",
                        content=caja,
                        size_hint=(0.90, 0.62),
                        auto_dismiss=False
                    )

                    caja.add_widget(crear_boton(
                        "GUARDAR CURSO",
                        VERDE,
                        lambda x: self.guardar_curso(
                            entrada_curso.text,
                            entrada_materia.text,
                            boton_tutor.state,
                            popup
                        )
                    ))

                    caja.add_widget(crear_boton(
                        "CANCELAR",
                        ROJO,
                        lambda x: popup.dismiss()
                    ))

                    popup.open()

                def guardar_curso(self, nombre, materia, tutor, popup):
                    if not nombre.strip() or not materia.strip():
                        mostrar_aviso("Debe escribir el curso y la materia.")
                        return

                    curso_id = db.crear_curso(
                        nombre.strip(),
                        materia.strip(),
                        1 if tutor == "down" else 0
                    )

                    self.curso_seleccionado = curso_id
                    popup.dismiss()
                    self.ver_cursos()
                    mostrar_aviso("Curso creado y guardado offline.")

                    # ------------------------------------------------------
                    # AGREGAR ALUMNOS MANUALMENTE
                    # ------------------------------------------------------
                    def ventana_agregar_alumno(self):
                        caja = BoxLayout(
                            orientation="vertical",
                            padding=dp(15),
                            spacing=dp(10)
                        )

                        caja.add_widget(Label(
                            text="Registrar estudiante",
                            color=MARRON,
                            font_size=dp(18),
                            size_hint_y=None,
                            height=dp(35)
                        ))

                        entrada = TextInput(
                            hint_text="Nombres y apellidos del estudiante",
                            multiline=False,
                            size_hint_y=None,
                            height=dp(45)
                        )

                        caja.add_widget(entrada)

                        popup = Popup(
                            title="EduSmart",
                            content=caja,
                            size_hint=(0.88, 0.42),
                            auto_dismiss=False
                        )

                        caja.add_widget(crear_boton(
                            "AGREGAR",
                            VERDE,
                            lambda x: self.guardar_alumno(entrada.text, popup)
                        ))

                        caja.add_widget(crear_boton(
                            "CANCELAR",
                            ROJO,
                            lambda x: popup.dismiss()
                        ))

                        popup.open()

                    def guardar_alumno(self, nombre, popup):
                        if not nombre.strip():
                            mostrar_aviso("Escriba el nombre del estudiante.")
                            return

                        db.agregar_alumno(self.curso_seleccionado, nombre)
                        popup.dismiss()
                        self.ver_asistencia()
                        mostrar_aviso("Estudiante registrado.")

                    # ------------------------------------------------------
                    # ASISTENCIA POR DÍA
                    # ------------------------------------------------------
                    def ver_asistencia(self):
                        self.limpiar_panel()

                        fecha_hoy = date.today().isoformat()

                        caja = BoxLayout(
                            orientation="vertical",
                            padding=dp(8),
                            spacing=dp(7)
                        )

                        caja.add_widget(Label(
                            text=f"[b]ASISTENCIA: {fecha_hoy}[/b]",
                            markup=True,
                            color=MARRON,
                            font_size=dp(16),
                            size_hint_y=None,
                            height=dp(32)
                        ))

                        caja.add_widget(Label(
                            text=(
                                "La asistencia se guarda automáticamente. "
                                "Al día siguiente se abrirá una nueva hoja."
                            ),
                            color=GRIS,
                            font_size=dp(11),
                            size_hint_y=None,
                            height=dp(25)
                        ))

                        caja.add_widget(crear_boton(
                            "＋ AGREGAR ESTUDIANTE",
                            AZUL,
                            lambda x: self.ventana_agregar_alumno(),
                            alto=42
                        ))

                        # Se crea o actualiza automáticamente el CSV del día.
                        exportar_asistencia_csv(self.curso_seleccionado, fecha_hoy)

                        alumnos = db.obtener_alumnos(self.curso_seleccionado)

                        scroll = ScrollView()

                        lista = GridLayout(
                            cols=1,
                            spacing=dp(7),
                            size_hint_y=None
                        )
                        lista.bind(minimum_height=lista.setter("height"))

                        if not alumnos:
                            lista.add_widget(Label(
                                text="No hay estudiantes registrados en este curso.",
                                color=MARRON,
                                size_hint_y=None,
                                height=dp(45)
                            ))

                        for alumno in alumnos:
                            alumno_id, curso_id, nombre = alumno

                            estado = db.obtener_estado_asistencia(
                                alumno_id,
                                fecha_hoy
                            )

                            fila = BoxLayout(
                                size_hint_y=None,
                                height=dp(64),
                                spacing=dp(3)
                            )

                            fila.add_widget(Label(
                                text=f"{nombre}\nEstado: {estado}",
                                color=MARRON,
                                font_size=dp(12),
                                size_hint_x=0.42
                            ))

                            fila.add_widget(crear_boton(
                                "P",
                                VERDE,
                                lambda x, a=alumno_id:
                                self.marcar_asistencia(a, "P"),
                                ancho=40,
                                alto=56
                            ))

                            fila.add_widget(crear_boton(
                                "A",
                                NARANJA,
                                lambda x, a=alumno_id:
                                self.marcar_asistencia(a, "A"),
                                ancho=40,
                                alto=56
                            ))

                            fila.add_widget(crear_boton(
                                "F",
                                ROJO,
                                lambda x, a=alumno_id:
                                self.marcar_asistencia(a, "F"),
                                ancho=40,
                                alto=56
                            ))

                            fila.add_widget(crear_boton(
                                "FJ",
                                AZUL,
                                lambda x, a=alumno_id:
                                self.marcar_asistencia(a, "FJ"),
                                ancho=45,
                                alto=56
                            ))

                            lista.add_widget(fila)

                        scroll.add_widget(lista)
                        caja.add_widget(scroll)
                        self.panel.add_widget(caja)

                    def marcar_asistencia(self, alumno_id, estado):
                        fecha_hoy = date.today().isoformat()

                        # Guarda la asistencia de ese alumno para la fecha de hoy.
                        db.guardar_asistencia(alumno_id, fecha_hoy, estado)

                        # Actualiza el archivo CSV automáticamente.
                        exportar_asistencia_csv(
                            self.curso_seleccionado,
                            fecha_hoy
                        )

                        mensajes = {
                            "P": "Presente guardado.",
                            "A": "Atraso guardado.",
                            "F": "Falta guardada.",
                            "FJ": "Falta justificada guardada."
                        }

                        self.ver_asistencia()
                        mostrar_aviso(mensajes[estado])

                    # ------------------------------------------------------
                    # NOTAS POR ACTIVIDADES
                    # ------------------------------------------------------
                    def ver_notas(self):
                        self.limpiar_panel()

                        caja = BoxLayout(
                            orientation="vertical",
                            padding=dp(8),
                            spacing=dp(6)
                        )

                        caja.add_widget(Label(
                            text="[b]NOTAS POR ACTIVIDADES[/b]",
                            markup=True,
                            color=MARRON,
                            font_size=dp(16),
                            size_hint_y=None,
                            height=dp(32)
                        ))

                        caja.add_widget(Label(
                            text=(
                                "Puedes cambiar los nombres de actividades. "
                                "Pulsa Enter al terminar de editar."
                            ),
                            color=GRIS,
                            font_size=dp(11),
                            size_hint_y=None,
                            height=dp(25)
                        ))

                        caja.add_widget(crear_boton(
                            "＋ NUEVA ACTIVIDAD",
                            AZUL,
                            lambda x: self.agregar_actividad(),
                            alto=40
                        ))

                        alumnos = db.obtener_alumnos(self.curso_seleccionado)
                        actividades = db.obtener_actividades(self.curso_seleccionado)

                        if not alumnos:
                            caja.add_widget(Label(
                                text="No hay estudiantes registrados.",
                                color=MARRON
                            ))
                            self.panel.add_widget(caja)
                            return

                        scroll = ScrollView(
                            do_scroll_x=True,
                            do_scroll_y=True
                        )

                        tabla = GridLayout(
                            cols=len(actividades) + 2,
                            spacing=dp(3),
                            size_hint=(None, None),
                            width=dp(190 + len(actividades) * 110),
                            height=dp(55 + len(alumnos) * 55)
                        )

                        tabla.add_widget(Label(
                            text="[b]Estudiante[/b]",
                            markup=True,
                            color=MARRON,
                            size_hint_x=None,
                            width=dp(180)
                        ))

                        # Encabezados editables de actividades.
                        for actividad in actividades:
                            actividad_id, curso_id, nombre_actividad = actividad

                            entrada_nombre = TextInput(
                                text=nombre_actividad,
                                multiline=False,
                                font_size=dp(11),
                                size_hint_x=None,
                                width=dp(105)
                            )

                            entrada_nombre.bind(
                                on_text_validate=lambda campo, a=actividad_id:
                                self.cambiar_nombre_actividad(a, campo.text)
                            )

                            tabla.add_widget(entrada_nombre)

                        tabla.add_widget(Label(
                            text="[b]Promedio[/b]",
                            markup=True,
                            color=MARRON,
                            size_hint_x=None,
                            width=dp(85)
                        ))

                        # Fila de cada estudiante.
                        for alumno in alumnos:
                            alumno_id, curso_id, nombre_alumno = alumno

                            tabla.add_widget(Label(
                                text=nombre_alumno,
                                color=MARRON,
                                size_hint_x=None,
                                width=dp(180)
                            ))

                            for actividad in actividades:
                                actividad_id = actividad[0]
                                nota = db.obtener_nota(alumno_id, actividad_id)

                                entrada_nota = TextInput(
                                    text="" if nota == 0 else str(nota),
                                    hint_text="0 - 10",
                                    input_filter="float",
                                    multiline=False,
                                    font_size=dp(13),
                                    size_hint_x=None,
                                    width=dp(105)
                                )

                                entrada_nota.bind(
                                    on_text_validate=lambda campo,
                                                            alumno=alumno_id,
                                                            actividad=actividad_id:
                                    self.guardar_nota(alumno, actividad, campo.text)
                                )

                                tabla.add_widget(entrada_nota)

                            promedio = self.calcular_promedio(
                                alumno_id,
                                actividades
                            )

                            tabla.add_widget(Label(
                                text=f"{promedio:.2f}",
                                color=MARRON,
                                bold=True,
                                size_hint_x=None,
                                width=dp(85)
                            ))

                        scroll.add_widget(tabla)
                        caja.add_widget(scroll)
                        self.panel.add_widget(caja)

                    def agregar_actividad(self):
                        actividades = db.obtener_actividades(self.curso_seleccionado)
                        numero = len(actividades) + 1

                        db.crear_actividad(
                            self.curso_seleccionado,
                            f"Actividad {numero}"
                        )

                        self.ver_notas()
                        mostrar_aviso("Nueva actividad creada.")

                    def cambiar_nombre_actividad(self, actividad_id, nombre):
                        if not nombre.strip():
                            mostrar_aviso("El nombre no puede quedar vacío.")
                            return

                        db.actualizar_actividad(actividad_id, nombre)
                        mostrar_aviso("Actividad actualizada.")

                    def guardar_nota(self, alumno_id, actividad_id, texto):
                        try:
                            nota = float(texto)

                            if nota < 0 or nota > 10:
                                mostrar_aviso("La nota debe estar entre 0 y 10.")
                                return

                            db.guardar_nota(alumno_id, actividad_id, nota)
                            self.ver_notas()

                        except ValueError:
                            mostrar_aviso("Ingrese una nota válida.")

                    def calcular_promedio(self, alumno_id, actividades):
                        if len(actividades) == 0:
                            return 0.0

                        suma = 0

                        for actividad in actividades:
                            actividad_id = actividad[0]
                            suma += db.obtener_nota(alumno_id, actividad_id)

                        return suma / len(actividades)

                # ==========================================================
                # APLICACIÓN EDU SMART
                # ==========================================================
                class EduSmartApp(App):
                    def build(self):
                        self.title = "EduSmart"

                        gestor = ScreenManager()

                        # ---------------- SPLASH ----------------
                        splash = PantallaSplash(name="splash")

                        caja_splash = BoxLayout(
                            orientation="vertical",
                            padding=dp(35),
                            spacing=dp(18)
                        )

                        caja_splash.add_widget(Label(
                            text="🎓",
                            font_size=dp(82),
                            size_hint_y=None,
                            height=dp(105)
                        ))

                        caja_splash.add_widget(Label(
                            text="[b]EduSmart[/b]",
                            markup=True,
                            color=MARRON,
                            font_size=dp(32),
                            size_hint_y=None,
                            height=dp(48)
                        ))

                        caja_splash.add_widget(Label(
                            text=(
                                "Unidad Educativa 17 de Septiembre\n"
                                "San Francisco de Milagro"
                            ),
                            color=MARRON,
                            halign="center",
                            font_size=dp(16)
                        ))

                        caja_splash.add_widget(Label(
                            text="◌ Cargando sistema offline...",
                            color=MADERA,
                            font_size=dp(15),
                            size_hint_y=None,
                            height=dp(40)
                        ))

                        splash.add_widget(caja_splash)

                        # ---------------- LOGIN ----------------
                        login = PantallaLogin(name="login")

                        caja_login = BoxLayout(
                            orientation="vertical",
                            padding=dp(30),
                            spacing=dp(14)
                        )

                        caja_login.add_widget(Label(
                            text="[b]INICIAR SESIÓN[/b]",
                            markup=True,
                            color=MARRON,
                            font_size=dp(24),
                            size_hint_y=None,
                            height=dp(55)
                        ))

                        correo = TextInput(
                            hint_text="Correo institucional",
                            multiline=False,
                            size_hint_y=None,
                            height=dp(48)
                        )

                        clave = TextInput(
                            hint_text="Contraseña",
                            password=True,
                            multiline=False,
                            size_hint_y=None,
                            height=dp(48)
                        )

                        caja_login.add_widget(correo)
                        caja_login.add_widget(clave)

                        caja_login.add_widget(crear_boton(
                            "INGRESAR",
                            MARRON,
                            lambda x: login.ingresar(correo, clave),
                            alto=48
                        ))

                        caja_login.add_widget(Label(
                            text="● Modo fuera de línea activo",
                            color=VERDE,
                            font_size=dp(13),
                            size_hint_y=None,
                            height=dp(35)
                        ))

                        login.add_widget(caja_login)

                        # ---------------- PRINCIPAL ----------------
                        principal = PantallaPrincipal(name="principal")

                        raiz = BoxLayout(orientation="vertical")

                        barra_superior = BoxLayout(
                            size_hint_y=None,
                            height=dp(58),
                            padding=(dp(12), dp(6)),
                            spacing=dp(8)
                        )

                        barra_superior.add_widget(Label(
                            text="[b]EduSmart[/b]",
                            markup=True,
                            color=MARRON,
                            font_size=dp(21)
                        ))

                        barra_superior.add_widget(crear_boton(
                            "📷 Cámara",
                            MADERA,
                            lambda x: mostrar_aviso(
                                "La cámara se puede integrar para capturar listas. "
                                "El OCR Android requiere una librería nativa adicional."
                            ),
                            ancho=110,
                            alto=43
                        ))

                        raiz.add_widget(barra_superior)

                        principal.panel = BoxLayout()
                        raiz.add_widget(principal.panel)

                        navegacion = BoxLayout(
                            size_hint_y=None,
                            height=dp(58),
                            spacing=dp(2)
                        )

                        navegacion.add_widget(crear_boton(
                            "Cursos",
                            MADERA,
                            lambda x: principal.ver_cursos(),
                            alto=55
                        ))

                        navegacion.add_widget(crear_boton(
                            "Asistencia",
                            MADERA,
                            lambda x: principal.ver_asistencia(),
                            alto=55
                        ))

                        navegacion.add_widget(crear_boton(
                            "Notas",
                            MADERA,
                            lambda x: principal.ver_notas(),
                            alto=55
                        ))

                        raiz.add_widget(navegacion)
                        principal.add_widget(raiz)

                        gestor.add_widget(splash)
                        gestor.add_widget(login)
                        gestor.add_widget(principal)

                        return gestor

                if __name__ == "__main__":
                    EduSmartApp().run()

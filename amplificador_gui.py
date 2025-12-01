#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simulador de Amplificador RC - Interfaz Grafica
Proyecto Electricidad II

GUI moderna con tema oscuro usando PySide6.
"""

import sys
import math
import cmath
from dataclasses import dataclass, field
from typing import List, Tuple
from enum import IntEnum

import numpy as np

# Matplotlib backend must be set before importing pyplot
import matplotlib
matplotlib.use('QtAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QGroupBox, QLabel, QDoubleSpinBox, QSpinBox,
    QComboBox, QPushButton, QSplitter, QScrollArea, QFrame,
    QStatusBar, QMenuBar, QMenu, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QPalette, QColor, QFont, QIcon


# =============================================================================
# CONSTANTES DE COLORES (TEMA OSCURO)
# =============================================================================

COLORS = {
    'background': '#1e1e1e',
    'background_alt': '#252526',
    'foreground': '#d4d4d4',
    'accent': '#0078d4',
    'accent_hover': '#1c8adb',
    'border': '#3c3c3c',
    'input_bg': '#2d2d2d',
    'error': '#f44747',
    'success': '#4ec9b0',
    'warning': '#dcdcaa',
    'card_bg': '#2d2d2d',
}


# =============================================================================
# CLASES DE DATOS
# =============================================================================

class ModoCarga(IntEnum):
    """Modos de carga del amplificador."""
    RC_SERIE = 1      # Carga RC normal (R y C en serie)
    SOLO_R = 2        # Solo resistencia (sin capacitor)
    CORTO = 3         # Salida en corto
    ABIERTO = 4       # Salida en abierto


@dataclass
class Armonica:
    """Representa una componente armonica de la senal."""
    frecuencia: float      # Hz
    amplitud_rms: float    # Volts RMS
    fase_rad: float        # Radianes


@dataclass
class ConfigCarga:
    """Configuracion de la carga R-C."""
    resistencia: float     # Ohms
    capacitancia: float    # Faradios
    modo: ModoCarga


@dataclass
class ConfigSenal:
    """Configuracion de la senal de entrada."""
    dc: float                          # Volts DC
    freq_fundamental: float            # Hz
    amp_fundamental_rms: float         # Volts RMS
    fase_fundamental_rad: float        # Radianes
    armonicas: List[Armonica] = field(default_factory=list)


@dataclass
class ComponenteSalida:
    """Componente de frecuencia de la salida."""
    frecuencia: float      # Hz
    voltaje_rms: float     # Volts RMS
    fase_rad: float        # Radianes


@dataclass
class Resultados:
    """Resultados de la simulacion."""
    vrms_total: float
    irms_total: float
    potencia_real: float
    thd: float
    componentes: List[ComponenteSalida] = field(default_factory=list)


# =============================================================================
# FUNCIONES DE CALCULO (Extraidas de amplificador.py)
# =============================================================================

def H_amp(omega: float) -> complex:
    """
    Ganancia compleja del amplificador H(omega) por regiones.
    Devuelve Vsal_amp / V_F (ambos en RMS, fasores).
    """
    j = 1j

    # Caso 1: bajas frecuencias
    if omega < 18:
        num = -13.03 * (j * omega - 0.6143)
        den = omega**2 - 23.55 * j * omega - 79.68
        return num / den

    # Caso 2: frecuencias medias
    elif omega < 2e9:
        num = -43.03 * (omega**2)
        den = omega**2 - 22.94 * j * omega - 73.48
        return num / den

    # Caso 3: altas frecuencias
    else:
        num = omega**2 * (0.4 * omega + 8.61e10 * j)
        den = omega**3 - 2e9 * omega**2 * j - 4.69e10 * omega + 1.41e11 * j
        return num / den


def salida_armonica(
    omega: float,
    amplitud_rms: float,
    fase_rad: float,
    carga: ConfigCarga
) -> Tuple[complex, complex]:
    """
    Calcula el fasor de salida (en la resistencia) para una componente
    de frecuencia omega, dados R, C y el modo de carga.

    Returns:
        Tuple[V_out, I]: Fasor de voltaje y corriente de salida
    """
    j = 1j
    R = carga.resistencia
    C = carga.capacitancia
    modo = carga.modo

    # Fasor de entrada al amplificador (RMS)
    V_F = amplitud_rms * cmath.exp(j * fase_rad)

    # Salida del amplificador (antes de la carga externa)
    H = H_amp(omega)
    V_sal_amp = H * V_F

    # Casos especiales de carga
    if modo == ModoCarga.CORTO:
        return 0j, 0j

    if modo == ModoCarga.ABIERTO:
        return V_sal_amp, 0j

    # Modos normales: RC o solo R
    Z_R = complex(R, 0.0)

    if modo == ModoCarga.SOLO_R or C <= 0:
        Z_tot = Z_R if R > 0 else 1e30
        I = V_sal_amp / Z_tot
        V_out = I * Z_R
        return V_out, I

    # Modo RC en serie
    Z_C = 1.0 / (j * omega * C) if C > 0 else 1e30
    Z_tot = Z_R + Z_C
    if Z_tot == 0:
        return 0j, 0j

    I = V_sal_amp / Z_tot
    V_out = I * Z_R
    return V_out, I


def calcular_respuesta(carga: ConfigCarga, senal: ConfigSenal) -> Resultados:
    """
    Calcula VRMS_total, IRMS_total, potencia real y THD
    a partir de la carga, el amplificador y la senal de entrada.
    """
    componentes_salida: List[ComponenteSalida] = []
    magnitudes_v: List[float] = []
    corrientes: List[complex] = []

    # Fundamental
    omega1 = 2 * math.pi * senal.freq_fundamental
    Vout1, I1 = salida_armonica(
        omega1, senal.amp_fundamental_rms,
        senal.fase_fundamental_rad, carga
    )
    Vout1_rms = abs(Vout1)
    fase1 = cmath.phase(Vout1)

    componentes_salida.append(ComponenteSalida(
        frecuencia=senal.freq_fundamental,
        voltaje_rms=Vout1_rms,
        fase_rad=fase1
    ))
    magnitudes_v.append(Vout1_rms)
    corrientes.append(I1)

    # Armonicas
    for armonica in senal.armonicas:
        omegak = 2 * math.pi * armonica.frecuencia
        Voutk, Ik = salida_armonica(
            omegak, armonica.amplitud_rms,
            armonica.fase_rad, carga
        )
        Voutk_rms = abs(Voutk)
        fasek = cmath.phase(Voutk)

        componentes_salida.append(ComponenteSalida(
            frecuencia=armonica.frecuencia,
            voltaje_rms=Voutk_rms,
            fase_rad=fasek
        ))
        magnitudes_v.append(Voutk_rms)
        corrientes.append(Ik)

    # Casos especiales
    if carga.modo == ModoCarga.CORTO:
        return Resultados(
            vrms_total=0.0,
            irms_total=0.0,
            potencia_real=0.0,
            thd=0.0,
            componentes=componentes_salida
        )

    if carga.modo == ModoCarga.ABIERTO:
        vrms = math.sqrt(sum(v**2 for v in magnitudes_v))
        thd = (math.sqrt(sum(v**2 for v in magnitudes_v[1:])) / magnitudes_v[0]
               if magnitudes_v[0] > 0 else 0.0)
        return Resultados(
            vrms_total=vrms,
            irms_total=0.0,
            potencia_real=0.0,
            thd=thd,
            componentes=componentes_salida
        )

    # Modo normal
    vrms_total = math.sqrt(sum(v**2 for v in magnitudes_v))
    irms_total = math.sqrt(sum(abs(I)**2 for I in corrientes))

    # Potencia real en la resistencia
    potencia_real = 0.0
    for idx, comp in enumerate(componentes_salida):
        V_complex = comp.voltaje_rms * cmath.exp(1j * comp.fase_rad)
        I_complex = corrientes[idx]
        potencia_real += (V_complex * np.conjugate(I_complex)).real

    # THD
    thd = (math.sqrt(sum(v**2 for v in magnitudes_v[1:])) / magnitudes_v[0]
           if magnitudes_v[0] > 0 else 0.0)

    return Resultados(
        vrms_total=vrms_total,
        irms_total=irms_total,
        potencia_real=potencia_real,
        thd=thd,
        componentes=componentes_salida
    )


def generar_senal_tiempo(
    dc: float,
    componentes: List[ComponenteSalida],
    num_periodos: int = 5,
    puntos: int = 5000
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Genera la senal de salida vout(t) a partir de sus componentes
    en frecuencia (fundamental + armonicas).
    """
    if not componentes:
        t = np.linspace(0, 1, puntos)
        return t, np.full_like(t, dc)

    f_fund = componentes[0].frecuencia
    T_fund = 1.0 / f_fund if f_fund > 0 else 1.0

    t = np.linspace(0, num_periodos * T_fund, puntos)
    vout = np.zeros_like(t) + dc

    for comp in componentes:
        V_pico = comp.voltaje_rms * math.sqrt(2.0)
        omega = 2 * math.pi * comp.frecuencia
        vout += V_pico * np.sin(omega * t + comp.fase_rad)

    return t, vout


# =============================================================================
# TEMA OSCURO
# =============================================================================

def create_dark_palette() -> QPalette:
    """Crea una paleta de colores oscura."""
    palette = QPalette()

    # Window colors
    palette.setColor(QPalette.ColorRole.Window, QColor(COLORS['background']))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(COLORS['foreground']))

    # Base colors
    palette.setColor(QPalette.ColorRole.Base, QColor(COLORS['input_bg']))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(COLORS['background_alt']))

    # Text colors
    palette.setColor(QPalette.ColorRole.Text, QColor(COLORS['foreground']))
    palette.setColor(QPalette.ColorRole.BrightText, QColor('#ffffff'))

    # Button colors
    palette.setColor(QPalette.ColorRole.Button, QColor(COLORS['background_alt']))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(COLORS['foreground']))

    # Highlight colors
    palette.setColor(QPalette.ColorRole.Highlight, QColor(COLORS['accent']))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor('#ffffff'))

    # Tooltip
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(COLORS['background_alt']))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(COLORS['foreground']))

    # Disabled state
    palette.setColor(
        QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText,
        QColor('#808080')
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text,
        QColor('#808080')
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText,
        QColor('#808080')
    )

    return palette


DARK_STYLESHEET = """
/* Global */
QWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
}

/* Group boxes */
QGroupBox {
    border: 1px solid #3c3c3c;
    border-radius: 6px;
    margin-top: 14px;
    padding: 12px 8px 8px 8px;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 2px 10px;
    color: #0078d4;
    background-color: #1e1e1e;
}

/* Buttons */
QPushButton {
    background-color: #3c3c3c;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 8px 16px;
    min-width: 80px;
    color: #d4d4d4;
}

QPushButton:hover {
    background-color: #4a4a4a;
    border-color: #666666;
}

QPushButton:pressed {
    background-color: #2d2d2d;
}

QPushButton#primaryButton {
    background-color: #0078d4;
    border-color: #0078d4;
    color: white;
    font-weight: bold;
    font-size: 14px;
    padding: 10px 20px;
}

QPushButton#primaryButton:hover {
    background-color: #1c8adb;
}

QPushButton#primaryButton:pressed {
    background-color: #006cbd;
}

QPushButton#removeButton {
    background-color: transparent;
    border: 1px solid #666666;
    border-radius: 12px;
    color: #888888;
    font-weight: bold;
    font-size: 12px;
    min-width: 24px;
    max-width: 24px;
    min-height: 24px;
    max-height: 24px;
    padding: 0px;
}

QPushButton#removeButton:hover {
    background-color: #f44747;
    border-color: #f44747;
    color: white;
}

QPushButton#addButton {
    background-color: #2d5a2d;
    border: 2px solid #4ec9b0;
    border-radius: 4px;
    color: #4ec9b0;
    font-weight: bold;
    font-size: 13px;
    padding: 6px 12px;
    min-width: 100px;
}

QPushButton#addButton:hover {
    background-color: #4ec9b0;
    color: #1e1e1e;
}

QPushButton#addButton:disabled {
    background-color: #2d2d2d;
    border-color: #555555;
    color: #555555;
}

/* Input fields */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #2d2d2d;
    border: 1px solid #3c3c3c;
    border-radius: 4px;
    padding: 6px 8px;
    color: #d4d4d4;
    selection-background-color: #0078d4;
}

QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border-color: #0078d4;
}

QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {
    background-color: #3c3c3c;
    border: none;
    width: 16px;
}

QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #4a4a4a;
}

/* ComboBox dropdown */
QComboBox::drop-down {
    border: none;
    width: 24px;
    background-color: #3c3c3c;
    border-top-right-radius: 4px;
    border-bottom-right-radius: 4px;
}

QComboBox QAbstractItemView {
    background-color: #2d2d2d;
    border: 1px solid #3c3c3c;
    selection-background-color: #0078d4;
    color: #d4d4d4;
}

/* Scroll area */
QScrollArea {
    border: none;
    background-color: transparent;
}

QScrollArea > QWidget > QWidget {
    background-color: transparent;
}

/* Scroll bars */
QScrollBar:vertical {
    background-color: #1e1e1e;
    width: 10px;
    border-radius: 5px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #555555;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #666666;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

/* Status bar */
QStatusBar {
    background-color: #007acc;
    color: white;
    padding: 4px;
}

/* Splitter */
QSplitter::handle {
    background-color: #3c3c3c;
}

QSplitter::handle:horizontal {
    width: 3px;
}

/* Menu bar */
QMenuBar {
    background-color: #2d2d2d;
    border-bottom: 1px solid #3c3c3c;
    padding: 2px;
}

QMenuBar::item {
    padding: 6px 12px;
    background: transparent;
}

QMenuBar::item:selected {
    background-color: #3c3c3c;
}

QMenu {
    background-color: #2d2d2d;
    border: 1px solid #3c3c3c;
    padding: 4px;
}

QMenu::item {
    padding: 6px 24px;
}

QMenu::item:selected {
    background-color: #0078d4;
}

/* Frame for cards */
QFrame#harmonicCard {
    background-color: #2d2d2d;
    border: 1px solid #3c3c3c;
    border-radius: 6px;
    padding: 8px;
}

/* Labels */
QLabel#resultValue {
    font-size: 16px;
    font-weight: bold;
    color: #4ec9b0;
}

QLabel#resultLabel {
    color: #808080;
}

QLabel#cardTitle {
    font-weight: bold;
    color: #0078d4;
}
"""


def apply_dark_theme(app: QApplication):
    """Aplica el tema oscuro a la aplicacion."""
    app.setStyle('Fusion')
    app.setPalette(create_dark_palette())
    app.setStyleSheet(DARK_STYLESHEET)


# =============================================================================
# WIDGET: PLOT CANVAS (MATPLOTLIB)
# =============================================================================

class PlotCanvas(FigureCanvasQTAgg):
    """Canvas de Matplotlib con tema oscuro."""

    def __init__(self, parent=None):
        self.fig = Figure(figsize=(8, 5), dpi=100)
        self.fig.patch.set_facecolor(COLORS['background'])
        self.ax = self.fig.add_subplot(111)
        super().__init__(self.fig)
        self.setParent(parent)
        self._setup_axes()

    def _setup_axes(self):
        """Configura los ejes con el tema oscuro."""
        self.ax.set_facecolor(COLORS['background'])
        self.ax.tick_params(colors=COLORS['foreground'], labelsize=10)
        self.ax.spines['bottom'].set_color(COLORS['border'])
        self.ax.spines['top'].set_color(COLORS['border'])
        self.ax.spines['left'].set_color(COLORS['border'])
        self.ax.spines['right'].set_color(COLORS['border'])
        self.ax.xaxis.label.set_color(COLORS['foreground'])
        self.ax.yaxis.label.set_color(COLORS['foreground'])
        self.ax.title.set_color(COLORS['foreground'])
        self.ax.grid(True, color=COLORS['border'], linestyle='--', alpha=0.5)

    def plot_signal(self, t: np.ndarray, vout: np.ndarray):
        """Grafica la senal de salida."""
        self.ax.clear()
        self._setup_axes()

        self.ax.plot(t * 1000, vout, color=COLORS['accent'], linewidth=1.5)
        self.ax.set_xlabel("Tiempo [ms]", fontsize=11)
        self.ax.set_ylabel("v_out(t) [V]", fontsize=11)
        self.ax.set_title("Señal de salida en el tiempo", fontsize=12, fontweight='bold')

        self.fig.tight_layout()
        self.draw()

    def clear(self):
        """Limpia la grafica."""
        self.ax.clear()
        self._setup_axes()
        self.ax.set_xlabel("Tiempo [ms]", fontsize=11)
        self.ax.set_ylabel("v_out(t) [V]", fontsize=11)
        self.ax.set_title("Señal de salida en el tiempo", fontsize=12, fontweight='bold')
        self.fig.tight_layout()
        self.draw()


# =============================================================================
# WIDGET: HARMONIC CARD
# =============================================================================

class HarmonicCard(QFrame):
    """Tarjeta expandible para una armonica individual."""

    removed = Signal(object)  # Emite self cuando se elimina

    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self.index = index
        self.setObjectName("harmonicCard")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 10)
        layout.setSpacing(8)

        # Header con titulo y boton eliminar
        header = QHBoxLayout()
        title = QLabel(f"Armonica {self.index + 1}")
        title.setObjectName("cardTitle")
        header.addWidget(title)
        header.addStretch()

        btn_remove = QPushButton("X")
        btn_remove.setObjectName("removeButton")
        btn_remove.setToolTip("Eliminar esta armonica")
        btn_remove.setFixedSize(24, 24)
        btn_remove.clicked.connect(self._on_remove)
        header.addWidget(btn_remove)
        layout.addLayout(header)

        # Formulario
        form = QFormLayout()
        form.setSpacing(6)

        # Frecuencia
        self.spin_freq = QDoubleSpinBox()
        self.spin_freq.setRange(0.001, 1e9)
        self.spin_freq.setSuffix(" Hz")
        self.spin_freq.setDecimals(2)
        self.spin_freq.setValue(1000)
        form.addRow("Frecuencia:", self.spin_freq)

        # Amplitud
        amp_layout = QHBoxLayout()
        amp_layout.setContentsMargins(0, 0, 0, 0)
        amp_layout.setSpacing(6)
        self.spin_amp = QDoubleSpinBox()
        self.spin_amp.setRange(0, 10000)
        self.spin_amp.setSuffix(" V")
        self.spin_amp.setDecimals(4)
        self.spin_amp.setValue(1.0)
        amp_layout.addWidget(self.spin_amp, 1)

        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Pico", "RMS"])
        self.combo_tipo.setFixedWidth(70)
        amp_layout.addWidget(self.combo_tipo, 0)
        form.addRow("Amplitud:", amp_layout)

        # Fase
        self.spin_fase = QDoubleSpinBox()
        self.spin_fase.setRange(-360, 360)
        self.spin_fase.setSuffix(" grados")
        self.spin_fase.setDecimals(2)
        self.spin_fase.setValue(0)
        form.addRow("Fase:", self.spin_fase)

        layout.addLayout(form)

    def _on_remove(self):
        """Emite senal de eliminacion."""
        self.removed.emit(self)

    def get_armonica(self) -> Armonica:
        """Retorna la configuracion de la armonica."""
        amplitud = self.spin_amp.value()
        if self.combo_tipo.currentIndex() == 0:  # Pico
            amplitud_rms = amplitud / math.sqrt(2)
        else:
            amplitud_rms = amplitud

        return Armonica(
            frecuencia=self.spin_freq.value(),
            amplitud_rms=amplitud_rms,
            fase_rad=math.radians(self.spin_fase.value())
        )

    def update_index(self, new_index: int):
        """Actualiza el indice mostrado."""
        self.index = new_index
        title = self.findChild(QLabel, "cardTitle")
        if title:
            title.setText(f"Armonica {new_index + 1}")


# =============================================================================
# WIDGET: LOAD PANEL
# =============================================================================

class LoadPanel(QGroupBox):
    """Panel de configuracion de la carga."""

    def __init__(self, parent=None):
        super().__init__("Configuracion de Carga", parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QFormLayout(self)
        layout.setSpacing(10)

        # Resistencia
        self.spin_r = QDoubleSpinBox()
        self.spin_r.setRange(0, 1e9)
        self.spin_r.setSuffix(" Ohm")
        self.spin_r.setDecimals(2)
        self.spin_r.setValue(1000)
        self.spin_r.setToolTip("Resistencia de carga en ohmios (>= 0)")
        layout.addRow("Resistencia (R):", self.spin_r)

        # Capacitancia
        self.spin_c = QDoubleSpinBox()
        self.spin_c.setRange(0, 1e6)
        self.spin_c.setSuffix(" uF")
        self.spin_c.setDecimals(3)
        self.spin_c.setValue(10)
        self.spin_c.setToolTip("Capacitancia en microfaradios (0 si no hay capacitor)")
        layout.addRow("Capacitancia (C):", self.spin_c)

        # Modo
        self.combo_modo = QComboBox()
        self.combo_modo.addItems([
            "RC en serie",
            "Solo resistencia",
            "Salida en corto",
            "Salida en abierto"
        ])
        self.combo_modo.setToolTip("Modo de conexion de la carga")
        layout.addRow("Modo de carga:", self.combo_modo)

    def get_config(self) -> ConfigCarga:
        """Retorna la configuracion de carga actual."""
        return ConfigCarga(
            resistencia=self.spin_r.value(),
            capacitancia=self.spin_c.value() * 1e-6,  # uF a F
            modo=ModoCarga(self.combo_modo.currentIndex() + 1)
        )

    def reset(self):
        """Reinicia los valores a sus defaults."""
        self.spin_r.setValue(1000)
        self.spin_c.setValue(10)
        self.combo_modo.setCurrentIndex(0)


# =============================================================================
# WIDGET: SIGNAL PANEL
# =============================================================================

class SignalPanel(QGroupBox):
    """Panel de configuracion de la senal de entrada."""

    def __init__(self, parent=None):
        super().__init__("Senal de Entrada", parent)
        self.harmonic_cards: List[HarmonicCard] = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Formulario de senal fundamental
        form = QFormLayout()
        form.setSpacing(8)

        # DC
        self.spin_dc = QDoubleSpinBox()
        self.spin_dc.setRange(-1000, 1000)
        self.spin_dc.setSuffix(" V")
        self.spin_dc.setDecimals(4)
        self.spin_dc.setValue(0)
        self.spin_dc.setToolTip("Componente de voltaje DC")
        form.addRow("Componente DC:", self.spin_dc)

        # Frecuencia fundamental
        self.spin_freq = QDoubleSpinBox()
        self.spin_freq.setRange(0.001, 1e9)
        self.spin_freq.setSuffix(" Hz")
        self.spin_freq.setDecimals(2)
        self.spin_freq.setValue(60)
        self.spin_freq.setToolTip("Frecuencia de la senal fundamental (> 0)")
        form.addRow("Frecuencia (f1):", self.spin_freq)

        # Amplitud fundamental
        amp_layout = QHBoxLayout()
        amp_layout.setContentsMargins(0, 0, 0, 0)
        amp_layout.setSpacing(6)
        self.spin_amp = QDoubleSpinBox()
        self.spin_amp.setRange(0, 10000)
        self.spin_amp.setSuffix(" V")
        self.spin_amp.setDecimals(4)
        self.spin_amp.setValue(10)
        self.spin_amp.setToolTip("Amplitud de la senal fundamental")
        amp_layout.addWidget(self.spin_amp, 1)

        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Pico", "RMS"])
        self.combo_tipo.setFixedWidth(70)
        self.combo_tipo.setToolTip("Tipo de amplitud: Pico o RMS")
        amp_layout.addWidget(self.combo_tipo, 0)
        form.addRow("Amplitud (A1):", amp_layout)

        # Fase fundamental
        self.spin_fase = QDoubleSpinBox()
        self.spin_fase.setRange(-360, 360)
        self.spin_fase.setSuffix(" grados")
        self.spin_fase.setDecimals(2)
        self.spin_fase.setValue(0)
        self.spin_fase.setToolTip("Fase de la senal fundamental")
        form.addRow("Fase (phi1):", self.spin_fase)

        layout.addLayout(form)

        # Seccion de armonicas
        harmonics_header = QHBoxLayout()
        harmonics_label = QLabel("Armonicas:")
        harmonics_label.setStyleSheet("font-weight: bold; color: #0078d4;")
        harmonics_header.addWidget(harmonics_label)

        self.btn_add = QPushButton(" +  Agregar")
        self.btn_add.setObjectName("addButton")
        self.btn_add.setToolTip("Agregar una nueva armonica (max 10)")
        self.btn_add.clicked.connect(self._add_harmonic)
        harmonics_header.addWidget(self.btn_add)
        harmonics_header.addStretch()
        layout.addLayout(harmonics_header)

        # Scroll area para las tarjetas de armonicas
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setMinimumHeight(100)
        # Sin maximo para expandir con el panel

        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(8)
        self.scroll_layout.addStretch()

        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area, stretch=1)  # Expandir para usar espacio disponible

    def _add_harmonic(self):
        """Agrega una nueva tarjeta de armonica."""
        if len(self.harmonic_cards) >= 10:
            QMessageBox.warning(
                self, "Limite alcanzado",
                "El numero maximo de armonicas es 10."
            )
            return

        card = HarmonicCard(len(self.harmonic_cards))
        card.removed.connect(self._remove_harmonic)
        self.harmonic_cards.append(card)

        # Insertar antes del stretch
        self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, card)

        self._update_add_button()

    def _remove_harmonic(self, card: HarmonicCard):
        """Elimina una tarjeta de armonica."""
        if card in self.harmonic_cards:
            self.harmonic_cards.remove(card)
            self.scroll_layout.removeWidget(card)
            card.deleteLater()

            # Actualizar indices
            for i, c in enumerate(self.harmonic_cards):
                c.update_index(i)

            self._update_add_button()

    def _update_add_button(self):
        """Actualiza el estado del boton agregar."""
        self.btn_add.setEnabled(len(self.harmonic_cards) < 10)
        count = len(self.harmonic_cards)
        self.btn_add.setText(f" +  Agregar ({count}/10)")

    def get_config(self) -> ConfigSenal:
        """Retorna la configuracion de senal actual."""
        amplitud = self.spin_amp.value()
        if self.combo_tipo.currentIndex() == 0:  # Pico
            amplitud_rms = amplitud / math.sqrt(2)
        else:
            amplitud_rms = amplitud

        armonicas = [card.get_armonica() for card in self.harmonic_cards]

        return ConfigSenal(
            dc=self.spin_dc.value(),
            freq_fundamental=self.spin_freq.value(),
            amp_fundamental_rms=amplitud_rms,
            fase_fundamental_rad=math.radians(self.spin_fase.value()),
            armonicas=armonicas
        )

    def reset(self):
        """Reinicia los valores a sus defaults."""
        self.spin_dc.setValue(0)
        self.spin_freq.setValue(60)
        self.spin_amp.setValue(10)
        self.combo_tipo.setCurrentIndex(0)
        self.spin_fase.setValue(0)

        # Eliminar todas las tarjetas de armonicas
        for card in self.harmonic_cards[:]:
            self._remove_harmonic(card)


# =============================================================================
# WIDGET: RESULTS PANEL
# =============================================================================

class ResultsPanel(QGroupBox):
    """Panel de visualizacion de resultados."""

    def __init__(self, parent=None):
        super().__init__("Resultados", parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Crear filas de resultados
        self.results = {}
        result_items = [
            ("vrms", "VRMS de salida:", "V"),
            ("irms", "IRMS de salida:", "A"),
            ("power", "Potencia real:", "W"),
            ("thd", "THD:", "%"),
        ]

        for key, label_text, unit in result_items:
            row = QHBoxLayout()

            label = QLabel(label_text)
            label.setObjectName("resultLabel")
            label.setMinimumWidth(120)
            row.addWidget(label)

            value = QLabel("---")
            value.setObjectName("resultValue")
            value.setAlignment(Qt.AlignmentFlag.AlignRight)
            self.results[key] = value
            row.addWidget(value)

            unit_label = QLabel(unit)
            unit_label.setObjectName("resultLabel")
            unit_label.setFixedWidth(30)
            row.addWidget(unit_label)

            layout.addLayout(row)

        layout.addStretch()

    def display_results(self, resultados: Resultados):
        """Muestra los resultados de la simulacion."""
        self.results["vrms"].setText(f"{resultados.vrms_total:.4f}")
        self.results["irms"].setText(f"{resultados.irms_total:.6f}")
        self.results["power"].setText(f"{resultados.potencia_real:.4f}")
        self.results["thd"].setText(f"{resultados.thd * 100:.2f}")

    def clear(self):
        """Limpia los resultados."""
        for value in self.results.values():
            value.setText("---")


# =============================================================================
# VENTANA PRINCIPAL
# =============================================================================

class MainWindow(QMainWindow):
    """Ventana principal del simulador."""

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._setup_menu()
        self._connect_signals()

    def _setup_ui(self):
        """Configura la interfaz de usuario."""
        self.setWindowTitle("Simulador de Amplificador RC - Electricidad II")
        self.setMinimumSize(1100, 700)
        self.resize(1200, 800)

        # Widget central
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Splitter para paneles redimensionables
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Panel izquierdo - Configuracion
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(10)

        self.load_panel = LoadPanel()
        self.signal_panel = SignalPanel()

        self.btn_simular = QPushButton("SIMULAR")
        self.btn_simular.setObjectName("primaryButton")
        self.btn_simular.setMinimumHeight(45)

        left_layout.addWidget(self.load_panel)
        left_layout.addWidget(self.signal_panel, stretch=1)  # Expandir para usar espacio
        left_layout.addWidget(self.btn_simular)  # Boton al fondo

        # Panel derecho - Resultados y grafica
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(10)

        self.results_panel = ResultsPanel()
        self.results_panel.setMaximumHeight(180)

        self.plot_canvas = PlotCanvas()
        self.plot_canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        self.plot_canvas.clear()

        right_layout.addWidget(self.results_panel)
        right_layout.addWidget(self.plot_canvas, stretch=1)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([350, 850])

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Listo para simular")

    def _setup_menu(self):
        """Configura el menu de la aplicacion."""
        menubar = self.menuBar()

        # Menu Archivo
        archivo_menu = menubar.addMenu("&Archivo")

        action_nuevo = QAction("&Nueva simulacion", self)
        action_nuevo.setShortcut("Ctrl+N")
        action_nuevo.triggered.connect(self._reset)
        archivo_menu.addAction(action_nuevo)

        archivo_menu.addSeparator()

        action_salir = QAction("&Salir", self)
        action_salir.setShortcut("Ctrl+Q")
        action_salir.triggered.connect(self.close)
        archivo_menu.addAction(action_salir)

        # Menu Ayuda
        ayuda_menu = menubar.addMenu("A&yuda")

        action_acerca = QAction("&Acerca de", self)
        action_acerca.triggered.connect(self._show_about)
        ayuda_menu.addAction(action_acerca)

    def _connect_signals(self):
        """Conecta las senales y slots."""
        self.btn_simular.clicked.connect(self._run_simulation)

    def _run_simulation(self):
        """Ejecuta la simulacion con los parametros actuales."""
        try:
            # Obtener configuraciones
            carga = self.load_panel.get_config()
            senal = self.signal_panel.get_config()

            # Validar entradas
            if not self._validate_inputs(senal):
                return

            self.status_bar.showMessage("Simulando...")
            QApplication.processEvents()

            # Ejecutar calculo
            resultados = calcular_respuesta(carga, senal)

            # Generar senal en el tiempo
            t, vout = generar_senal_tiempo(senal.dc, resultados.componentes)

            # Actualizar grafica
            self.plot_canvas.plot_signal(t, vout)

            # Mostrar resultados
            self.results_panel.display_results(resultados)

            self.status_bar.showMessage("Simulacion completada")

        except Exception as e:
            self.status_bar.showMessage(f"Error: {str(e)}")
            QMessageBox.critical(
                self, "Error de simulacion",
                f"Ocurrio un error durante la simulacion:\n{str(e)}"
            )

    def _validate_inputs(self, senal: ConfigSenal) -> bool:
        """Valida los datos de entrada."""
        if senal.freq_fundamental <= 0:
            QMessageBox.warning(
                self, "Error de validacion",
                "La frecuencia fundamental debe ser mayor que cero."
            )
            return False

        for i, arm in enumerate(senal.armonicas):
            if arm.frecuencia <= 0:
                QMessageBox.warning(
                    self, "Error de validacion",
                    f"La frecuencia de la armonica {i+1} debe ser mayor que cero."
                )
                return False

        return True

    def _reset(self):
        """Reinicia la simulacion."""
        self.load_panel.reset()
        self.signal_panel.reset()
        self.results_panel.clear()
        self.plot_canvas.clear()
        self.status_bar.showMessage("Listo para simular")

    def _show_about(self):
        """Muestra el dialogo Acerca de."""
        QMessageBox.about(
            self,
            "Acerca del Simulador",
            "<h3>Simulador de Amplificador RC</h3>"
            "<p>Proyecto Electricidad II</p>"
            "<p>Instituto Tecnologico de Costa Rica</p>"
            "<hr>"
            "<p>Interfaz grafica desarrollada con PySide6</p>"
            "<p>Tema oscuro moderno</p>"
        )


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================

def main():
    """Funcion principal."""
    import os

    app = QApplication(sys.argv)

    # Metadata de la aplicacion
    app.setApplicationName("Simulador Amplificador RC")
    app.setOrganizationName("ITCR")
    app.setApplicationVersion("1.0.0")

    # Cargar icono de la aplicacion
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
    if os.path.exists(icon_path):
        app_icon = QIcon(icon_path)
        app.setWindowIcon(app_icon)

    # Aplicar tema oscuro
    apply_dark_theme(app)

    # Crear y mostrar ventana principal
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

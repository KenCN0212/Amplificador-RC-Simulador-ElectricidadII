🔧 Simulador de Amplificador con Carga R–C

Proyecto – Electricidad II
Instituto Tecnológico de Costa Rica

📘 Descripción del proyecto

Este repositorio contiene un simulador completo de un amplificador con carga R–C, desarrollado para el curso Electricidad II.
El sistema implementa un modelo por regiones de frecuencia, reconstrucción de señales periódicas y una interfaz gráfica moderna en PySide6.

El programa permite:

✔ Modelado del amplificador

Función de transferencia H(ω) definida por regiones de operación.

Implementación matemática basada en análisis nodal simplificado.

Validación conceptual frente a simulación LTSpice.

✔ Configuración de la señal de entrada

Componente DC, frecuencia fundamental y hasta 10 armónicas configurables.

Reconstrucción de la señal en el dominio del tiempo.

Cálculo automático de magnitudes eléctricas.

✔ Modos de carga seleccionables

RC en serie

Solo resistencia

Salida en corto

Salida en abierto

✔ Cálculos eléctricos automáticos

VRMS total

IRMS total

Potencia real entregada a la carga

THD (Total Harmonic Distortion)

Señal de salida reconstruida

✔ Interfaz gráfica (GUI)

Desarrollada con PySide6, incluye:

Tema oscuro y diseño moderno

Panel de configuración de la señal

Panel de selección de carga

Tarjetas desplegables para armónicas

Gráfico interactivo en tiempo con Matplotlib

Organización clara para uso académico

🎯 Objetivo del proyecto

Simular de forma precisa la respuesta de un amplificador sometido a una señal periódica arbitraria, permitiendo estudiar efectos como:

Atenuación y fase según frecuencia

Distorsión introducida por la carga

Variaciones de potencia y corriente

Comparación entre diferentes modos de carga

Todo esto usando un modelo matemático que puede ser portado fácilmente a otros lenguajes (C, MATLAB, Verilog-A, etc.).

🧰 Requisitos del sistema

Python 3.8+

Numpy

Matplotlib

PySide6 (para la GUI)

📦 Instalación

Instalar dependencias:

pip install numpy matplotlib PySide6


Ejecutar el simulador:

python main.py

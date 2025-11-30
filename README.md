# Simulador de Amplificador con Carga R–C  
Proyecto – Electricidad II  
Instituto Tecnológico de Costa Rica  

---

## 📘 Descripción del proyecto

Este repositorio contiene el simulador completo del amplificador analizado en el curso **Electricidad II**, basado en un modelo por regiones de frecuencia.  

El programa:

- Modela el amplificador mediante tres funciones de transferencia según la frecuencia.  
- Recibe una señal de entrada formada por componente DC, fundamental y hasta 10 armónicas.  
- Calcula VRMS, IRMS, potencia real y THD.  
- Reconstruye la señal temporal de salida.  
- Permite seleccionar distintos modos de carga:  
  - RC en serie  
  - Solo R  
  - Salida en corto  
  - Salida en abierto  

El código está diseñado para ser fácilmente adaptable a cualquier otro lenguaje de programación.

---

## 🎯 Objetivo

Simular la respuesta del amplificador para cualquier señal periódica, validando su comportamiento mediante las funciones de transferencia obtenidas por análisis nodal simplificado y comparadas con LTSpice.

---

## 🧰 Requisitos

- Python 3.8+
- Numpy
- Matplotlib

Instalación:

```bash
pip install numpy matplotlib

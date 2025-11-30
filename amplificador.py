import math
import cmath
import numpy as np
import matplotlib.pyplot as plt

# ------------------------------
# Funciones auxiliares de entrada
# ------------------------------

def leer_float(mensaje):
    while True:
        try:
            valor = float(input(mensaje))
            return valor
        except ValueError:
            print("Entrada inválida. Por favor ingrese un número.")


def leer_int(mensaje):
    while True:
        try:
            valor = int(input(mensaje))
            return valor
        except ValueError:
            print("Entrada inválida. Por favor ingrese un número entero.")


def leer_int_rango(mensaje, minimo, maximo):
    while True:
        valor = leer_int(mensaje)
        if minimo <= valor <= maximo:
            return valor
        else:
            print(f"Por favor ingrese un valor entre {minimo} y {maximo}.")


# ---------------------------------
# Lectura y validación de la carga
# ---------------------------------

def pedir_carga():
    """
    Pide al usuario la carga R-C y el modo:
    1 = normal (R + C en serie)
    2 = solo R (sin capacitor)
    3 = salida en corto
    4 = salida en abierto
    Devuelve (R, C, modo_carga)
    """
    while True:
        print("\n--- Datos de la carga ---")

        # Primero el capacitor (como indica el enunciado)
        C_micro = leer_float("Ingrese la capacitancia C en microfaradios (0 si no hay capacitor): ")
        C = C_micro * 1e-6  # conversión a faradios

        R = leer_float("Ingrese la resistencia R en ohmios (≥0): ")

        print("\nSeleccione el modo de la salida:")
        print("1) Carga RC normal (R y C en serie)")
        print("2) Solo resistencia (sin capacitor)")
        print("3) Salida en corto")
        print("4) Salida en abierto")
        modo = leer_int_rango("Opción: ", 1, 4)

        # Validaciones simples
        if R < 0:
            print("Error: R no puede ser negativa.")
            continue
        if C < 0:
            print("Error: C no puede ser negativa.")
            continue

        # Ajustes según modo
        if modo == 2:  # solo R
            C = 0.0
        elif modo in (3, 4):
            # en corto o abierto, el valor de R y C no influye en el resultado de salida
            pass

        return R, C, modo


# ---------------------------------
# Lectura y validación de la señal
# ---------------------------------

def pedir_senal():
    """
    Pide al usuario los datos de la señal:
    DC, fundamental, hasta 10 armónicas.
    Devuelve:
      DC (float),
      f1 (float),
      A1_rms (float),
      phi1_rad (float),
      lista_harmonicas (lista de dicts: {'f', 'A_rms', 'fase_rad'})
    """
    while True:
        print("\n--- Datos de la señal de entrada ---")

        DC = leer_float("Ingrese el valor DC (puede ser 0): ")

        f1 = leer_float("Ingrese la frecuencia de la fundamental en Hz (>0): ")
        if f1 <= 0:
            print("La frecuencia fundamental debe ser mayor que cero.")
            continue

        A1 = leer_float("Ingrese la amplitud de la fundamental: ")
        if A1 < 0:
            print("La amplitud no puede ser negativa.")
            continue

        print("¿La amplitud de la fundamental es pico o RMS?")
        print("1) Pico")
        print("2) RMS")
        tipo_amp = leer_int_rango("Opción: ", 1, 2)

        if tipo_amp == 1:
            A1_rms = A1 / math.sqrt(2.0)
        else:
            A1_rms = A1

        phi1_deg = leer_float("Ingrese la fase de la fundamental en grados (0 si no sabe): ")
        phi1_rad = math.radians(phi1_deg)

        N = leer_int_rango("Número de armónicas (0 a 10): ", 0, 10)

        armonicas = []
        for idx in range(1, N + 1):
            print(f"\nArmónica {idx}:")
            fk = leer_float("  Frecuencia (Hz): ")
            if fk <= 0:
                print("  La frecuencia debe ser mayor que cero. Se cancela la lectura de la señal.")
                break

            Ak = leer_float("  Amplitud: ")
            if Ak < 0:
                print("  La amplitud no puede ser negativa. Se cancela la lectura de la señal.")
                break

            print("  ¿La amplitud es pico o RMS?")
            print("  1) Pico")
            print("  2) RMS")
            tipo_ampk = leer_int_rango("  Opción: ", 1, 2)

            if tipo_ampk == 1:
                Ak_rms = Ak / math.sqrt(2.0)
            else:
                Ak_rms = Ak

            phik_deg = leer_float("  Fase en grados (0 si no sabe): ")
            phik_rad = math.radians(phik_deg)

            armonicas.append({
                "f": fk,
                "A_rms": Ak_rms,
                "fase_rad": phik_rad
            })
        else:
            # lectura correcta
            return DC, f1, A1_rms, phi1_rad, armonicas

        print("Hubo un error en los datos de las armónicas. Repita la entrada de la señal.")


# ---------------------------------------
# Modelo del amplificador H(ω)
# ---------------------------------------

def H_amp(omega):
    """
    Ganancia compleja del amplificador H(ω) por regiones.
    Devuelve Vsal_amp / V_F (ambos en RMS, fasores).
    """
    j = 1j

    # --------------------
    # Caso 1: bajas frecuencias
    # --------------------
    if omega < 18:
        num = -13.03 * (j * omega - 0.6143)
        den = omega**2 - 23.55 * j * omega - 79.68
        return num / den

    # --------------------
    # Caso 2: frecuencias medias 
    # --------------------
    elif omega < 2e9:
        num = -43.03 * (omega**2)
        den = omega**2 - 22.94 * j * omega - 73.48   # ← AQUÍ SE AGREGA j
        return num / den

    # --------------------
    # Caso 3: altas frecuencias
    # --------------------
    else:
        num = omega**2 * (0.4 * omega + 8.61e10 * j)
        den = omega**3 - 2e9 * omega**2 * j - 4.69e10 * omega + 1.41e11 * j
        return num / den

def salida_armonica(omega, A_rms, fase_rad, R, C, modo_carga):
    """
    Calcula el fasor de salida (en la resistencia) para una componente
    de frecuencia omega, dados R, C y el modo de carga.
    """
    j = 1j

    # Fasor de entrada al amplificador (RMS)
    V_F = A_rms * cmath.exp(j * fase_rad)

    # Salida del amplificador (antes de la carga externa)
    H = H_amp(omega)
    V_sal_amp = H * V_F

    # Casos especiales de carga
    if modo_carga == 3:  # corto
        V_out = 0j
        I = 0j
        return V_out, I

    if modo_carga == 4:  # abierto
        # No hay carga, asumimos Vout = salida del amplificador
        V_out = V_sal_amp
        I = 0j
        return V_out, I

    # Modos normales: 1 = RC, 2 = solo R
    Z_R = complex(R, 0.0)

    if modo_carga == 2 or C <= 0:
        # Solo R
        Z_tot = Z_R if R > 0 else 1e30  # evitar división por cero
        I = V_sal_amp / Z_tot
        V_out = I * Z_R
        return V_out, I

    # Modo 1: RC en serie
    Z_C = 1.0 / (j * omega * C) if C > 0 else 1e30
    Z_tot = Z_R + Z_C
    if Z_tot == 0:
        I = 0j
        V_out = 0j
    else:
        I = V_sal_amp / Z_tot
        V_out = I * Z_R  # medimos en la resistencia

    return V_out, I


# ---------------------------------------
# Cálculo de respuesta completa
# ---------------------------------------

def calcular_respuesta(R, C, modo_carga, f1, A1_rms, phi1_rad, armonicas):
    """
    Calcula VRMS_total, IRMS_total, potencia real y THD
    a partir de la carga, el amplificador y la señal de entrada.
    También devuelve lista con info de cada componente de salida
    para reconstruir la señal en el tiempo.
    """
    componentes_salida = []  # {'f', 'Vout_rms', 'fase_rad'}
    magnitudes_v = []
    corrientes = []

    # Fundamental
    omega1 = 2 * math.pi * f1
    Vout1, I1 = salida_armonica(omega1, A1_rms, phi1_rad, R, C, modo_carga)
    Vout1_rms = abs(Vout1)
    fase1 = cmath.phase(Vout1)

    componentes_salida.append({
        "f": f1,
        "Vout_rms": Vout1_rms,
        "fase_rad": fase1
    })
    magnitudes_v.append(Vout1_rms)
    corrientes.append(I1)

    # Armónicas
    for armonica in armonicas:
        fk = armonica["f"]
        Ak_rms = armonica["A_rms"]
        phik = armonica["fase_rad"]

        omegak = 2 * math.pi * fk
        Voutk, Ik = salida_armonica(omegak, Ak_rms, phik, R, C, modo_carga)
        Voutk_rms = abs(Voutk)
        fasek = cmath.phase(Voutk)

        componentes_salida.append({
            "f": fk,
            "Vout_rms": Voutk_rms,
            "fase_rad": fasek
        })
        magnitudes_v.append(Voutk_rms)
        corrientes.append(Ik)

    # Casos especiales de corto y abierto
    if modo_carga == 3:  # corto
        VRMS_total = 0.0
        IRMS_total = 0.0
        potencia_real = 0.0
        THD = 0.0
        # en componentes_salida ya tenemos todas en cero por salida_armonica
        return VRMS_total, IRMS_total, potencia_real, THD, componentes_salida

    if modo_carga == 4:  # abierto
        # Vout es la salida del amplificador, pero I = 0 y P = 0
        VRMS_total = math.sqrt(sum(v**2 for v in magnitudes_v))
        IRMS_total = 0.0
        potencia_real = 0.0
        if magnitudes_v[0] > 0:
            THD = math.sqrt(sum(v**2 for v in magnitudes_v[1:])) / magnitudes_v[0]
        else:
            THD = 0.0
        return VRMS_total, IRMS_total, potencia_real, THD, componentes_salida

    # Modo normal / solo R
    # VRMS total (todas las componentes, RMS cuadrático)
    VRMS_total = math.sqrt(sum(v**2 for v in magnitudes_v))

    # Corriente RMS total
    IRMS_total = math.sqrt(sum(abs(I)**2 for I in corrientes))

    # Potencia real en la resistencia (suma Re{V * I*})
    potencia_real = 0.0
    for idx, comp in enumerate(componentes_salida):
        V_rms = comp["Vout_rms"]
        fase = comp["fase_rad"]
        V_complex = V_rms * cmath.exp(1j * fase)
        I_complex = corrientes[idx]
        potencia_real += (V_complex * np.conjugate(I_complex)).real

    # THD basado en magnitud de salida
    if magnitudes_v[0] > 0:
        THD = math.sqrt(sum(v**2 for v in magnitudes_v[1:])) / magnitudes_v[0]
    else:
        THD = 0.0

    return VRMS_total, IRMS_total, potencia_real, THD, componentes_salida


# ---------------------------------------
# Reconstrucción de la señal en el tiempo
# ---------------------------------------

def generar_senal_tiempo(DC, componentes_salida, num_periodos=5, puntos=5000):
    """
    Genera la señal de salida vout(t) a partir de sus componentes
    en frecuencia (fundamental + armónicas).
    """
    f_fund = componentes_salida[0]["f"]
    T_fund = 1.0 / f_fund if f_fund > 0 else 1.0

    t = np.linspace(0, num_periodos * T_fund, puntos)
    vout = np.zeros_like(t) + DC  # DC se suma directamente

    for comp in componentes_salida:
        f = comp["f"]
        V_rms = comp["Vout_rms"]
        fase = comp["fase_rad"]
        V_pico = V_rms * math.sqrt(2.0)
        omega = 2 * math.pi * f
        vout += V_pico * np.sin(omega * t + fase)

    return t, vout


# ----------------------
# Programa principal
# ----------------------

def main():
    print("Simulador de amplificador con carga R-C (proyecto Electricidad II)\n")

    # Carga inicial y señal inicial
    R, C, modo_carga = pedir_carga()
    DC, f1, A1_rms, phi1_rad, armonicas = pedir_senal()

    continuar = True

    while continuar:
        # Calcular respuesta
        VRMS_total, IRMS_total, P_real, THD, comps_salida = calcular_respuesta(
            R, C, modo_carga, f1, A1_rms, phi1_rad, armonicas
        )

        # Generar señal en el tiempo
        t, vout_t = generar_senal_tiempo(DC, comps_salida)

        # Mostrar resultados numéricos
        print("\n--- Resultados ---")
        print(f"VRMS de salida: {VRMS_total:.4f} V")
        print(f"IRMS de salida: {IRMS_total:.4f} A")
        print(f"Potencia real (en la resistencia): {P_real:.4f} W")
        print(f"THD (distorsión armónica total): {THD * 100:.2f} %")

        # Graficar
        plt.figure()
        plt.plot(t, vout_t)
        plt.xlabel("Tiempo [s]")
        plt.ylabel("v_out(t) [V]")
        plt.title("Señal de salida en el tiempo")
        plt.grid(True)
        plt.show()

        # Menú de continuación
        print("\n¿Qué desea hacer ahora?")
        print("1) Cambiar solo la carga (R, C, modo)")
        print("2) Cambiar solo la señal de entrada")
        print("3) Cambiar carga y señal")
        print("4) Salir")

        opcion = leer_int_rango("Opción: ", 1, 4)

        if opcion == 1:
            R, C, modo_carga = pedir_carga()
        elif opcion == 2:
            DC, f1, A1_rms, phi1_rad, armonicas = pedir_senal()
        elif opcion == 3:
            R, C, modo_carga = pedir_carga()
            DC, f1, A1_rms, phi1_rad, armonicas = pedir_senal()
        elif opcion == 4:
            continuar = False

    print("\nFin del programa.")


if __name__ == "__main__":
    main()

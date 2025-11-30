=========================================================
1. Funciones de entrada
=========================================================

LeerFloat(mensaje)
    Repetir:
        Mostrar mensaje
        Leer x
    Hasta que x sea un número válido
    Retornar x

LeerInt(mensaje)
    Repetir:
        Mostrar mensaje
        Leer n
    Hasta que n sea un entero válido
    Retornar n

LeerIntRango(mensaje, min, max)
    Repetir:
        n ← LeerInt(mensaje)
    Hasta que min ≤ n ≤ max
    Retornar n


=========================================================
2. Lectura de la carga
=========================================================

PedirCarga()
    Repetir:
        C_micro ← LeerFloat("Capacitancia en microfaradios")
        C ← C_micro × 10⁻⁶
        R ← LeerFloat("Resistencia en ohmios")

        Mostrar:
            1) RC en serie
            2) Solo R
            3) Corto
            4) Abierto

        modo ← LeerIntRango(1, 4)

    Hasta que los datos sean válidos

    Si modo = 2:
        C ← 0   // sin capacitor

    Retornar (R, C, modo)


=========================================================
3. Lectura de la señal
=========================================================

PedirSeñal()
    DC ← LeerFloat("Valor DC")

    Repetir:
        f1 ← LeerFloat("Frecuencia fundamental")
    Hasta que f1 > 0

    A1 ← LeerFloat("Amplitud fundamental")
    tipo_amp ← LeerIntRango(1=pico, 2=RMS)

    Si tipo_amp = pico:
        A1_rms ← A1 / √2
    Sino:
        A1_rms ← A1

    phi1_rad ← grados → radianes

    N ← LeerIntRango("Armónicas (0–10)", 0, 10)

    armonicas ← lista vacía

    Para k = 1 hasta N:
        fk ← LeerFloat("Frecuencia")
        Ak ← LeerFloat("Amplitud")

        tipo ← LeerIntRango(1=pico, 2=RMS)

        Si tipo = pico:
            Ak_rms ← Ak / √2
        Sino:
            Ak_rms ← Ak

        fase_rad ← grados → radianes

        agregar {fk, Ak_rms, fase_rad} a armonicas

    Retornar DC, f1, A1_rms, phi1_rad, armonicas


=========================================================
4. Modelo del amplificador H_amp(ω)
=========================================================

H_amp(ω)
    j ← número imaginario

    Si ω < 18:
        num = -13.03( jω − 0.6143 )
        den = ω² − 23.55 jω − 79.68

    Sino si ω < 2×10⁹:
        num = -43.03 ω²
        den = ω² − 22.94 jω − 73.48   // término complejo corregido

    Sino:
        num = ω² (0.4ω + 8.61×10¹⁰ j)
        den = ω³ − 2×10⁹ jω² − 4.69×10¹⁰ ω + 1.41×10¹¹ j

    Retornar num / den


=========================================================
5. Salida de cada componente de frecuencia
=========================================================

SalidaArmonica(ω, A_rms, fase, R, C, modo)
    V_F = A_rms · e^(j fase)
    V_amp = H_amp(ω) · V_F

    Si modo = corto:
        retornar (0, 0)

    Si modo = abierto:
        retornar (V_amp, 0)

    Z_R = R

    Si modo = solo R:
        Z_tot ← Z_R
    Sino:
        Z_C ← 1 / (jωC)
        Z_tot ← Z_R + Z_C

    I ← V_amp / Z_tot
    V_out ← I · Z_R

    Retornar (V_out, I)


=========================================================
6. Cálculo global: VRMS, IRMS, Potencia y THD
=========================================================

CalcularRespuesta(...)
    Procesar fundamental y cada armónica

    Si modo = corto:
        VRMS = 0 ; IRMS = 0 ; P = 0 ; THD = 0
        retornar

    Si modo = abierto:
        VRMS = RMS(V)
        IRMS = 0
        P = 0
        THD = √(sumarmónicas²) / fundamental
        retornar

    // Modo normal o solo R
    VRMS = √(sum(Vout_rms²))
    IRMS = √(sum(|I|²))

    P = suma de Re{ V · conj(I) }

    THD = √(sum(armónicas²)) / fundamental

    retornar VRMS, IRMS, P, THD


=========================================================
7. Reconstrucción temporal
=========================================================

GenerarSeñalTiempo(DC, componentes)
    t ← vector de tiempo
    vout(t) = DC

    Para cada componente:
        V_pico ← V_rms √2
        vout += V_pico sin(2π f t + fase)

    retornar (t, vout)


=========================================================
8. Programa principal
=========================================================

main()
    Mostrar "Simulador de amplificador"

    (R, C, modo) ← PedirCarga()
    (DC, f1, A1_rms, phi1, armonicas) ← PedirSeñal()

    continuar ← verdadero

    Mientras continuar:
        calcular respuesta
        mostrar VRMS, IRMS, Potencia, THD
        graficar señal en el tiempo

        mostrar menú:
            1 cambiar carga
            2 cambiar señal
            3 cambiar ambas
            4 salir

        si opción = 1 → pedir carga
        si opción = 2 → pedir señal
        si opción = 3 → pedir ambas
        si opción = 4 → continuar = falso

    Fin

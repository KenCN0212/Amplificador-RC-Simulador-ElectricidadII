
1. Funciones de entrada


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



2. Lectura de la carga


PedirCarga()
    Repetir:
        C_micro ← LeerFloat
        C ← C_micro × 10⁻⁶
        R ← LeerFloat

        Mostrar:
            1) RC en serie
            2) Solo R
            3) Corto
            4) Abierto

        modo ← LeerIntRango(1,4)

    Hasta que datos válidos

    Si modo = 2 → C ← 0

    Retornar (R, C, modo)


3. Lectura de la señal


PedirSeñal()
    DC ← LeerFloat

    Repetir:
        f1 ← LeerFloat
    Hasta que f1 > 0

    A1 ← LeerFloat
    tipo_amp ← Pico/RMS

    Si tipo_amp = Pico:
        A1_rms ← A1 / √2
    Sino:
        A1_rms ← A1

    phi1_rad ← grados → radianes

    N ← número de armónicas (0–10)

    Para k = 1..N:
        fk ← LeerFloat
        Ak ← LeerFloat
        tipo ← Pico/RMS

        Si Pico:
            Ak_rms ← Ak/√2
        Sino:
            Ak_rms ← Ak

        fase_rad ← grados → rad
        agregar {fk, Ak_rms, fase_rad}

    Retornar datos


4. Modelo del amplificador H_amp(ω)

H_amp(ω)
    j ← imaginario

    Si ω < 18:
        num = -13.03 (jω − 0.6143)
        den = ω² − 23.55 jω − 79.68

    Sino si ω < 2×10⁹:
        num = -43.03 ω²
        den = ω² − 22.94 jω − 73.48

    Sino:
        num = ω² (0.4ω + 8.61×10¹⁰ j)
        den = ω³ − 2×10⁹ jω² − 4.69×10¹⁰ ω + 1.41×10¹¹ j

    Retornar num/den



5. Salida de cada componente


SalidaArmonica(ω, A_rms, fase, R, C, modo)
    V_F = A_rms e^(j fase)
    V_amp = H_amp(ω) × V_F

    Si modo = corto:
        retornar (0, 0)

    Si modo = abierto:
        retornar (V_amp, 0)

    Z_R = R

    Si modo = solo R:
        Z_tot ← Z_R
    Sino:
        Z_C ← 1/(jωC)
        Z_tot ← Z_R + Z_C

    I ← V_amp / Z_tot
    V_out ← I × Z_R

    Retornar (V_out, I)


6. Cálculo VRMS, IRMS, potencia y THD


CalcularRespuesta(...)
    Procesar fundamental y armónicas

    Si corto:
        VRMS = 0 ; IRMS = 0 ; P = 0 ; THD = 0
        retornar

    Si abierto:
        VRMS = RMS(V)
        IRMS = 0
        P = 0
        THD = √(sum armónicas²) / fundamental
        retornar

    VRMS = √(suma Vout_rms²)
    IRMS = √(suma |I|²)
    P = suma de Re{V · conj(I)}
    THD = √(sum armónicas²) / fundamental

    retornar valores


7. Reconstrucción temporal


GenerarSeñalTiempo(DC, componentes)
    t ← vector de tiempo
    vout(t) = DC

    Para cada componente:
        V_pico ← V_rms √2
        vout += V_pico sin(2π f t + fase)

    retornar (t, vout)



8. Programa principal


main()
    Leer carga
    Leer señal

    Mientras continuar:
        calcular respuesta
        mostrar resultados
        graficar

        menú:
            cambiar carga
            cambiar señal
            ambas
            salir

    Fin
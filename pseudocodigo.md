1. Funciones de entrada
  LeerFloat(mensaje)
  Repetir:
      Mostrar mensaje
      Leer x
  Hasta que x sea número válido
  Retornar x
  
  LeerInt(mensaje)
  Repetir:
      Mostrar mensaje
      Leer n
  Hasta que n sea entero válido
  Retornar n
  
  LeerIntRango(mensaje, min, max)
  Repetir:
      n ← LeerInt(mensaje)
  Hasta que min ≤ n ≤ max
  Retornar n

2. Lectura de la carga
  PedirCarga()
  Repetir:
      Pedir C (microfaradios)
      C ← C × 10⁻⁶
      Pedir R (ohmios)
  
      Mostrar modos:
        1 RC normal
        2 Solo R
        3 Corto
        4 Abierto
      modo ← LeerIntRango(1,4)
  
  Hasta que datos válidos
  
  Si modo = 2:
      C ← 0
  
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
  
  phi1 ← grados → radianes
  
  N ← número de armónicas (0-10)
  
  Para k = 1..N:
      fk ← LeerFloat
      Ak ← LeerFloat
      tipo ← Pico/RMS
      Si Pico:
          Ak_rms = Ak/√2
      fase_rad ← grados → rad
  
      agregar {fk, Ak_rms, fase_rad}
  
  Retornar datos

4. Modelo del amplificador: H_amp(ω)
  Si ω < 18:
      num = -13.03 (jω − 0.6143)
      den = ω² − 23.55 jω − 79.68
  Sino si ω < 2×10⁹:
      num = -43.03 ω²
      den = ω² − 22.94 jω − 73.48
  Sino:
      num = ω² (0.4ω + 8.61e10 j)
      den = ω³ − 2e9 jω² − 4.69e10 ω + 1.41e11 j
  
  Retornar num/den

5. Salida por componente: SalidaArmonica(ω, A_rms, fase, R, C, modo)
  V_F = A_rms e^(j fase)
  V_amp = H(ω) × V_F
  
  Si modo = corto:
      return 0, 0
  
  Si modo = abierto:
      return V_amp, 0
  
  Z_R = R
  Si modo = solo R:
      Z_tot = Z_R
  Sino:
      Z_C = 1/(jωC)
      Z_tot = Z_R + Z_C
  
  I = V_amp / Z_tot
  V_out = I × Z_R
  
  Retornar (V_out, I)

6. Cálculo de VRMS, IRMS, potencia y THD
  Procesar fundamental y armónicas
  
  Si corto:
      todo = 0
  
  Si abierto:
      VRMS = RMS(V)
      THD = armónicas/fundamental
  
  Modo normal:
      VRMS = sqrt(sum(V²))
      IRMS = sqrt(sum(|I|²))
      Potencia = sum( Re{ V·conj(I) } )
      THD = magnitudes_armónicas / magnitud_fundamental

7. Reconstrucción temporal
  t = vector de tiempo
  vout = DC
  
  Para cada componente:
      vout += V_pico sin(2π f t + fase)
  
  Retornar (t, vout)

8. Programa principal
  Leer carga
  Leer señal
  
  Mientras continuar:
      Calcular respuesta
      Mostrar VRMS, IRMS, P, THD
      Graficar señal temporal
  
      Mostrar menú
      Si cambiar carga → pedir carga
      Si cambiar señal → pedir señal
      Si ambas → pedir ambas
      Si salir → terminar

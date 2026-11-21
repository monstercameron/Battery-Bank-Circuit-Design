"""Flashlight (AL8860 buck LED driver, XP-G3 on the aluminium LED board), red night LED, 8x SK6812 glow strip.
AL8860: I_LED = 0.1 V / R_SET; 0.2 ohm -> 0.5 A (3:1 on the 1.5 A driver). CTRL < 0.2 V = off; CTRL floating = ON;
PWM < 500 Hz via open drain.

X-39 default-off independent of V3V3: the CTRL clamp FET (AO3400A, Vgs(th) <= 1.45 V) has its gate biased from the
driver's own supply LED_VIN through 220k/150k, so the clamp is on whenever the AL8860 can run:
  Vgs = VIN x 150/370:  VIN 4.5 V (AL8860 min) -> 1.82 V > 1.45 V;  VIN 21 V (VBAT max) -> 8.51 V < 12 V abs-max (1.41:1).
  Divider standby current 21 V / 370k = 57 uA; gate tau ~ 89k x 1 nF = 0.09 ms (fine for < 500 Hz PWM).
The ESP32 only RELEASES the clamp: IO13 (FLASH_PWM) high -> 2N7002 pulls the clamp gate low -> CTRL floats -> LED on.
IO13 floating / ESP32 unpowered / V3V3 dead -> 100k pull-down -> 2N7002 off -> clamp on -> LED off.

Red night LED (X-39): R >= (V5_AUX max 5.5 V - Vf min 1.6 V) / 6.67 mA = 585 ohm. 1k 0603 fitted:
  I_max = 3.9 V / 990 ohm = 3.94 mA (5.1:1 on the 20 mA LED), P = 15.5 mW in 0.1 W (6.4:1). Vf(min) 1.6 V VERIFY (KT-0603R).
"""


def build(D):
    sh = D.sheet("lighting", "Flashlight, red night light, attention-glow RGB strip")
    G = "GND"
    D.v("LED_VIN", 21.0)
    D.JP(sh, "VBAT", "LED_VIN", i_op=0.15, note="ISO flashlight driver")
    D.TP(sh, "LED_VIN", small=True)
    D.TP(sh, "GND", small=True)
    D.IC(sh, "AL8860QMP-13", {"SET": "LED_RS", "GND": G, "CTRL": "LED_CTRL", "SW": "LED_SW", "VIN": "LED_VIN", "EP": G},
         nc=["N/C"], fields={"Op_I": 0.5, "Rated_I": 1.5})
    D.v("LED_RS", 21.0)
    D.v("LED_SW", 21.0)
    D.v("LED_K", 21.0)
    D.IC(sh, "1206W4F200LT5E", {"1": "LED_VIN", "2": "LED_RS"}, prefix="R", value="0.2R 1206",
         fields={"Op_P": 0.05, "Rated_P": 0.25, "Note": "I = 0.1/0.2 = 0.5 A"})
    D.C(sh, "C_10u_50V", "LED_VIN", G, fields={"Note": ">= 10 uF X7R at VIN (datasheet)"})
    D.C(sh, "C_100n_50V", "LED_VIN", G)
    D.IC(sh, "FNR8040S470MT", {"1": "LED_K", "2": "LED_SW"}, prefix="L", value="47uH 1.7A",
         fields={"Rated_I": 1.7, "Isat": 2.0, "Op_Irms": 0.5, "Op_Ipk": 0.6})
    D.IC(sh, "SS310SMA", {"A": "LED_SW", "K": "LED_VIN"}, prefix="D", fields={"Op_I": 0.5, "Rated_I": 3.0})
    # LED board connector (XP-G3 + red LED live on the aluminium-core board)
    D.CONN(sh, "LED_BOARD", ["LED_A", "LED_K", "RED_A", "RED_K", "NTC", "GND"],
           {"LED_A": "LED_RS", "LED_K": "LED_K", "RED_A": "LED_RED_A", "RED_K": "LED_RED_K", "NTC": "LED_NTC", "GND": G},
           footprint="Connector_JST:JST_PH_B6B-PH-K_1x06_P2.00mm_Vertical", prefix="J",
           fields={"LCSC": "C131342", "MPN": "B6B-PH-K-S(LF)(SN)", "B2B": True, "Op_I": 0.5, "Rated_I": 2.0,
                   "Note": "JST PH 6-pin harness to the aluminium LED board (2 A contacts -> 4:1)"})
    D.CONN(sh, "LED_BOARD_HDR", ["LED_A", "LED_K", "RED_A", "RED_K", "NTC", "GND"],
           {"LED_A": "LED_RS", "LED_K": "LED_K", "RED_A": "LED_RED_A", "RED_K": "LED_RED_K", "NTC": "LED_NTC", "GND": G},
           footprint="Connector_JST:JST_PH_B6B-PH-K_1x06_P2.00mm_Vertical", prefix="J",
           fields={"LCSC": "C131342", "MPN": "B6B-PH-K-S(LF)(SN)", "Board": "LED", "B2B": True, "Op_I": 0.5, "Rated_I": 2.0,
                   "Note": "LED-board end of the 6-wire harness"})
    D.IC(sh, "XPGDWT-01-0000-00ME2", {"A": "LED_RS", "K": "LED_K", "3": "LED_K"}, prefix="D", value="XP-G3 5700K",
         fields={"Board": "LED", "Op_I": 0.5, "Rated_I": 2.0, "Note": "pad 3 = thermal (cathode-side) VERIFY"})
    D.jlc_generic(sh, "NTC", "NTC_10k_0603", {"1": "LED_NTC", "2": G}, prefix="TH", value="10k NTC @LED",
                  footprint="Resistor_SMD:R_0603_1608Metric", fields={"Board": "LED"})
    D.R(sh, "10k", "LED_NTC", "V3V3", fields={"Note": "read on ESP32 IO36 (SENSOR_VP, ADC1)"})
    D.TP(sh, "LED_NTC", small=True)
    # X-39: CTRL clamp, gate biased from the driver's own supply; the ESP32 can only release it
    D.IC(sh, "AO3400A", {"D": "LED_CTRL", "G": "FLASH_CLAMP_G", "S": G}, prefix="Q",
         fields={"Note": "X-39 CTRL clamp: on whenever LED_VIN >= 4.5 V (Vgs >= 1.82 V) -> LED off by default"})
    D.v("FLASH_CLAMP_G", 8.6)
    D.R(sh, "220k", "LED_VIN", "FLASH_CLAMP_G", fields={"Note": "Vgs = VIN x 150/370: 1.82 V @ 4.5 V, 8.51 V @ 21 V"})
    D.R(sh, "150k", "FLASH_CLAMP_G", G)
    D.IC(sh, "2N7002", {"D": "FLASH_CLAMP_G", "G": "FLASH_PWM", "S": G}, prefix="Q",
         fields={"Note": "X-39: IO13 high releases the clamp (LED on / PWM); 60 V part on an 8.6 V node"})
    D.R(sh, "100k", "FLASH_PWM", G, fields={"Note": "IO13 floating or ESP32 unpowered -> clamp stays on -> LED off"})
    D.TP(sh, "FLASH_PWM", small=True)
    D.TP(sh, "LED_CTRL", small=True)
    D.C(sh, "C_1n_50V", "LED_CTRL", G, fields={"Note": "soft start ~1.5 ms/nF"})
    D.v("LED_CTRL", 6.0)
    # red night light: 1k from V5_AUX -> <= 3.94 mA at 5.5 V and Vf 1.6 V (X-39)
    D.IC(sh, "KT-0603R", {"A": "LED_RED_A", "K": "LED_RED_K"}, prefix="D", value="RED night",
         fields={"Board": "LED", "Op_I": 0.0040, "Rated_I": 0.02})
    D.R(sh, "1k", "V5_AUX", "LED_RED_A", pkg="0603", p_op=0.0156,
        fields={"Note": "X-39: (5.5 V - 1.6 V Vf min) / 990 ohm = 3.94 mA <= 6.67 mA (3:1 on 20 mA)"})
    D.IC(sh, "AO3400A", {"D": "LED_RED_K", "G": "RED_LED", "S": G}, prefix="Q")
    D.v("LED_RED_K", 5.5)

    # glow strip: 8x SK6812MINI-E chained, on board B along the front-top edge light pipe
    sh = D.sheet("glow", "Attention-glow strip: 8x SK6812MINI-E (board B, front-top light pipe)", board="B")
    sh.note("X-30: the 3.3 -> 5 V data buffer is powered from the strip's own gated rail (V5_GLOW_L). AHCT inputs have no VCC "
            "clamp (VI abs-max 7 V independent of VCC), so IO4 and the expander OE line cannot back-power the strip.")
    D.v("V5_GLOW_L", 5.5)
    D.JP(sh, "V5_GLOW", "V5_GLOW_L", i_op=0.4, note="ISO glow strip")
    D.TP(sh, "V5_GLOW_L", small=True)
    D.TP(sh, "GND", small=True)
    D.IC(sh, "SN74AHCT1G125DBVR", {"~{OE}": "GLOW_OE_N", "A": "GLOW_D3V3", "GND": G, "Y": "GLOW_D5V", "VCC": "V5_GLOW_L"}, prefix="U",
         fields={"Note": "X-30: in the strip's domain; output Hi-Z by default (OE pulled up)"})
    D.C(sh, "C_100n_16V", "V5_GLOW_L", G)
    D.R(sh, "10k", "GLOW_OE_N", "V5_GLOW_L", fields={"Note": "C-11: buffer disabled (Hi-Z) by default; TCA9535 I/O is 5 V tolerant"})
    D.v("GLOW_OE_N", 5.5)
    D.v("GLOW_D5V", 5.5)
    D.R(sh, "33", "GLOW_D5V", "GLOW_D0")
    for i in range(8):
        D.IC(sh, "SK6812MINI-E_C5149201", {"GND": G, "DIN": f"GLOW_D{i}", "VDD": "V5_GLOW_L", "DOUT": f"GLOW_D{i+1}"},
             prefix="D", value=f"SK6812 #{i+1}", fields={"Op_I": 0.012, "Rated_I": 0.036, "Note": "firmware caps each channel at 1/3"})
        D.C(sh, "C_100n_16V", "V5_GLOW_L", G)
        D.v(f"GLOW_D{i}", 5.5)
    D.TP(sh, "GLOW_D8", small=True)
    D.v("GLOW_D8", 5.5)
    return sh

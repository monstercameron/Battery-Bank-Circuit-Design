"""Flashlight (AL8860 buck LED driver, XP-G3 on the aluminium LED board), red night LED, 8x SK6812 glow strip.
AL8860: I_LED = 0.1 V / R_SET; 0.2 ohm -> 0.5 A (3:1 on the 1.5 A driver). CTRL < 0.2 V = off; PWM < 500 Hz via open drain.
Default OFF: the CTRL pull-down FET's gate is pulled up, so CTRL is held low until the ESP32 drives FLASH_PWM_N low.
"""


def build(D):
    sh = D.sheet("lighting", "Flashlight, red night light, attention-glow RGB strip")
    G = "GND"
    D.IC(sh, "AL8860QMP-13", {"SET": "LED_RS", "GND": G, "CTRL": "LED_CTRL", "SW": "LED_SW", "VIN": "VBAT", "EP": G},
         nc=["N/C"], fields={"Op_I": 0.5, "Rated_I": 1.5})
    D.v("LED_RS", 21.0)
    D.v("LED_SW", 21.0)
    D.v("LED_K", 21.0)
    D.IC(sh, "1206W4F200LT5E", {"1": "VBAT", "2": "LED_RS"}, prefix="R", value="0.2R 1206",
         fields={"Op_P": 0.05, "Rated_P": 0.25, "Note": "I = 0.1/0.2 = 0.5 A"})
    D.C(sh, "C_10u_50V", "VBAT", G, fields={"Note": ">= 10 uF X7R at VIN (datasheet)"})
    D.C(sh, "C_100n_50V", "VBAT", G)
    D.IC(sh, "FNR8040S470MT", {"1": "LED_K", "2": "LED_SW"}, prefix="L", value="47uH 1.7A",
         fields={"Rated_I": 1.7, "Isat": 2.0, "Op_Irms": 0.5, "Op_Ipk": 0.6})
    D.IC(sh, "SS310SMA", {"A": "LED_SW", "K": "VBAT"}, prefix="D", fields={"Op_I": 0.5, "Rated_I": 3.0})
    # LED board connector (XP-G3 + red LED live on the aluminium-core board)
    D.CONN(sh, "LED_BOARD", ["LED_A", "LED_K", "RED_A", "RED_K", "NTC", "GND"],
           {"LED_A": "LED_RS", "LED_K": "LED_K", "RED_A": "LED_RED_A", "RED_K": "LED_RED_K", "NTC": "LED_NTC", "GND": G},
           footprint="Connector_JST:JST_PH_B6B-PH-K_1x06_P2.00mm_Vertical", prefix="J",
           fields={"LCSC": "C131342", "MPN": "B6B-PH-K-S(LF)(SN)", "Op_I": 0.5, "Rated_I": 2.0,
                   "Note": "JST PH 6-pin harness to the aluminium LED board (2 A contacts -> 4:1)"})
    D.IC(sh, "XPGDWT-01-0000-00ME2", {"A": "LED_RS", "K": "LED_K", "3": "LED_K"}, prefix="D", value="XP-G3 5700K",
         fields={"Board": "LED (aluminium core)", "Op_I": 0.5, "Rated_I": 2.0, "Note": "pad 3 = thermal (cathode-side) VERIFY"})
    D.jlc_generic(sh, "NTC", "NTC_10k_0603", {"1": "LED_NTC", "2": G}, prefix="TH", value="10k NTC @LED",
                  footprint="Resistor_SMD:R_0603_1608Metric", fields={"Board": "LED"})
    D.R(sh, "10k", "LED_NTC", "V3V3", fields={"Note": "read on an ESP32 ADC1 pin via the expander-free path TBD"})
    D.TP(sh, "LED_NTC", small=True)
    # CTRL default-off pulldown
    D.IC(sh, "AO3400A", {"D": "LED_CTRL", "G": "FLASH_PWM_N", "S": G}, prefix="Q")
    D.R(sh, "10k", "FLASH_PWM_N", "V3V3", fields={"Note": "FET on = CTRL low = LED off by default"})
    D.C(sh, "C_1n_50V", "LED_CTRL", G, fields={"Note": "soft start ~1.5 ms/nF"})
    D.v("LED_CTRL", 6.0)
    # red night light: 6.6 mA (3:1 on the 20 mA LED)
    D.IC(sh, "KT-0603R", {"A": "LED_RED_A", "K": "LED_RED_K"}, prefix="D", value="RED night",
         fields={"Board": "LED", "Op_I": 0.0066, "Rated_I": 0.02})
    D.R(sh, "470", "V5_AUX", "LED_RED_A", pkg="0603", p_op=0.021)
    D.IC(sh, "AO3400A", {"D": "LED_RED_K", "G": "RED_LED", "S": G}, prefix="Q")
    D.v("LED_RED_K", 5.5)
    # glow strip: 8x SK6812MINI-E chained
    D.R(sh, "33", "GLOW_D5V", "GLOW_D0")
    for i in range(8):
        D.IC(sh, "SK6812MINI-E_C5149201", {"GND": G, "DIN": f"GLOW_D{i}", "VDD": "V5_GLOW", "DOUT": f"GLOW_D{i+1}"},
             prefix="D", value=f"SK6812 #{i+1}", fields={"Op_I": 0.012, "Rated_I": 0.036, "Note": "firmware caps each channel at 1/3"})
        D.C(sh, "C_100n_16V", "V5_GLOW", G)
        D.v(f"GLOW_D{i}", 5.5)
    D.TP(sh, "GLOW_D8", small=True)
    D.v("GLOW_D8", 5.5)
    return sh

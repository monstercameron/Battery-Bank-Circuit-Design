"""Speakerphone audio: MAX98357A I2S class-D (ESP32 I2S1) + 2x PDM mics on one data line (ESP32 I2S0 PDM RX).
MAX98357A: SD_MODE > 1.4 V = left channel, < 0.16 V shutdown; GAIN_SLOT floating = 9 dB; 3.2 W/4 ohm @10 % THD.
3:1 rule -> ~1 W average to the speaker (firmware volume limit).
"""


def build(D):
    sh = D.sheet("audio", "Speakerphone: MAX98357A amp + 2 PDM MEMS mics")
    G = "GND"
    D.IC(sh, "MAX98357AETE+T", {"DIN": "AUD_DIN", "GND": G, "~{SD_MODE}": "AUD_SDM", "VDD": "V5_AUX", "OUTP": "AUD_SPKP",
                                 "OUTN": "AUD_SPKN", "LRCLK": "AUD_LRCLK", "BCLK": "AUD_BCLK", "EP": G},
         nc=["GAIN_SLOT", "N.C."], fields={"Op_P": 1.0, "Rated_P": 3.2, "Note": "GAIN_SLOT floating = 9 dB"})
    D.R(sh, "10k", "AMP_EN", "AUD_SDM", fields={"Note": "3.0 V at SD_MODE with the internal 100k pull-down -> left channel; IO12 low = shutdown"})
    D.C(sh, "C_10u_16V", "V5_AUX", G)
    D.C(sh, "C_100n_16V", "V5_AUX", G)
    D.CONN(sh, "SPEAKER", ["SPK+", "SPK-"], {"SPK+": "AUD_SPKP", "SPK-": "AUD_SPKN"}, footprint="", prefix="LS",
           fields={"LCSC": "C50387222", "Note": "XHXDZ 40 mm 4 ohm 3 W driver on flying leads (solder pads)"})
    D.TP(sh, "AUD_SPKP", small=True)
    D.TP(sh, "AUD_SPKN", small=True)
    for sel, side in ((G, "left"), ("V3V3", "right")):
        D.IC(sh, "MMICT390200012", {"DATA": "MIC_DATA", "SELECT": sel, "GND": G, "CLK": "MIC_CLK", "VDD": "V3V3"}, prefix="MK",
             fields={"Note": f"PDM {side} channel. Mount away from the fan; acoustic port to the top grille."})
        D.C(sh, "C_100n_16V", "V3V3", G)
    D.TP(sh, "MIC_CLK", small=True)
    D.TP(sh, "MIC_DATA", small=True)
    return sh

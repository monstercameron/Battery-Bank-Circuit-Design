"""Speakerphone audio: MAX98357A I2S class-D (ESP32 I2S1) + 2x PDM mics on one data line (ESP32 I2S0 PDM RX).
MAX98357A: SD_MODE > 1.4 V = left channel, < 0.16 V shutdown; 3.2 W/4 ohm @10 % THD at 5 V.

X-40 hardware power ceiling (speaker: 4 ohm, 3 W -> 1 W allowed by the 3:1 rule; 1 W into 4 ohm = sqrt(1 x 4) = 2.0 Vrms):
  GAIN_SLOT 100k to VDD -> minimum gain 3 dB (gain table: 100k-VDD 3 dB / VDD 6 / open 9 / GND 12 / 100k-GND 15 dB).
  0 dBFS output = 2.1 dBV + gain (ADI EngineerZone, MAX98357A gain definition) = 5.1 dBV = 1.80 Vrms sine, 2.55 V peak.
  The DAC cannot exceed full scale, so the differential output is bounded to 2.55 V peak for ANY waveform; the worst
  case is a full-scale square wave (crest factor 1) = 2.55 Vrms -> 1.62 W into 4 ohm, above 1 W.
  Series resistance 2 x 0.56 ohm (one per output leg): V_spk = 2.55 x 4 / (4 + 1.12) = 1.99 Vrms -> 0.99 W <= 1 W.
  Full-scale sine: 1.80 x 4/5.12 = 1.41 Vrms -> 0.49 W. Supply (5 V) is not the limit at 3 dB (2.55 V pk < ~4.9 V swing).
  Resistor stress (square): I = 2.55/5.12 = 0.50 A, P = 0.139 W each in a 1 W 2512 (7.2:1).
  Residual risk: a missing GAIN_SLOT resistor reverts to 9 dB (open) -> clip-limited ~3.7 W square; TP on GAIN_SLOT for ICT.
  Verify sustained-tone power and speaker temperature in the enclosure.
"""


def build(D):
    sh = D.sheet("audio", "Speakerphone: MAX98357A amp + 2 PDM MEMS mics", board="B")
    G = "GND"
    VA, VM = "V5_AMP", "V3V3_MIC"
    D.v(VA, 5.5)
    D.v(VM, 3.6)
    D.JP(sh, "V5_AUX", VA, i_op=0.5, note="ISO amp")
    D.JP(sh, "V3V3", VM, i_op=0.002, note="ISO mics")
    D.TP(sh, VA, small=True)
    D.TP(sh, "GND", small=True)
    D.IC(sh, "MAX98357AETE+T", {"DIN": "AUD_DIN", "GND": G, "~{SD_MODE}": "AUD_SDM", "VDD": VA, "OUTP": "AUD_OUTP",
                                 "OUTN": "AUD_OUTN", "LRCLK": "AUD_LRCLK", "BCLK": "AUD_BCLK", "GAIN_SLOT": "AUD_GAIN", "EP": G},
         nc=["N.C."], fields={"Op_P": 1.0, "Rated_P": 3.2,
                              "Note": "X-40: gain 3 dB (GAIN_SLOT 100k to VDD) + 2x 0.56R -> <= 0.99 W into 4 ohm for any 0 dBFS waveform"})
    D.R(sh, "100k", "AUD_GAIN", VA, fields={"Note": "X-40: GAIN_SLOT 100k to VDD = 3 dB (minimum gain)"})
    D.TP(sh, "AUD_GAIN", small=True)
    D.R(sh, "10k", "AMP_EN", "AUD_SDM", fields={"Note": "3.0 V at SD_MODE with the internal 100k pull-down -> left channel; IO12 low = shutdown"})
    D.TP(sh, "AUD_SDM", small=True)
    D.C(sh, "C_10u_16V", VA, G)
    D.C(sh, "C_100n_16V", VA, G)
    for out, spk in (("AUD_OUTP", "AUD_SPKP"), ("AUD_OUTN", "AUD_SPKN")):
        D.generic(sh, "R", "0.56R 1W 2512", "Resistor_SMD:R_2512_6332Metric", {"1": out, "2": spk}, prefix="R",
                  fields={"LCSC": "C56739", "MPN": "25121WF560LT4E", "JLC_Class": "Extended", "Rated_P": 1.0, "Op_P": 0.139,
                          "Rated_V": 200, "Note": "X-40 hardware power limit: 0.50 A worst case (0 dBFS square) -> 0.139 W"})
    D.CONN(sh, "SPEAKER", ["SPK+", "SPK-"], {"SPK+": "AUD_SPKP", "SPK-": "AUD_SPKN"}, footprint="", prefix="LS",
           fields={"_nobom": True, "Consigned": True, "Note": "C-22: off-board 40 mm 4 ohm 3 W driver (e.g. XHXDZ C50387222, low JLC stock) on flying leads to solder pads; sourced and fitted at final assembly, not by JLCPCB"})
    D.TP(sh, "AUD_SPKP", small=True)
    D.TP(sh, "AUD_SPKN", small=True)
    for sel, side in ((G, "left"), (VM, "right")):
        D.IC(sh, "MMICT390200012", {"DATA": "MIC_DATA", "SELECT": sel, "GND": G, "CLK": "MIC_CLK", "VDD": VM}, prefix="MK",
             fields={"Note": f"PDM {side} channel. Mount away from the fan; acoustic port to the top grille."})
        D.C(sh, "C_100n_16V", VM, G)
    D.TP(sh, "MIC_CLK", small=True)
    D.TP(sh, "MIC_DATA", small=True)
    return sh

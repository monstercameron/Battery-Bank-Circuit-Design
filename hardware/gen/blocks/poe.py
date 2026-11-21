"""PoE powered device on the RJ45 (802.3bt Type 3, Class 6 ~51 W at the PD) with an isolated flyback to VPOE (20.3 V, ~46 W).

Follows TIDA-050023 (TPS2373 + LM5155x flyback, 12 V out) adapted to a 20.3 V output.

TPS2373-4 (datasheet values):
  - VDD bypass 0.1 uF; DEN 24.9k; REF 49.9k; RCLSA 63.4 (class 4) + RCLSB 249 (class 1) = Class 6; APD to RTN.
  - AMPS_CTL 1.18k (DS 7.3.8 recommends 1.3k, min 1k); MPS_DUTY shorted to VSS = 12.5 % (DS Table 5, C_BULK ~100 uF,
    no blocking diode); UVLO_SEL open (VC_OUT UV falling 6.45-7.35 V).
  - VC_OUT 1 uF (startup source 13.5-15 V), VC_IN 0.1 uF from the aux winding.
  - TPH/TPL -> two optos -> expander (allocated power, DS 8.2.2.7). BT is left open: allocated power is fully encoded
    by TPH/TPL (DS Table 2); BT only tells PSE Type 1-2 from 3-4.

Flyback design point (VERIFY on bench; transformer is consigned):
  - Vin 37-57 V; fsw 219 kHz (RT 100k: f = 2.21e10/(RT + 955)); Np:Ns:Na = 18:9:5; Vor = 41.6 V; Lp 80 uH.
  - Worst case at 37 V and 52 W in: D 0.53, Ipk 3.22 A, Ipri,rms 1.95 A, Isec,pk 6.0 A, Isec,rms 3.4 A, Iout 2.3 A.
  - R_CS 25 mR: I_lim 3.72-4.28 A (100 mV +/-7 %), P 0.095 W in a 3 W part.
  - The drain is clamped by an RCD (ES1G 400 V, 3 x 10k 2 W). The clamp cap sits at about 73 V for Llk 0.6 uH, so the
    drain is about 130 V at 57 V in. The FET is 250 V (1.9x).
  - Feedback: TL431 + PC817 pulls COMP down. FB is grounded per LM5155 DS 9.3.8: the min-COMP clamp is disabled only
    with FB grounded in a flyback, which keeps light-load pulse skipping. COMP has a 47k pull-up from VCC and a 100 pF
    pole. The secondary uses a Type-II network plus a secondary soft-start (DS Fig 9-9).
  - OVP: a second opto (BZT52C22 on VPOE) pulls LM5155 UVLO low, giving a hiccup at about 23-26 V. SMBJ26A is the
    last-resort clamp.
  - LM51551 (hiccup variant, as in TIDA-050023) is fitted on the LM5155 symbol (pin-identical, C778612).
  - VCC is tied to BIAS. DS 8.3 allows this for BIAS 2.97-16 V. It gives a ~11 V gate drive from VC_OUT. VC_OUT is
    15 V max at startup; the aux clamp BZT52C16 holds it to 17.1 V max, under the VCC abs max of 18 V.
Primary side (POE_*, PRI_*) is isolated from system GND: 1500 V AC.
"""


def build(D):
    sh = D.sheet("poe", "RJ45 + PoE PD (802.3bt Class 6) + isolated flyback to VPOE", board="B")
    G = "GND"
    sh.note("ISOLATION: everything named POE_*/PRI_* is primary side. Keep >= 2.5 mm creepage to secondary/GND (1500 V AC).")
    sh.note("Flyback 37-57 V -> 20.3 V / 2.3 A, 219 kHz, Np:Ns:Na 18:9:5, Lp 80 uH, Ipk 3.22 A @37 V. VERIFY all on bench.")
    # ---------------------------------------------------------------- RJ45 MagJack (consigned)
    D.CONN(sh, "RJ45_POE_2G5", ["TD0+", "TD0-", "TD1+", "TD1-", "TD2+", "TD2-", "TD3+", "TD3-", "CT",
                                "POE_12", "POE_36", "POE_45", "POE_78", "SHIELD", "LEDG_A", "LEDG_K"],
           {"TD0+": "RJ_TD0P", "TD0-": "RJ_TD0N", "TD1+": "RJ_TD1P", "TD1-": "RJ_TD1N", "TD2+": "RJ_TD2P", "TD2-": "RJ_TD2N",
            "TD3+": "RJ_TD3P", "TD3-": "RJ_TD3N", "CT": "RJ_CT", "POE_12": "POE_P12", "POE_36": "POE_P36", "POE_45": "POE_P45",
            "POE_78": "POE_P78", "SHIELD": "RJ_SHIELD", "LEDG_A": "RJ_LEDA", "LEDG_K": G},
           footprint="", prefix="J", fields={"Consigned": True, "Op_I": 0.7, "Rated_I": 1.0,
                                             "Derating_Exception": "802.3bt per-pair current, docs/design-rules.md 1.4",
                                             "Note": "Candidates: YAGEO JXF0 / Pulse JXK0-2500NL / Daburn 56F-1803DGDZ2NL. "
                                                     "H-30: wire the PHY-side centre taps per the chosen MagJack's reference "
                                                     "circuit (single CT shown); footprint from the selected MPN (C-22)."})
    D.C(sh, "C_100n_16V", "RJ_CT", G, fields={"Note": "PHY-side centre-tap bypass (VERIFY against MagJack ref circuit, H-30)"})
    D.C(sh, "C_1n_2kV", "RJ_SHIELD", G, fields={"V_across": 0, "Note": "shield to chassis via 1 nF 2 kV (+1M bleed)"})
    D.R(sh, "1M", "RJ_SHIELD", G, pkg="0805")
    # H-25: link LED from RTL8221B LED2 (active-high with PHYAD2 strapped 0), not from INTB.
    D.R(sh, "1k", "ETH_PHY_LED2", "RJ_LEDA", fields={"Note": "H-25: LED2 (2.5G link) drives the MagJack LED"})
    D.R(sh, "4.7k", "ETH_PHY_LED2", G, fields={"Note": "PHYAD2 strap = 0 (LED2 then active-high). ethernet.py must map LED2/PHYAD2 -> ETH_PHY_LED2"})
    # H-30: DNP low-capacitance TVS footprints on the PHY side of the magnetics
    for a, b, c, d in (("RJ_TD0P", "RJ_TD0N", "RJ_TD1P", "RJ_TD1N"), ("RJ_TD2P", "RJ_TD2N", "RJ_TD3P", "RJ_TD3N")):
        D.IC(sh, "TPD4E05U06DQAR_C138714", {"D1+": a, "D1-": b, "D2+": c, "D2-": d, "GND": G},
             nc=["NC"], dnp=True, fields={"Note": "H-30 DNP surge footprint. VERIFY: unidirectional 5.5 V part; MDI swing vs "
                                                   "PHY common mode may need a bidirectional low-C array"})
    for n_ in ("POE_P12", "POE_P36", "POE_P45", "POE_P78"):
        D.v(n_, 57.0)
    # ---------------------------------------------------------------- input bridges + TVS
    for p in ("POE_P12", "POE_P36", "POE_P45", "POE_P78"):
        D.IC(sh, "SS310SMA", {"A": p, "K": "POE_VDD"}, prefix="D", fields={"Op_I": 0.9, "Rated_I": 3.0})
        D.IC(sh, "SS310SMA", {"A": "POE_VSS", "K": p}, prefix="D", fields={"Op_I": 0.9, "Rated_I": 3.0})
    D.v("POE_VDD", 57.0)
    D.v("POE_VSS", 0.0)
    D.IC(sh, "SMAJ58A", {"K": "POE_VDD", "A": "POE_VSS"}, prefix="D", fields={"Note": "58 V standoff (PSE 57 V max)"})
    # ---------------------------------------------------------------- TPS2373-4 PD
    D.IC(sh, "TPS2373-4RGWR", {
        "VDD": "POE_VDD", "DEN": "POE_DEN", "CLSA": "POE_CLSA", "VSS": "POE_VSS", "CLSB": "POE_CLSB", "REF": "POE_REF",
        "AMPS_CTL": "POE_AMPS", "MPS_DUTY": "POE_VSS",
        "APD": "POE_RTN", "RTN": "POE_RTN", "PG": "PRI_UVLO", "VC_OUT": "POE_VCC", "VC_IN": "POE_VAUX",
        "TPL": "PRI_TPL_K", "TPH": "PRI_TPH_K", "EP": "POE_VSS"},
        nc=["UVLO_SEL", "#BT", "NC"],
        fields={"Op_I": 1.41, "Rated_I": 2.2, "Derating_Exception": "IC-internal hot-swap FET, docs/design-rules.md 1.4",
                "Note": "hot-swap FET 0.1 ohm / 2.2 A (TPS2373-4); 52 W / 37 V = 1.41 A. MPS_DUTY shorted = 12.5 %, "
                        "UVLO_SEL open = 6.9 V VC_OUT UV, BT unused (TPH/TPL encode allocated power)"})
    D.v("POE_RTN", 0.0)  # primary-side reference (isolated)
    D.C(sh, "C_100n_250V", "POE_VDD", "POE_VSS")
    D.R(sh, "24.9k", "POE_VDD", "POE_DEN", pkg="0805", fields={"Note": "detection signature"})
    D.R(sh, "63.4", "POE_CLSA", "POE_VSS", pkg="0805", p_op=0.03,
        fields={"Note": "class 4 events 1-2 (Class 6). ~2.5 V / 40 mA = 0.1 W only during class events (< 100 ms at power-up); ~0 W average"})
    D.R(sh, "249", "POE_CLSB", "POE_VSS", pkg="0805", p_op=0.03,
        fields={"Note": "class 1 events 3+ (Class 6). 25 mW during class events only"})
    D.R(sh, "49.9k", "POE_REF", "POE_VSS", pkg="0805")
    D.v("POE_CLSA", 2.6)   # classification output ~2.5 V (abs max 6.5 V)
    D.v("POE_CLSB", 2.6)
    D.v("POE_REF", 1.5)    # internal 1.5 V reference
    # P-44: automatic MPS. 4 x 4.7k = 1.18k (DS: 1.3k typ, >= 1k). ~20 mA pulses at ~24 V, 12.5 % duty.
    for _ in range(4):
        D.R(sh, "4.7k", "POE_AMPS", "POE_VSS", pkg="0805", p_op=0.016,
            fields={"V_across": 24.0, "Note": "P-44 R_AMPS (1 of 4). Peak 0.12 W during the MPS pulse, 0.016 W average at 12.5 % duty"})
    D.v("POE_AMPS", 30.0)
    # VC_OUT / VC_IN (advanced startup). POE_VCC also feeds LM5155 BIAS+VCC.
    D.C(sh, "C_1u_16V", "POE_VCC", "POE_RTN", fields={"Note": "VC_OUT 1 uF (DS). Part is 50 V X5R 0603"})
    D.C(sh, "C_100n_50V", "POE_VAUX", "POE_RTN", fields={"Note": "VC_IN 0.1 uF (DS: ~1/10 of VC_OUT)"})
    D.v("POE_VCC", 17.1)    # startup 15 V max; aux clamp BZT52C16 17.1 V max (fault)
    D.v("POE_VAUX", 17.1)
    # ---------------------------------------------------------------- primary bulk + HF input caps (P-18)
    for _ in range(2):
        D.IC(sh, "RV100V47M8X10", {"1": "POE_VDD", "2": "POE_RTN"}, prefix="C", value="47uF 100V elec",
             fields={"Note": "pin 1 = + VERIFY on footprint; ripple rating VERIFY (MLCCs carry the HF ripple)", "Rated_V": 100})
    for _ in range(3):
        D.IC(sh, "FS55X225K251EGG", {"1": "POE_VDD", "2": "POE_RTN"}, prefix="C", value="2.2uF 250V X7R 2220",
             fields={"Rated_V": 250, "Note": "P-18 HF input caps: place tight across transformer primary + FET + R_CS loop"})
    # ---------------------------------------------------------------- LM51551 controller
    D.IC(sh, "LM5155DSSR", {"BIAS": "POE_VCC", "VCC": "POE_VCC", "GATE": "PRI_GATE_DRV", "PGND": "POE_RTN", "CS": "PRI_CS",
                            "COMP": "PRI_COMP", "AGND": "POE_RTN", "FB": "POE_RTN", "SS": "PRI_SS", "RT": "PRI_RT",
                            "UVLO/SYNC": "PRI_UVLO", "EP": "POE_RTN"},
         nc=["PGOOD"], value="LM51551DSSR",
         fields={"LCSC": "C778612", "MPN": "LM51551DSSR",
                 "Note": "LM51551 = LM5155 with hiccup (TIDA-050023, P-43). VCC tied to BIAS (DS 8.3: 2.97-16 V). "
                         "FB grounded: secondary (opto) regulation, DS 9.3.8. PGOOD unused (meaningless with FB grounded)"})
    D.C(sh, "C_100n_50V", "POE_VCC", "POE_RTN", fields={"Note": "local VCC/BIAS decoupling at LM51551 pins 1-2"})
    # P-3 / X-18: UVLO divider from VC_OUT; TPS2373 PG (open drain) holds it low until inrush is done.
    # V_on = 1.5 x 6 = 9.0 V (8.55-9.45). V_off = 1.45 x 6 - 5 uA x 100k = 8.2 V (7.62-8.72), above the TPS2373 VCO_UV max of 7.35 V.
    D.R(sh, "100k", "POE_VCC", "PRI_UVLO", fields={"Note": "UVLO top: start 9.0 V, stop 8.2 V on VC_OUT"})
    D.R(sh, "20k", "PRI_UVLO", "POE_RTN", fields={"Note": "UVLO bottom"})
    D.C(sh, "C_1n_50V", "PRI_UVLO", "POE_RTN", fields={"Note": "UVLO filter (DS 9.3.1 C_UVLO)"})
    D.C(sh, "C_47n_50V", "PRI_SS", "POE_RTN", fields={"Note": "SS (no effect with FB grounded; secondary soft-start sets the ramp)"})
    D.R(sh, "100k", "PRI_RT", "POE_RTN", fields={"Note": "f = 2.21e10/(RT + 955) = 219 kHz VERIFY"})
    # COMP: opto pulls down against 47k pull-up from VCC + EA source (180 uA, saturated with FB = 0). Pole 47k/100p = 34 kHz.
    D.R(sh, "47k", "POE_VCC", "PRI_COMP", fields={"Note": "P-20 COMP pull-up: linear opto gain (0.3 mA max into the COMP clamp) VERIFY loop"})
    D.C(sh, "C_100p_50V", "PRI_COMP", "POE_RTN", fields={"Note": "P-20 COMP pole cap VERIFY with loop measurement"})
    # gate + switch + current sense (P-4 / X-19)
    D.R(sh, "2.2", "PRI_GATE_DRV", "PRI_GATE", pkg="0603", key="R_2.2_0603", fields={"Note": "gate resistor (tune for EMI)"})
    D.FET(sh, "IPD600N25N3G", "PRI_GATE", "PRI_DRAIN", "PRI_ISNS", vds=250, id100=17.7, irms=1.95)
    sh.parts[-1].fields["Note"] = ("250 V / 60 mR @10 V / 29 nC, TO-252. Drain max ~130 V (57 V + 73 V clamp). "
                                   "Loss ~0.4 W cond + ~0.8 W sw @37 V full load: VERIFY <= 1/3 of DPAK on our copper. Id(100C) VERIFY")
    D.IC(sh, "RLP25FEGR025", {"1": "PRI_ISNS", "2": "POE_RTN"}, prefix="R", value="25m 1% 3W 2512",
         fields={"Op_P": 0.095, "Rated_P": 3.0, "_power_part": True,
                 "Note": "P-4/X-19: I_lim = 100 mV/25 mR = 4.0 A (3.72-4.28); Ipk 3.22 A @37 V 52 W; P = 1.95^2 x 25m. Kelvin to CS"})
    D.R(sh, "100", "PRI_ISNS", "PRI_CS", fields={"Note": "CS RC filter (DS Table 10-2: 100 R + 100 pF). Slope comp: internal fixed only, VERIFY at D 0.53"})
    D.C(sh, "C_100p_50V", "PRI_CS", "POE_RTN")
    for n_, v in [("PRI_GATE_DRV", 17.1), ("PRI_GATE", 17.1), ("PRI_CS", 1.0), ("PRI_ISNS", 1.0), ("PRI_COMP", 3.0),
                  ("PRI_SS", 3.0), ("PRI_RT", 1.0), ("PRI_UVLO", 17.1), ("PRI_DRAIN", 135.0), ("PRI_SNUB", 135.0)]:
        D.v(n_, v)
    # ---------------------------------------------------------------- RCD clamp (P-5, P-19, X-20)
    # P = 0.5 Llk Ipk^2 fsw Vc/(Vc - Vor) = 0.5 x 0.6u x 3.22^2 x 219k x 73/31.4 = 1.6 W; Vc = sqrt(P x 3.33k) = 73 V.
    D.IC(sh, "ES1G_C123904", {"A": "PRI_DRAIN", "C": "PRI_SNUB"}, prefix="D",
         fields={"Op_I": 0.03, "Rated_I": 1.0, "Rated_V": 400,
                 "Note": "P-5: 400 V / 35 ns ultrafast. V_R = 57 + 73 = 130 V (3.1x). I_avg = 1.6 W / 73 V"})
    for _ in range(3):
        D.IC(sh, "HP122WF1002T4E", {"1": "PRI_SNUB", "2": "POE_VDD"}, prefix="R", value="10k 1% 2W 2512",
             fields={"Op_P": 0.54, "Rated_P": 2.0, "Rated_V": 300, "_power_part": True,
                     "Note": "P-19/X-20: 3 x 10k = 3.33k, 1.6 W total for Llk <= 0.6 uH. If the measured Llk is higher, re-size"})
    D.C(sh, "C_100n_250V", "PRI_SNUB", "POE_VDD", fields={"V_across": 75.0, "Note": "clamp cap; ~73 V across (RC = 333 us)"})
    # ---------------------------------------------------------------- transformer (consigned)
    D.CONN(sh, "T_POE_FLYBACK", ["PRI_A", "PRI_B", "SEC_A", "SEC_B", "AUX_A", "AUX_B"],
           {"PRI_A": "POE_VDD", "PRI_B": "PRI_DRAIN", "SEC_A": "SEC_SW", "SEC_B": G, "AUX_A": "PRI_AUXSW", "AUX_B": "POE_RTN"},
           footprint="", prefix="T",
           fields={"Consigned": True, "_power_part": True, "Op_Irms": 1.95, "Rated_I": 6.0, "Op_Ipk": 3.22, "Isat": 6.5,
                   "Note": "REQUIRED SPEC (no stocked part at LCSC; custom/Wurth 750-series or Coilcraft POE600F-class, VERIFY): "
                           "Np:Ns:Na = 18:9:5 (2:1:0.556); Lp 80 uH +/-10 %; Llk <= 0.6 uH; fsw 219 kHz; "
                           "Ipk 3.22 A (4.28 A at current limit), Isat >= 6.5 A; Ipri,rms 1.95 A, Isec,rms 3.4 A, "
                           "winding thermal rating >= 3x RMS (6 A pri / 10 A sec); Vin 37-57 V, Vout 20.3 V / 2.3 A (46 W), "
                           "aux 11 V / 30 mA. Isolation pri-sec 1500 Vrms 60 s (IEEE 802.3 33.4.1). "
                           "Dots: PRI_A, SEC_B, AUX_B. Footprint from selected MPN (C-22)"})
    # aux winding -> VC_IN (P-23): Na/Ns = 5/9 gives 11 V. A 10 R series resistor tames leakage peak-charging.
    # BZT52C16 clamp (<= VC_OUT 20 V abs, VCC 18 V abs).
    D.IC(sh, "B1100-13-F", {"A": "PRI_AUXSW", "C": "PRI_AUXR"}, prefix="D",
         fields={"Op_I": 0.03, "Rated_I": 1.0, "Note": "aux rectifier; V_R = 57 x 5/18 + 11 + spike ~ 32 V (100 V part)"})
    D.R(sh, "10", "PRI_AUXR", "POE_VAUX", p_op=0.01, fields={"Note": "P-23 aux series R"})
    D.IC(sh, "BZT52C16", {"K": "POE_VAUX", "A": "POE_RTN"}, prefix="D",
         fields={"Note": "P-23 aux clamp 15.3-17.1 V: above VC_OUT startup (15 V max), below VCC abs max 18 V"})
    D.v("PRI_AUXSW", 40.0)
    D.v("PRI_AUXR", 40.0)
    D.v("SEC_SW", 60.0)
    # ---------------------------------------------------------------- secondary rectifier + output
    D.IC(sh, "MBR20100CT-G1", {"1": "SEC_SW", "3": "SEC_SW", "2": "VPOE"}, prefix="D",
         fields={"Op_I": 2.3, "Rated_I": 20.0, "Rated_V": 100,
                 "Note": "dual 10 A common cathode, both anodes paralleled. V_R = 20.8 + 57/2 + clamp spike ~ 58 V (1.7x)"})
    for _ in range(3):
        D.IC(sh, "MA35V100M6X8", {"1": "VPOE", "2": G}, prefix="C", value="100uF 35V polymer",
             fields={"Rated_V": 35, "Op_I": 0.83, "Rated_I": 2.9, "_power_part": True,
                     "Note": "P-30: Icout,rms 2.48 A shared by 3 (2.9 A each @100 kHz). pin 1 = + VERIFY on footprint"})
    for _ in range(2):
        D.C(sh, "C_10u_50V", "VPOE", G, fields={"Note": "HF output decoupling at the rectifier"})
    D.IC(sh, "SMBJ26A_C123820", {"C": "VPOE", "A": G}, prefix="D",
         fields={"Note": "P-21 last-resort clamp: 26 V standoff >= 1.1 x 22 V; breakdown 28.9 V min, above the opto OVP trip"})
    # ---------------------------------------------------------------- isolated feedback: TL431 + PC817 (P-20)
    D.R(sh, "71.5k", "VPOE", "SEC_REF", fields={"Note": "2.495 x (1 + 71.5/10) = 20.3 V"})
    D.R(sh, "10k", "SEC_REF", G)
    D.IC(sh, "TL431_C181103", {"REF": "SEC_REF", "C": "SEC_OPTO_K", "A": G}, prefix="U",
         fields={"Note": "I_KA = I_LED + 1.6 mA bias; P < 60 mW"})
    D.R(sh, "10k", "VPOE", "SEC_OPTO_A", pkg="0805", p_op=0.035,
        fields={"Note": "X-20: LED feed (fast lane, gain = CTR x 47k/10k). Fault (TL431 on hard): (22-1.2-2)^2/10k = 35 mW"})
    D.R(sh, "680", "SEC_OPTO_A", "SEC_OPTO_K", p_op=0.002, fields={"Note": "P-20 bias across opto LED: >= 1.5 mA TL431 minimum"})
    D.R(sh, "10k", "SEC_OPTO_K", "SEC_FBZ", fields={"Note": "P-20 Type-II zero (10k / 10 nF = 1.6 kHz) VERIFY loop"})
    D.C(sh, "C_10n_50V", "SEC_FBZ", "SEC_REF")
    D.IC(sh, "PC817B_C2936042", {"AN": "SEC_OPTO_A", "CAT": "SEC_OPTO_K", "COL": "PRI_COMP", "EM": "POE_RTN"}, prefix="U",
         fields={"Note": "feedback opto, 5 kV isolation; CTR >= 30 % needed at 1.7 mA"})
    # secondary soft-start (P-43, LM5155 DS Fig 9-9): 0.47 uF x dV/dt = 0.25 mA -> 530 V/s, aux > 8.5 V in ~31 ms (< 50 ms TPS2373 timeout)
    D.C(sh, "C_470n_50V", "VPOE", "SEC_SSX", fields={"Note": "secondary soft-start cap VERIFY"})
    D.IC(sh, "1N4148W_C81598", {"A": "SEC_SSX", "K": "SEC_REF"}, prefix="D", fields={"Note": "soft-start diode (Si, low leakage into REF)"})
    D.R(sh, "100k", "SEC_SSX", G, fields={"Note": "soft-start discharge"})
    for n_ in ("SEC_OPTO_K", "SEC_OPTO_A", "SEC_FBZ", "SEC_SSX"):
        D.v(n_, 22.0)
    D.v("SEC_REF", 3.5)    # 2.5 V regulated; 3.4 V at a 28 V fault (TL431 REF abs max is well above)
    # ---------------------------------------------------------------- output OVP (P-21): zener + opto -> LM51551 UVLO low (hiccup)
    D.IC(sh, "BZT52C22", {"K": "VPOE", "A": "SEC_OVP_Z"}, prefix="D", fields={"Note": "P-21 OVP: trip ~23-26 V (20.8-23.3 V zener + LED)"})
    D.R(sh, "1k", "SEC_OVP_Z", "SEC_OVP_A", pkg="0805", p_op=0.036, fields={"Note": "OVP LED current limit; 6 mA at 28 V"})
    D.R(sh, "10k", "SEC_OVP_A", G, fields={"Note": "shunts zener leakage below the trip"})
    D.IC(sh, "PC817B_C2936042", {"AN": "SEC_OVP_A", "CAT": G, "COL": "PRI_UVLO", "EM": "POE_RTN"}, prefix="U",
         fields={"Note": "P-21 OVP opto: pulls LM51551 UVLO low -> stop; restarts when VPOE decays (hiccup)"})
    D.v("SEC_OVP_Z", 22.0)
    D.v("SEC_OVP_A", 1.5)  # opto LED anode: clamped by the LED forward voltage
    # ---------------------------------------------------------------- allocated power -> firmware (P-17, X-21)
    # TPH/TPL active-low open drain (DS 8.2.2.7): LED from VC_OUT via 10k (~1 mA) into TPx. Secondary active-low, 47k pull-up.
    # Decode: CLASS(TPH)=0 -> 40/51 W; CLASS_TPL=0 -> 25.5 W; both 1 -> 12.95 W or no PoE / not started (safe default).
    for tp, net in (("PRI_TPH", "EXP_POE_CLASS"), ("PRI_TPL", "EXP_POE_CLASS_TPL")):
        D.R(sh, "10k", "POE_VCC", tp + "_A", pkg="0603", p_op=0.02, fields={"Note": f"R_TPx (DS 8.2.2.7) for {tp[4:]}"})
        D.IC(sh, "PC817B_C2936042", {"AN": tp + "_A", "CAT": tp + "_K", "COL": net, "EM": G}, prefix="U",
             fields={"Note": f"P-17/X-21: TPS2373 {tp[4:]} across the barrier, active-low to the expander"})
        D.R(sh, "47k", net, "V3V3", fields={"Note": "pull-up: high = not allocated (firmware assumes 12.95 W)"})
        D.TP(sh, net, small=True)
        D.v(tp + "_A", 17.1)
        D.v(tp + "_K", 17.1)
    # ---------------------------------------------------------------- barrier Y-cap (P-22, X-8)
    D.IC(sh, "TMY1102M", {"1": "POE_RTN", "2": G}, prefix="C", value="1nF Y1 400VAC",
         fields={"Rated_V": 400, "Note": "P-22/X-8: Y1 safety cap (UL/ENEC class Y1) across the 1500 Vrms barrier; keep creepage"})
    # ---------------------------------------------------------------- test points
    D.TP(sh, "VPOE")
    D.TP(sh, "PRI_UVLO", small=True)
    D.TP(sh, "POE_VCC", small=True)
    D.TP(sh, "PRI_ISNS", small=True)
    D.TP(sh, "PRI_DRAIN", small=True)
    D.TP(sh, "POE_RTN", small=True)
    return sh

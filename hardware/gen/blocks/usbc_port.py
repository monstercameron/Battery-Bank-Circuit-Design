"""USB-C port k (1..4): connector, ESD, TPD4S480, TPS26750 + EEPROM, PD-controlled bidirectional VBUS switch
(LM74502 + back-to-back N-FETs), BQ25756 bidirectional 100 W stage, HD3SS3212 SS mux, RTL8156BG 2.5GbE with its
own 0.95 V buck.

Architecture (TI EPR reference: BQ25756 DS 7.2.2 / Fig 7-18, TPS26750 DS 8.2.2.1 / 8.4.1.2.2.6, PMP41115, SLUAAY7):
  connector VBUS -> [Qa|Qb back-to-back, LM74502 driven from TPS26750 POWER_PATH_EN] -> VAC -> 5 mOhm -> VIN -> BQ25756
  The TPS26750 owns the BQ25756 on its private I2C controller bus (I2Cc) together with the config EEPROM, and enables
  the VBUS switch only inside a contract. The ESP32 is not in the safety loop.

Datasheet values used (docs/datasheets/text/*.txt; LM74502H/PMP41115 text extracted from docs/datasheets/*.pdf):
  BQ25756  VFB = 1.536 V +-0.5 % (0-85 C) / +-0.7 % (-40..125 C); R_FBG 33..55 Ohm; K_ICHG = 48..52 A*kOhm @5 mOhm;
           K_ILIM = 48..52 A*kOhm @2 mOhm (-> 19.2..20.8 A*kOhm @5 mOhm); V_ACUV_DPM 1.21 V, V_REF_ACUV 1.1 V,
           V_REF_ACOV 1.2 V; C_IN / C_OUT >= 80 uF after derating; L time constant 0.05..1.26 uH/mOhm; R_FSW 80.6k ~347 kHz.
  TPS26750 POWER_PATH_EN 6-12 V / 8.5-11.5 uA source, Hi-Z at reset, buffer to LDO_3V3 per DS 8.4.1.2.2.6;
           LDO_3V3 from VBUS (VBUS >= 3.9 V), external load <= 5 mA (DS 5.3); C_LDO3V3 5-25 uF; C_VBUS 1-10 uF;
           I2Cc EEPROM @0x50; 4CC 'I2Cr'/'I2Cw' host passthrough and GPIO event WAIT_nPG (TRM SLVUCR7).
  TPD4S480 VPWR 2.7-4.5 V, 112/160 uA, C 0.3-1 uF; unpowered: VBUS_LV = VBUS, dead-battery Rd on C_CCx.
  LM74502  EN rising 1.24 V, OV rising 1.165/1.25/1.333 V, VS 4..60 V, C_VCAP >= 10 x Ciss, gate 60 uA (inrush with
           C_dVdT = I_GATE x C_OUT / I_INRUSH), GATE-SRC abs max 15 V (zener when SRC can collapse).
"""

# Battery-side bus the stage regulates onto. Single constant so the planned VSYS architecture (Codex X-2) is a one-line change.
STAGE_BUS = "VBAT"

ADCIN = {  # port -> (ADCIN1 source, ADCIN2 source); "DIV6" = divider to 0.806 of LDO_3V3
    1: ("LDO3", "GND"), 2: ("GND", "GND"), 3: ("DIV6", "GND"), 4: ("LDO15", "LDO3"),
}

# 0.1 % / 25 ppm thin-film FB divider parts (P-12 / X-11). Not yet in passives.json: LCSC fields set explicitly.
FB_TOP = {"LCSC": "C705752", "MPN": "RT0603BRD07249KL", "JLC_Class": "Extended", "Tolerance": "0.1% 25ppm thin film"}
FB_BOT = {"LCSC": "C705630", "MPN": "RT0402BRD0720KL", "JLC_Class": "Extended", "Tolerance": "0.1% 25ppm thin film"}

STAGE_I = 7.42  # X-17: 100 W out of a 15 V pack at 90 % -> 7.41 A average + 1.3 A p-p ripple (8.2 uH, 347 kHz) -> 7.42 A RMS
STAGE_IPK = 8.65  # 7.41 + 2.45/2 (worst ripple: buck 28 V -> 15 V)


def build(D, k):
    sh = D.sheet(f"usbc_port_{k}", f"USB-C port {k}: 100 W bidirectional PD 3.x (SPR source / EPR sink) + 2.5GbE")
    n = lambda s: f"{s}_C{k}"  # noqa: E731
    G = "GND"
    BUS = STAGE_BUS
    VBUS, VAC, VIN, VOUT, SW1, SW2 = n("VBUS"), n("VAC"), n("VIN"), n("VOUT"), n("SW1"), n("SW2")
    BUSJ = n("BUSJ")      # stage side of the isolation jumper to the battery bus
    LDO3 = n("LDO3V3")    # per-port VBUS-powered bootstrap domain (TPS26750 LDO_3V3)
    SWG, SWS, SWVS, SWCAP = n("SWG"), n("SWSRC"), n("SWVS"), n("SWCAP")
    for net, v in [(VBUS, 28.0), (VAC, 28.0), (VIN, 28.0), (VOUT, 21.0), (SW1, 28.0), (SW2, 21.0), (n("VBUSLV"), 22.0),
                   (BUSJ, 21.0), (SWS, 28.0), (SWVS, 28.0), (SWG, 42.0), (n("SWGC"), 42.0), (SWCAP, 42.0), (n("SWOV"), 1.5),
                   (n("PPEN_RAW"), 12.0), (n("ACUV"), 7.5), (n("ACOV"), 1.3), (LDO3, 3.6)]:
        D.v(net, v)

    sh.note("Port power: 100 W max. SOURCE = SPR only, max 20 V/5 A (X-14, USB PD 10.2.3.3: PDP <= 100 W stays SPR); "
            "no 28 V source PDO. EPR (28 V AVS/fixed) is used for SINKING only, request <= 28 V/3.2 A.")
    sh.note("VBUS power path (P-2 / X-6): connector -> back-to-back NTMFS5C628NL (60 V >= 1.5 x 28 V) driven by LM74502 -> VAC -> "
            "BQ25756. LM74502 EN = TPS26750 POWER_PATH_EN through TI's 2-NMOS buffer to LDO_3V3 (DS 8.4.1.2.2.6). Switch is OFF "
            "whenever the TPS26750 is unpowered, in reset, unattached or between contracts. Connector-side discharge: 24.9k bleed "
            "(tau 25 ms -> vSafe0V in < 0.15 s with the 1 uF connector cap) plus the TPS26750 VBUS discharge.")
    sh.note("Hardware OVP: LM74502 OV divider 300k/12k opens the switch at 30.3-34.7 V on the connector; BQ25756 ACOV at 31.0 V; "
            "TVS SMBJ33A. Inrush: LM74502 (60 uA gate) + 10 nF C_dVdT -> 6 V/ms, ~0.7 A into ~115 uF behind the switch.")
    sh.note("I2Cc address map (per port, private bus on LDO_3V3): M24512 EEPROM 0x50, BQ25756 0x6B. BQ ~INT -> I2Cc_IRQ, "
            "BQ ~PG -> GPIO11 (WAIT_nPG event). Trade-off: the ESP32 no longer talks to the BQ25756 directly; it reads "
            "telemetry / writes limits through the TPS26750 host port (I2Ct 0x20+k-1) with the 'I2Cr'/'I2Cw' 4CC tasks "
            "(TRM 5.5.2/5.5.3). Slower and serialised behind the PD controller, but a stalled ESP32 cannot leave VBUS live: "
            "the TPS26750 alone sequences the BQ (safe 5 V / off) and the switch. Mux channels I2C0..3 are now unused by this sheet.")
    sh.note("Dead-battery bootstrap (P-7 / X-13): TPD4S480 unpowered -> VBUS_LV = VBUS and Rd on CC; TPS26750 LDO_3V3 comes up "
            "from VBUS and powers TPD4S480 VPWR, EEPROM, I2Cc pull-ups and the switch buffer. LDO_3V3 load budget (limit 5 mA "
            "from VBUS, DS 5.3): EEPROM read <= 2 mA, TPD 0.16 mA, SDA/SCL 2 x 0.7 mA (when low), IRQ 0.33 mA, 5 x 100k "
            "pull-ups 0.17 mA, ADCIN divider 0.03 mA -> <= 4.1 mA worst case. VERIFY on EVM with empty, cut-off and absent pack.")
    sh.note("ILIM_HIZ hardware ceiling (P-8 / P-13 / X-12 / X-13), K = 19.2..20.8 A*kOhm, 1 % resistors: "
            "default 47k = 0.40/0.43/0.45 A (min/nom/max) -> pre-contract draw <= default USB 500 mA; "
            "+6.8k (QA, GPIO3 'contract' level) = 5.94k -> 3.20/3.37/3.54 A (<= 99 W at 28 V EPR sink); "
            "+15k (QB, GPIO6, SPR <= 20 V only) = 4.26k -> 4.47/4.70/4.94 A (<= 98.8 W at 20 V). Both gates 100k pull-down = default low.")
    sh.note("X-12: EN_ILIM_HIZ_PIN / EN_ICHG_PIN / DIS_CE_PIN and IAC_REV / IBAT_REV registers can override or bypass the pin "
            "limits, and the ILIM pin is not specified to limit reverse current. The only register-independent hardware "
            "ceilings on this port are the VBUS switch (on/off + OVP) and the connector-side protections; reverse (source) "
            "current is limited only by IAC_REV programmed by the TPS26750. OPEN ITEM: add a current-sense comparator into the "
            "LM74502 OV pin if a hardware reverse-current trip is required.")
    sh.note("FB tolerance budget (P-12 / X-11): 249k 0.1 % / 20.0k 0.1 %, 25 ppm. Nominal 1.536 x (1 + 249/(20 + 0.033)) = 20.63 V. "
            "High corner: VFB +0.7 % (full Tj), R ratio +0.2 % (tolerance) +0.3 % (25 ppm x 60 C, opposite drift), R_FBG = 0: "
            "1.5468 x (1 + 12.512) = 20.90 V <= 21.0 V (4.18 V/cell). Firmware must keep VFB_REG <= 0x10 (1.536 V); the "
            "1.566 V register maximum would give 21.3 V. Per-cell OV stays in the cartridge BQ77915.")
    sh.note("ICHG 7.5k: K_ICHG 48..52 -> 6.40/6.67/7.00 A (stage output). 7.00 A <= 25 A / 3 (inductor) and <= 7.42 A design point.")
    sh.note("Connector-side capacitance (X-15, Type-C Table 4-2 <= 10 uF): 1 uF/100 V + TPD4S480 VBUS_LV 1 uF (TPS26750 C_VBUS) "
            "= 2 uF nominal. Converter bulk (>= 80 uF effective each side, P-9) is all behind the switch.")
    sh.note("Data role: TPS26750 'Initiate Swap to UFP' = 1 so the host sees the RTL8156BG as a USB NIC (H-8). If the partner "
            "rejects DR_Swap (or is not PD), the bank stays DFP: power is delivered normally, DOCK_DET stays low and the NIC "
            "does not enumerate on that port (accepted limitation, X-14). VERIFY with macOS / Windows / Android hosts.")
    sh.note("Config / firmware duties (P-11, P-32, P-36, P-49): PP5V is used for VCONN ONLY - never as a VBUS source (its switch "
            "lands on TPD4S480 VBUS_LV, rated 20 mA); BQ25756 EN_JEITA = 0 (TS = connector temperature); VFB_REG <= 1.536 V; "
            "WATCHDOG never 00 on port stages; pass-through: EN_CHG_TMR = 0 / EN_TERM = 0; enable VAC discharge on detach; "
            "TPS26750 clears the dead-battery flag once V3V3 is up. GPIO map: GPIO0 SS-mux orientation, GPIO1 EPR_EN, "
            "GPIO2 TPD ~FLT, GPIO3 ILIM-A, GPIO6 ILIM-B, GPIO7 DOCK (inverted UFP-attached), GPIO11 WAIT_nPG; GPIO4/5 tied low.")

    # ---------------------------------------------------------------- connector + ESD (connector side <= 10 uF)
    J = D.IC(sh, "HC-TYPE-C-24P-MM0.8-5A-01", {
        "A4": VBUS, "A9": VBUS, "B4": VBUS, "B9": VBUS,
        "A1": G, "B1": G, "A12": G, "B12": G, "25": G, "26": G, "27": G, "28": G,
        "A5": n("CONN_CC1"), "B5": n("CONN_CC2"),
        "A6": n("DPC"), "B6": n("DPC"), "A7": n("DNC"), "B7": n("DNC"),
        "A2": n("SSTX1P"), "A3": n("SSTX1N"), "B11": n("SSRX1P"), "B10": n("SSRX1N"),
        "B2": n("SSTX2P"), "B3": n("SSTX2N"), "A11": n("SSRX2P"), "A10": n("SSRX2N"),
    }, nc=["A8", "B8"], prefix="J", fields={"Op_I": 5.0, "Rated_I": 5.0, "Derating_Exception": "USB-C 5 A contact rating, docs/design-rules.md 1.4"})
    D.IC(sh, "SMBJ33A", {"K": VBUS, "A": G}, prefix="D", fields={"Note": "VBUS TVS: standoff 33 V >= 28 V x1.1; clamp < 60 V FETs"})
    D.C(sh, "C_1u_100V", VBUS, G, fields={"Note": "connector-side VBUS cap (budget <= 10 uF incl. VBUS_LV 1 uF)"})
    D.R(sh, "24.9k", VBUS, G, pkg="0805", p_op=0.032,
        fields={"Note": "VBUS bleed / vSafe0V (X-6): 28^2/24.9k = 31 mW vs 125 mW; independent of firmware"})
    for side in (1, 2):
        D.IC(sh, "TPD4E05U06DQAR_C138714", {"D1+": n(f"SSTX{side}P"), "D1-": n(f"SSTX{side}N"),
                                             "D2+": n(f"SSRX{side}P"), "D2-": n(f"SSRX{side}N"), "GND": G},
             nc=["NC"], prefix="U")

    # ---------------------------------------------------------------- TPD4S480 CC/D+/D- protection (VPWR on LDO_3V3)
    D.IC(sh, "TPD4S480RUKR_C43131250", {
        "C_SBU1": n("DPC"), "C_SBU2": n("DNC"), "VBIAS": n("VBIAS"), "C_CC1": n("CONN_CC1"), "C_CC2": n("CONN_CC2"),
        "RPD_G1": n("CONN_CC1"), "RPD_G2": n("CONN_CC2"), "GND": G, "~{FLT}": n("TPDFLT"), "VPWR": LDO3,
        "CC1": n("CC1"), "CC2": n("CC2"), "SBU1": n("U2DP"), "SBU2": n("U2DN"), "EPR_EN": n("EPREN"),
        "VBUS_LV": n("VBUSLV"), "VBUS": VBUS, "EP": G}, nc=["EPR_BLK_G"],
        fields={"Note": "VPWR from TPS26750 LDO_3V3 (P-7 dead battery). SBU channels protect USB2 D+/D- (datasheet pin note). "
                        "VERIFY USB2 HS signal integrity."})
    D.C(sh, "C_100n_100V", n("VBIAS"), G, fields={"Note": "VBIAS cap: >=63 V required, 100 V recommended"})
    D.C(sh, "C_1u_16V", LDO3, G, fields={"Note": "TPD4S480 VPWR cap (0.3-1 uF)"})
    D.R(sh, "10k", n("TPDFLT"), LDO3)
    D.R(sh, "100k", n("EPREN"), G)

    # ---------------------------------------------------------------- TPS26750 PD controller
    a1, a2 = ADCIN[k]
    src = {"LDO3": LDO3, "LDO15": n("LDO1V5"), "GND": G}
    adc1 = n("ADCIN1") if a1 == "DIV6" else src[a1]
    adc2 = src[a2]
    D.IC(sh, "TPS26750SRSMR_C42166327", {
        "LDO_3V3": LDO3, "ADCIN1": adc1, "ADCIN2": adc2, "LDO_1V5": n("LDO1V5"),
        "GPIO0": n("MUXSEL"), "GPIO1": n("EPREN"), "GPIO2": n("TPDFLT"), "GPIO3": n("ILIMA_EN"), "GPIO6": n("ILIMB_EN"),
        "GPIO7": n("DOCKOFF"), "GPIO11": n("PG"), "GPIO4/USB_P/LD1": G, "GPIO5/USB_N/LD2": G,
        "I2Ct_SDA": "I2C_SDA", "I2Ct_SCL": "I2C_SCL", "~{I2Ct_IRQ}": "PD_INT_N", "GND": G,
        "I2Cc_SDA": n("PDE_SDA"), "I2Cc_SCL": n("PDE_SCL"), "~{I2Cc_IRQ}": n("PDE_IRQ"),
        "POWER_PATH_EN": n("PPEN_RAW"),
        "CC1": n("CC1"), "CC2": n("CC2"), "VBUS": n("VBUSLV"), "PP5V": "V5_PD", "VIN_3V3": "V3V3"},
        nc=["NC"],
        fields={"Note": f"I2C target 0x{0x20 + k - 1:02X} (ADCIN SafeMode strap #{k}); config + patch from EEPROM 0x50; "
                        "controls BQ25756 (0x6B) on I2Cc and the PPEXT switch. Unused GPIO4/5 tied to GND (P-46). "
                        "PP5V = VCONN only. GPIO events VERIFY in Application Customization Tool (H-17)."})
    if a1 == "DIV6":
        D.R(sh, "24k", LDO3, n("ADCIN1"))
        D.R(sh, "100k", n("ADCIN1"), G)
    D.C(sh, "C_10u_16V", LDO3, G)
    D.C(sh, "C_10u_16V", n("LDO1V5"), G)
    D.C(sh, "C_10u_16V", "V3V3", G)
    D.C(sh, "C_1u_50V", n("VBUSLV"), G,
        fields={"Note": "P-33: 1 uF = TPS26750 C_VBUS min, keeps VBUS_LV (20 mA, EPR divider 0.42) response fast"})
    D.C(sh, "C_22u_10V", "V5_PD", G, fields={"Note": "PP5V (VCONN only). Datasheet lists 120 uF when sourcing 3 A from PP5V - not used here."})
    D.C(sh, "C_330p_50V", n("CC1"), G)
    D.C(sh, "C_330p_50V", n("CC2"), G)
    # private I2C controller bus: EEPROM + BQ25756, all on the VBUS-powered LDO_3V3 domain (P-7)
    D.R(sh, "4.7k", n("PDE_SDA"), LDO3)
    D.R(sh, "4.7k", n("PDE_SCL"), LDO3)
    D.R(sh, "10k", n("PDE_IRQ"), LDO3, fields={"Note": "BQ25756 ~INT (256 us pulses) -> TPS26750 I2Cc_IRQ"})
    D.IC(sh, "M24512-RMN6TP", {"E0": G, "E1": G, "E2": G, "VSS": G, "SDA": n("PDE_SDA"), "SCL": n("PDE_SCL"),
                                "~{WC}": G, "VCC": LDO3},
         fields={"Note": "64 KB (>= 36 KB required) PD config/patch EEPROM @0x50, powered from LDO_3V3 (P-7)"})
    D.C(sh, "C_100n_16V", LDO3, G)
    for t in (n("PDE_SDA"), n("PDE_SCL"), n("PDE_IRQ"), LDO3):
        D.TP(sh, t, small=True)
    D.TP(sh, G, small=True)

    # ---------------------------------------------------------------- POWER_PATH_EN buffer (TPS26750 DS 8.4.1.2.2.6)
    D.R(sh, "1M", n("PPEN_RAW"), G, fields={"Note": "defines gate while POWER_PATH_EN is Hi-Z; 8.5 uA x 1M > 6 V when on"})
    D.IC(sh, "2N7002", {"G": n("PPEN_RAW"), "S": G, "D": n("PPEN_N")}, prefix="Q",
         fields={"Note": "Q6: POWER_PATH_EN (6-12 V) level shift; Vgs 20 V rated"})
    D.R(sh, "100k", LDO3, n("PPEN_N"))
    D.IC(sh, "AO3400A", {"G": n("PPEN_N"), "S": G, "D": n("PPEN")}, prefix="Q", fields={"Note": "Q7: non-inverting stage"})
    D.R(sh, "100k", LDO3, n("PPEN"), fields={"Note": "PPEN high (3.3 V) = path enabled; 0 V when LDO_3V3 is down"})
    D.TP(sh, n("PPEN"), small=True)

    # ---------------------------------------------------------------- bidirectional VBUS switch (P-2 / X-6)
    D.IC(sh, "LM74502DDFR", {"EN/UVLO": n("PPEN"), "GND": G, "VCAP": SWCAP, "VS": SWVS, "GATE": SWG,
                             "OV": n("SWOV"), "SRC": SWS}, nc=["N.C"],
         fields={"Note": "LM74502 (60 uA gate: inrush control; the H variant cannot use C_dVdT). Back-to-back common-source "
                         "drive. VS diode-ORed from both sides so the switch works as source and as sink. "
                         "VERIFY VS >= 3.9 V POR at vSafe5V min (4.75 V - 0.5 V diode)."})
    D.FET(sh, "NTMFS5C628NLT1G", SWG, VBUS, SWS, vds=60, id100=100, irms=5.0)  # Qa, drain at connector
    D.FET(sh, "NTMFS5C628NLT1G", SWG, VAC, SWS, vds=60, id100=100, irms=5.0)   # Qb, drain at BQ side
    D.IC(sh, "1N4148W_C81598", {"A": VBUS, "K": SWVS}, prefix="D", fields={"Note": "VS supply from connector (sink), 75 V"})
    D.IC(sh, "1N4148W_C81598", {"A": VAC, "K": SWVS}, prefix="D", fields={"Note": "VS supply from BQ side (source), 75 V"})
    D.C(sh, "C_100n_100V", SWVS, G, fields={"Note": "VS cap (>= 22 nF)"})
    D.C(sh, "C_470n_50V", SWCAP, SWVS, fields={"V_across": 14.0, "Note": "VCAP >= 10 x Ciss: 10 x 2 x 3.6 nF (LCSC listing) = 72 nF; 470 nF -> ~10 ms first enable"})
    D.IC(sh, "BZT52C13", {"K": SWG, "A": SWS}, prefix="D",
         fields={"Note": "GATE-SRC clamp 12.4-14.1 V < 15 V abs max (LM74502 DS 9.3.3 / 9.4: SRC can collapse on a short)"})
    D.R(sh, "1k", SWG, n("SWGC"), p_op=0.002,
        fields={"V_across": 14.0, "Note": "R_G isolation for C_dVdT (DS Fig 8-2). Op_P: carries only the 60 uA gate current "
                                          "(3.6 uW) plus a 1 uJ C_dVdT discharge per turn-off; 2 mW is a generous bound"})
    D.C(sh, "C_10n_100V", n("SWGC"), G, fields={"Note": "C_dVdT: 60 uA / 10 nF = 6 V/ms; I_inrush = 60u x 115u / 10n = 0.7 A"})
    D.R(sh, "300k", VBUS, n("SWOV"))
    D.R(sh, "12k", n("SWOV"), G, fields={"Note": "OV cut-off 1.25 x 312/12 = 32.5 V (30.3..34.7 V)"})
    for t in (SWG, SWS, VAC):
        D.TP(sh, t, small=True)

    # ---------------------------------------------------------------- BQ25756 100 W stage
    D.JP(sh, BUS, BUSJ, i_op=STAGE_I, note="stage isolate (copper bridge, size for 3 x 7.4 A)")
    D.IC(sh, "BQ25756RRVR", {
        "SCL": n("PDE_SCL"), "SDA": n("PDE_SDA"), "~{INT}": n("PDE_IRQ"), "STAT1": n("STAT1"), "STAT2": n("STAT2"),
        "~{PG}": n("PG"), "~{CE}": n("CE"), "TS": n("TS"), "ICHG": n("ICHG"), "ILIM_HIZ": n("ILIM"), "FBG": n("FBG"),
        "FB": n("FB"), "SRN": BUSJ, "SRP": VOUT, "PGND": G, "SW2": SW2, "HIDRV2": n("HD2"), "BTST2": n("BT2"),
        "LODRV2": n("LD2"), "DRV_SUP": n("REGN"), "REGN": n("REGN"), "LODRV1": n("LD1"), "BTST1": n("BT1"),
        "HIDRV1": n("HD1"), "SW1": SW1, "ACN": VIN, "ACP": VAC, "VAC": VAC, "ACUV": n("ACUV"), "ACOV": n("ACOV"),
        "FSW_SYNC": n("FSW")},
        nc=["NC"], fields={"Note": "I2C 0x6B on the TPS26750 I2Cc bus (P-2). VAC/ACP behind the port switch. "
                                   "P-36: DRV_SUP = REGN gate-drive loss unverified (VERIFY Qg)."})
    q = "NTMFS5C628NLT1G"  # 60 V (>= 1.5 x 28 V), I_D(100 C) >> 3 x 7.42 A
    for g, d, s, gn in [(n("HD1g"), VIN, SW1, n("HD1")), (n("LD1g"), SW1, G, n("LD1")),
                        (n("HD2g"), VOUT, SW2, n("HD2")), (n("LD2g"), SW2, G, n("LD2"))]:
        D.FET(sh, q, g, d, s, vds=60, id100=100, irms=STAGE_I)
        D.R(sh, "0", gn, g, fields={"Note": "gate resistor footprint (0 ohm; tune for EMI)"})
    D.L(sh, "YSPIT1510A-8R2M", SW1, SW2, rated_i=25, isat=32, irms=STAGE_I, ipk=STAGE_IPK, value="8.2uH 25A 7.2mR")
    sh.note("Inductor (P-37 / X-17): YSPIT1510A-8R2M 8.2 uH, 25 A rated, 32 A sat, DCR 7.2 mOhm -> L/DCR 1.14 uH/mOhm "
            "(BQ25756 window 0.05..1.26). 25/7.42 = 3.4:1 rated, 32/8.65 = 3.7:1 sat. Ripple 2.45 A p-p worst (33 %). "
            "Values from the LCSC listing; VERIFY against the Yushan datasheet.")
    D.RSENSE(sh, VAC, VIN, i_op=5.0)
    D.RSENSE(sh, VOUT, BUSJ, i_op=STAGE_I)
    D.C(sh, "C_100n_16V", n("BT1"), SW1, fields={"V_across": 5.5})
    D.C(sh, "C_100n_16V", n("BT2"), SW2, fields={"V_across": 5.5})
    D.C(sh, "C_4u7_16V", n("REGN"), G)
    D.C(sh, "C_4u7_16V", n("REGN"), G)
    # sense filters
    D.C(sh, "C_470n_100V", VAC, VIN, fields={"V_across": 1.0})
    D.C(sh, "C_100n_100V", VAC, G)
    D.C(sh, "C_470n_100V", VIN, G)
    D.C(sh, "C_470n_50V", VOUT, BUSJ, fields={"V_across": 1.0})
    D.C(sh, "C_100n_50V", VOUT, G)
    D.C(sh, "C_100n_50V", BUSJ, G)
    # bulk (P-9 / X-15): >= 80 uF effective each side, all behind the port switch, split across R_AC_SNS (DS 7.2.1.2.5)
    poly = {"Rated_V": 35, "Note": "47 uF 35 V polymer (1.25 x 28 V), 35 mOhm, 2.65 A ripple; no DC-bias loss. "
                                   "Pin 1 = + (VERIFY footprint polarity mark)"}
    D.C(sh, "C_1u_100V", VAC, G, fields={"Note": "BQ25756 VAC pin 1 uF"})
    for net in (VAC, VIN):
        D.IC(sh, "MA35V47M6X6", {"1": net, "2": G}, prefix="C", fields=dict(poly))
        for _ in range(2):
            D.C(sh, "C_4u7_100V", net, G)
    D.C(sh, "C_100n_100V", VIN, G)
    sh.note("Bulk budget: input 2 x 47 uF polymer (-20 % = 75 uF) + 4 x 4.7 uF/100 V X7R 1210 (~3.5 uF each at 28 V) = 89 uF "
            "effective; output 2 x 47 uF polymer (75 uF) + 4 x 10 uF/50 V X5R 1206 (~3.5 uF each at 21 V, P-47) = 89 uF >= 80 uF.")
    for _ in range(2):
        D.IC(sh, "MA35V47M6X6", {"1": VOUT, "2": G}, prefix="C", fields=dict(poly))
    for _ in range(4):
        D.C(sh, "C_10u_50V", VOUT, G)
    # ACUV / ACOV window (P-8): 1.00M / 300k / 52.3k -> DPM 4.65 V, UVP 4.22 V, OVP 31.0 V
    D.R(sh, "1M", VAC, n("ACUV"))
    D.R(sh, "300k", n("ACUV"), n("ACOV"))
    D.R(sh, "52.3k", n("ACOV"), G, fields={"Note": "VAC_DPM 1.21 x 1352.3/352.3 = 4.65 V; UVP 4.22 V; OVP 1.2 x 1352.3/52.3 = 31.0 V"})
    # programming resistors
    D.R(sh, "249k", BUSJ, n("FB"), pkg="0603", fields=dict(FB_TOP, Note="VBAT_REG 20.63 V nom, <= 20.90 V high corner (see sheet note)"))
    D.R(sh, "20k", n("FB"), n("FBG"), fields=dict(FB_BOT))
    D.R(sh, "7.5k", n("ICHG"), G, fields={"Note": "ICHG 48..52/7.5k = 6.40..7.00 A (stage output into the bus)"})
    # switched ILIM network (P-8 / P-13 / X-13): default low, raised only by the PD controller
    D.R(sh, "47k", n("ILIM"), G, fields={"Note": "default 0.43 A (<= 0.45 A high corner) before any contract"})
    D.R(sh, "6.8k", n("ILIM"), n("ILIMA"))
    D.IC(sh, "AO3400A", {"G": n("ILIMA_EN"), "S": G, "D": n("ILIMA")}, prefix="Q",
         fields={"Note": "QA: contract level, 3.37 A nom (<= 3.54 A -> <= 99 W at 28 V)"})
    D.R(sh, "100k", n("ILIMA_EN"), G)
    D.R(sh, "15k", n("ILIM"), n("ILIMB"))
    D.IC(sh, "AO3400A", {"G": n("ILIMB_EN"), "S": G, "D": n("ILIMB")}, prefix="Q",
         fields={"Note": "QB: SPR <= 20 V only, with QA 4.70 A nom (<= 4.94 A -> <= 98.8 W at 20 V)"})
    D.R(sh, "100k", n("ILIMB_EN"), G)
    D.R(sh, "80.6k", n("FSW"), G, fields={"Note": "~347 kHz"})
    D.R(sh, "5.23k", n("REGN"), n("TS"))
    D.R(sh, "30.1k", n("TS"), G)
    D.jlc_generic(sh, "NTC", "NTC_10k_0603", {"1": n("TS"), "2": G}, prefix="TH", value="10k NTC @connector",
                  footprint="Resistor_SMD:R_0603_1608Metric",
                  fields={"Note": "Place at the USB-C connector: TS = connector temperature; EN_JEITA = 0 (P-32)"})
    D.R(sh, "10k", n("CE"), G, fields={"Note": "charge enabled in hardware; pack-level limiter may drive ~CE high (P-10, lead)"})
    D.TP(sh, n("CE"), small=True)
    D.TP(sh, n("STAT1"), small=True)
    D.TP(sh, n("STAT2"), small=True)
    D.TP(sh, n("PG"), small=True)
    D.R(sh, "100k", n("PG"), LDO3, fields={"Note": "~PG -> TPS26750 GPIO11 (WAIT_nPG) in the LDO_3V3 domain"})
    D.JP(sh, "V3V3", n("PGLED"), note="LED cut")
    D.R(sh, "2.2k", n("PGLED"), n("PGLEDK"))
    D.IC(sh, "KT-0603R", {"A": n("PGLEDK"), "K": n("PG")}, prefix="D", value="PG LED")
    for t in (VBUS, VIN, VOUT, SW1, SW2):
        D.TP(sh, t)

    # ---------------------------------------------------------------- SuperSpeed mux + RTL8156BG
    D.IC(sh, "HD3SS3212IRKSR", {
        "OEn": G, "A0p": n("TXC_P"), "A0n": n("TXC_N"), "A1p": n("U3RXP"), "A1n": n("U3RXN"), "GND": G, "VCC": "V3V3",
        "SEL": n("MUXSELR"), "B0P": n("SSTX1P"), "B0N": n("SSTX1N"), "B1P": n("SSRX1P"), "B1N": n("SSRX1N"),
        "C0P": n("SSTX2P"), "C0N": n("SSTX2N"), "C1P": n("SSRX2P"), "C1N": n("SSRX2N"), "EP": G},
        nc=["RSVD1", "RSVD2"], fields={"Note": "SEL from TPS26750 GPIO0 configured as plug-orientation output. RSVD may be NC (DS)."})
    D.C(sh, "C_100n_16V", "V3V3", G)
    D.R(sh, "1k", n("MUXSEL"), n("MUXSELR"), fields={"Note": "H-6: mux on always-on V3V3; series R on SEL"})
    D.C(sh, "C_100n_16V", n("U3TXP"), n("TXC_P"), fields={"Note": "USB3 TX AC coupling (device side)"})
    D.C(sh, "C_100n_16V", n("U3TXN"), n("TXC_N"))
    V09 = n("V0V95")
    D.v(V09, 1.0)
    mdi = {}
    for i, pair in enumerate("ABCD"):
        mdi[f"MDIP{i}"] = n(f"MDI{i}P")
        mdi[f"MDIN{i}"] = n(f"MDI{i}N")
    D.IC(sh, "RTL8156BG-CG", {
        "POW_EXT_SWR": n("EXTSWR"), "DVDD09": V09, "AVDD09": V09, "U3VDD09": V09, "U2VDD09": V09,
        "AVDD33": "V3V3_ETH", "AVDD33_XTAL": "V3V3_ETH", "DVDD33": "V3V3_ETH", "DVDD33_UPS": "V3V3_ETH", "U2VDD33": "V3V3_ETH",
        "DVDD09_UPS": n("UPS09"), "CKXTAL1": n("XI"), "CKXTAL2": n("XO"), "RSET": n("RSET"),
        **mdi, "LED2": n("LINKLED"), "U3SSTXP": n("U3TXP"), "U3SSTXN": n("U3TXN"),
        "U3SSRXP": n("U3RXP"), "U3SSRXN": n("U3RXN"), "U2DM": n("U2DN"), "U2DP": n("U2DP"), "GND": G,
        "DOCK_DET": n("DOCKDET"), "CONFIG_SEQ": n("CFGSEQ"), "GPI": n("NICGPI")},
        nc=["LANWAKEB", "NC", "CKOUT", "EEDO/SPISO", "TWSI_SDA/SPICSB", "EECS/TWSI_SCL", "GPIO3", "GPIO2/SCL",
            "GPIO1/SDA", "LED0/EEDI/SPISI", "LED1/EESK/SPISCK", "LED3", "GPIO4"],
        fields={"Note": "MAC in eFUSE (Realtek PG tool). RSET value VERIFY (2.49k assumed, as RTL8221B/RTL8372N)."})
    # H-15 / H-16 / H-17: DOCK_DET follows the TPS26750 'attached as UFP' event; open-drain so no back-power into V3V3_ETH
    D.R(sh, "10k", "V3V3_ETH", n("DOCKDET"), fields={"Note": "DOCK_DET high = connected (DS Table 11)"})
    D.IC(sh, "AO3400A", {"G": n("DOCKOFF"), "S": G, "D": n("DOCKDET")}, prefix="Q",
         fields={"Note": "holds DOCK_DET low (NIC detached, no D+ pull-up) until the TPS26750 reports UFP attach"})
    D.R(sh, "100k", LDO3, n("DOCKOFF"), fields={"Note": "default: DOCK_DET low. GPIO7 drives low on 'UFP attached' (inverted event). VERIFY"})
    D.R(sh, "10k", n("CFGSEQ"), G, fields={"Note": "H-15: CONFIG_SEQ low = NCM as configuration 1 (driverless)"})
    D.R(sh, "10k", "V3V3_ETH", n("NICGPI"), fields={"Note": "H-15: GPI high = LAN not disabled"})
    D.R(sh, "2.49k", n("RSET"), G)
    D.IC(sh, "NX3225SA-25MHZ-STD-CSR-6", {"1": n("XI"), "3": n("XO"), "GND": G}, prefix="Y", value="25MHz 10pF")
    D.C(sh, "C_12p_50V", n("XI"), G)
    D.C(sh, "C_12p_50V", n("XO"), G)
    D.C(sh, "C_1u_16V", n("UPS09"), G, fields={"Note": "DVDD09_UPS internal LDO output - own cap only. VERIFY value"})
    for _ in range(6):
        D.C(sh, "C_100n_16V", V09, G)
    D.C(sh, "C_22u_6V3", V09, G)
    for _ in range(6):
        D.C(sh, "C_100n_16V", "V3V3_ETH", G)
    D.C(sh, "C_10u_16V", "V3V3_ETH", G)
    D.R(sh, "1k", "V3V3_ETH", n("LINKLEDA"))
    D.IC(sh, "KT-0603R", {"A": n("LINKLEDA"), "K": n("LINKLED")}, prefix="D", value="LINK LED")
    # MDI PHY-to-PHY AC coupling to RTL8372N port (k-1). VERIFY values with Realtek (100 nF typical).
    for i, pair in enumerate("ABCD"):
        for pol in "PN":
            D.C(sh, "C_100n_16V", n(f"MDI{i}{pol}"), f"SW_P{k-1}MDI{pair}{pol}",
                fields={"Note": "PHY-to-PHY capacitive coupling (no magnetics)"})
    # NIC core buck: TPS62933F 5 V -> 0.95 V, enabled by RTL8156BG POW_EXT_SWR
    D.IC(sh, "TPS62933FDRLR", {"RT": G, "EN": n("EXTSWR"), "VIN": "V5_ETH", "GND": G, "SW": n("BSW"),
                                "BST": n("BBST"), "SS": n("BSS"), "FB": n("BFB")},
         fields={"Op_I": 0.65, "Rated_I": 3.0,
                 "Note": "H-10: FCCM variant at 1.2 MHz (RT=GND) from V5_ETH; 0.65 A NIC core vs 3 A -> 4.6:1"})
    D.v(n("BSW"), 5.5)
    D.C(sh, "C_33n_50V", n("BSS"), G, fields={"Note": "soft start ~5 ms"})
    D.R(sh, "100k", n("EXTSWR"), G, fields={"Note": "keeps buck off while the NIC is unpowered"})
    D.C(sh, "C_100n_16V", n("BBST"), n("BSW"), fields={"V_across": 5.5})
    D.L(sh, "FNR6045S2R2MT", n("BSW"), V09, rated_i=5.0, isat=7.4, irms=0.65, ipk=0.8, value="2.2uH 5A")
    D.R(sh, "1.87k", V09, n("BFB"), fields={"Note": "0.8 x (1 + 1.87/10) = 0.950 V"})
    D.R(sh, "10k", n("BFB"), G)
    D.C(sh, "C_10u_16V", "V5_ETH", G)
    D.C(sh, "C_100n_16V", "V5_ETH", G)
    D.C(sh, "C_22u_6V3", V09, G)
    D.TP(sh, V09)
    return sh

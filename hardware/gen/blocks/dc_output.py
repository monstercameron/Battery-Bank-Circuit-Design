"""DC barrel output 12-24 V (app-selected, default OFF): BQ25756 in reverse mode regulating VDCOUT_RAW
(VAC_REV, 20 mV steps), then TPS26631 eFuse (I_LIM 1.65 A = 3:1 on the 5 A jack) and an LM74700
ideal diode so nothing plugged into the jack can back-feed the converter.
CE is pulled HIGH in hardware: this stage never charges (forward mode disabled); firmware sets EN_REV.

Voltages: VAC_REV max 24 V +2 % (BQ25756 V_REV_ACC) = 24.5 V -> VDCOUT_RAW / DCO_EF / VDCOUT rated 24.5 V
(50 V MLCC = 2.04x). eFuse OV 27.1 V nominal, 26.4 V low corner > 24.5 V: no nuisance trip at 24 V (P-15b).
Hardware reverse-current ceiling: ILIM_HIZ 13k -> 1.54 A (P-42: below the 1.65 A eFuse, so the eFuse is the backup;
the pin also caps IAC_REV per the TI EPR example, VERIFY).
"""
from blocks.power_input import bq_stage, efuse, ideal_diode


def build(D):
    sh = D.sheet("dc_output", "DC barrel output 12-24 V, 37 W max, default off")
    sh.note("Output voltage set by BQ25756 VAC_REV over I2C (mux ch5). Power-up state: EN_REV=0 -> output off.")
    sh.note("Glow LEDs show the selected voltage; the app requires an explicit confirm before enabling.")
    sh.note("Hardware ceiling 1.54 A (ILIM_HIZ 13k) -> 37 W at 24 V; eFuse 1.65 A is the backup.")
    D.v("VDCOUT_RAW", 24.5)
    bq_stage(D, sh, "DCO", "VDCOUT_RAW", 5, ichg_r="10k", ilim_r="13k", ce_net="DCO_CE", vmax=24.5,
             note="Reverse-only stage (CE high blocks charging). ILIM 20/13k = 1.54 A hardware ceiling; IAC_REV <= 1.5 A by firmware.",
             irms=2.9)
    D.v("DCO_CE", 3.6)
    D.R(sh, "10k", "DCO_CE", "V3V3", fields={"Note": "charging disabled in hardware"})
    D.TP(sh, "DCO_CE", small=True)
    D.TP(sh, "VDCOUT_RAW")
    efuse(D, sh, "VDCOUT_RAW", "DCO_EF", "DCOF", note="IN_SYS fed from the converter side", vin_max=24.5, vout_max=24.5)
    ideal_diode(D, sh, "DCO_EF", "VDCOUT", "DCO_ORING", vmax=24.5)
    D.v("VDCOUT", 24.5)
    D.IC(sh, "SMBJ33CA-C78420", {"1": "VDCOUT", "2": "GND"}, prefix="D", value="SMBJ33CA",
         fields={"Note": "P-48: bidirectional: a reverse source on DC OUT does not forward-bias the clamp. Standoff 33 V > 24.5 V"})
    D.C(sh, "C_10u_50V", "VDCOUT", "GND")
    D.IC(sh, "DC-005-5A-2.5", {"1": "VDCOUT", "2": "GND", "3": "GND"}, prefix="J", value="DC OUT 2.5mm",
         fields={"Op_I": 1.65, "Rated_I": 5.0, "Note": "2.5 mm pin so a 2.0 mm input plug can't mate"})
    D.TP(sh, "VDCOUT")
    return sh

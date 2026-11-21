"""DC barrel output 12-24 V (app-selected, default OFF): BQ25756 in reverse mode regulating VDCOUT_RAW
(VAC_REV, 20 mV steps), then TPS26631 eFuse (I_LIM 1.65 A = 3:1 on the 5 A jack) and an LM74700
ideal diode so nothing plugged into the jack can back-feed the converter.
CE is pulled HIGH in hardware: this stage never charges (forward mode disabled); firmware sets EN_REV.
"""
from blocks.power_input import bq_stage, efuse, ideal_diode


def build(D):
    sh = D.sheet("dc_output", "DC barrel output 12-24 V, 40 W max, default off")
    sh.note("Output voltage set by BQ25756 VAC_REV over I2C (mux ch5). Power-up state: EN_REV=0 -> output off.")
    sh.note("Glow LEDs show the selected voltage; the app requires an explicit confirm before enabling.")
    bq_stage(D, sh, "DCO", "VDCOUT_RAW", 5, ichg_r="10k", ilim_r="10k", ce_net="DCO_CE",
             note="Reverse-only stage (CE high blocks charging). IAC_REV limit set <= 1.8 A by firmware.", irms=2.9)
    D.R(sh, "10k", "DCO_CE", "V3V3", fields={"Note": "charging disabled in hardware"})
    D.TP(sh, "DCO_CE", small=True)
    D.TP(sh, "VDCOUT_RAW")
    efuse(D, sh, "VDCOUT_RAW", "DCO_EF", "DCOF", note="IN_SYS fed from the converter side")
    D.JP(sh, "VDCOUT_RAW", "DCOF_INSYS", i_op=1.65, note="DC-out isolate")
    D.v("DCO_EF", 24.0)
    ideal_diode(D, sh, "DCO_EF", "VDCOUT", "DCO_ORING")
    D.IC(sh, "SMBJ33A", {"K": "VDCOUT", "A": "GND"}, prefix="D")
    D.C(sh, "C_10u_50V", "VDCOUT", "GND")
    D.IC(sh, "DC-005-5A-2.5", {"1": "VDCOUT", "2": "GND", "3": "GND"}, prefix="J", value="DC OUT 2.5mm",
         fields={"Op_I": 1.65, "Rated_I": 5.0, "Note": "2.5 mm pin so a 2.0 mm input plug can't mate"})
    D.TP(sh, "VDCOUT")
    return sh

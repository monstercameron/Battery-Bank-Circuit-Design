"""Main-board side of the swappable cartridge: XT60 power, 4 pogo signal pads, bus bulk + TVS.
Protection (BQ77915), fuse and gauge (BQ34Z100) live in the cartridge PCB (separate project, cartridge.py).

TVS coordination (P-24 / X-3, this wave):
  SMBJ24A: standoff 24 V >= 21.0 x 1.1 = 23.1 V; V_BR 26.7-29.5 V; clamp 38.9 V at I_pp (series data, VERIFY part sheet).
  No TVS meets both the 23.1 V standoff and a clamp below the TPS62933's 32 V VIN abs max (TPS62933 DS 8.1), so the
  32 V parts are NOT protected by this clamp directly. Instead (aux_power.py) every VBAT-fed TPS62933 / TPS56A37 sits
  behind a TPS26631 with OV cut-off at 23.5 V nominal (22.8-24.2 V; TPS2663 DS: V(OVPR) 1.176-1.224 V, OVP turn-off
  8.5-14 us). At the worst bus slew this board can produce (all chargers dumping ~30 A into ~160 uF when a cartridge is
  pulled: 0.19 V/us) the sub-bus overshoots by < 3 V during the 14 us turn-off -> < 27 V at the bucks.
  The chargers themselves stop at BATOVP = 104 % (102.5-105.5 %) of VFB_REG -> 21.8 V max (BQ25756 DS).
  Bus-connected parts left directly on VBAT and their ratings vs the 38.9 V clamp:
    IP6525S (USB-A): DC withstand 40 V, input OVP 32.6 V (IP6525S DS) -> OK.  AL8860 (lighting): 40 V -> OK.
    BQ25756 SRP/SRN/FB divider: high-voltage pins -> OK.  TPS62933P NIC bucks in usbc_port.py: NOT OK -> move to an
    OV-protected sub-bus (see aux_power.py VPROT_B) - owned by the usbc_port block.
Open for the next wave (battery-to-bus architecture, X-3 / P-25 / P-26): insertion precharge / hot-swap / voltage match,
reverse-insertion protection, main-board fuse with >= 3x interrupt rating (no stocked >= 1 kA SMD fuse or MINI-blade
holder on JLC today: 0297015.WXNV 1 kA@32 V exists, holders 3568 are out of stock).
"""


def build(D):
    sh = D.sheet("battery", "Battery cartridge interface + VBAT bus")
    sh.note("Cartridge: 5S1P Samsung 50S, 90 Wh. 3:1 on cell current -> 8.3 A max; firmware limit 8.0 A; BQ77915 OCD backs it up.")
    sh.note("Cartridge PCB (separate KiCad project): BQ7791500 protector + CHG/DSG FETs, BQ34Z100-G1 gauge, fuse, NTCs.")
    sh.note("X-3 (open, next wave): insertion connects the pack straight onto ~160 uF of VBAT bulk with no precharge or voltage match.")
    sh.note("TVS: SMBJ24A clamp (38.9 V) > TPS62933 32 V abs max -> the 32 V bucks are behind OV-cutoff eFuses (aux_power VPROT_A/B).")
    D.IC(sh, "XT60PW-M", {"+": "VBAT", "-": "GND"}, nc=["3", "4"], prefix="J", value="XT60 cartridge",
         fields={"Op_I": 8.3, "Rated_I": 30.0, "Note": "Rated_I 30 A (distributor data, VERIFY). 3.6:1"})
    D.generic(sh, "TP", "POGO GND", "TestPoint:TestPoint_Pad_D2.0mm", {"1": "GND"}, prefix="P",
              fields={"Note": "pogo contact pad (cartridge springs)", "_nobom": True})
    D.generic(sh, "TP", "POGO SDA", "TestPoint:TestPoint_Pad_D2.0mm", {"1": "I2C7_SDA"}, prefix="P", fields={"_nobom": True})
    D.generic(sh, "TP", "POGO SCL", "TestPoint:TestPoint_Pad_D2.0mm", {"1": "I2C7_SCL"}, prefix="P", fields={"_nobom": True})
    D.generic(sh, "TP", "POGO PRES_A", "TestPoint:TestPoint_Pad_D2.0mm", {"1": "CART_PRES_LOOP"}, prefix="P", fields={"_nobom": True})
    D.generic(sh, "TP", "POGO PRES_B", "TestPoint:TestPoint_Pad_D2.0mm", {"1": "CART_PRES_LOOP"}, prefix="P",
              fields={"_nobom": True, "Note": "PRES_A-PRES_B shorted here: wakes the cartridge protector only when seated"})
    D.v("CART_PRES_LOOP", 21.0)
    D.IC(sh, "SMBJ24A-C87268", {"C": "VBAT", "A": "GND"}, prefix="D",
         fields={"Note": "bus TVS: standoff 24 V >= 21 x 1.1. Clamp 38.9 V protects >= 40 V parts only; 32 V bucks are behind "
                         "OV-cutoff eFuses (aux_power). Reverse insertion forward-biases it (X-3, open)."})
    for _ in range(4):
        D.C(sh, "C_10u_50V", "VBAT", "GND")
    D.C(sh, "C_100n_50V", "VBAT", "GND")
    D.TP(sh, "VBAT")
    D.TP(sh, "GND")
    D.TP(sh, "GND")
    return sh

"""Main-board side of the swappable cartridge: XT60 power, 4 pogo signal pads, bus bulk + TVS.
Protection (BQ77915), fuse and gauge (BQ34Z100) live in the cartridge PCB (separate project, TODO).
"""


def build(D):
    sh = D.sheet("battery", "Battery cartridge interface + VBAT bus")
    sh.note("Cartridge: 5S1P Samsung 50S, 90 Wh. 3:1 on cell current -> 8.3 A max; firmware limit 8.0 A; BQ77915 OCD backs it up.")
    sh.note("Cartridge PCB (separate KiCad project): BQ7791500 protector + CHG/DSG FETs, BQ34Z100-G1 gauge, fuse, NTCs.")
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
    D.IC(sh, "SMBJ24A-C87268", {"C": "VBAT", "A": "GND"}, prefix="D", fields={"Note": "bus TVS: standoff 24 V >= 21 x 1.1"})
    for _ in range(4):
        D.C(sh, "C_10u_50V", "VBAT", "GND")
    D.C(sh, "C_100n_50V", "VBAT", "GND")
    D.TP(sh, "VBAT")
    D.TP(sh, "GND")
    D.TP(sh, "GND")
    return sh

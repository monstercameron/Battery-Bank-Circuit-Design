"""Review round 1 - H-3 / C-4: board partition.
Board A (power, z=28): USB-C stages + NICs + RTL8372N switch, inputs, DC out, aux rails, USB-A, MCU, flashlight driver.
Board B (logic, z=48): RTL8221B PHY + RJ45 + PoE, router module, LoRa, audio, Qi, glow strip.
Only 4 SerDes pairs cross (switch S0 <-> router, S1 <-> PHY) on a high-speed mezzanine; low-speed + power on a 2.54 mm header.
SerDes AC-coupling caps sit next to each transmitter (RTL8221B DS 6.3), i.e. switch-TX caps on A, PHY/router-TX caps on B."""
import os

GEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "gen")


def sub(rel, old, new):
    path = os.path.join(GEN, rel)
    t = open(path, encoding="utf-8").read()
    assert old in t, (rel, old[:90])
    open(path, "w", encoding="utf-8").write(t.replace(old, new, 1))


E = "blocks/ethernet.py"
sub(E, '''    sh = D.sheet("ethernet", "2.5G switch RTL8372N + RTL8221B (RJ45 PHY) + router module")''',
    '''    sh = D.sheet("eth_switch", "2.5G switch RTL8372N + SPI flash (board A, beside the 4 NICs)", board="A")''')
sub(E, '''    # RTL8221B PHY for the RJ45''', '''    shA = sh
    sh = D.sheet("eth_phy_router", "RTL8221B PHY + RJ45 side + router module (board B)", board="B")
    sh.note("Board B: receives the switch SerDes S0/S1 over the high-speed mezzanine. PHY analog rails filtered locally.")
    D.v("V3V3_PHYA", 3.6)
    D.jlc_generic(sh, "FB", "FB_3A_0603", {"1": V33, "2": "V3V3_PHYA"}, prefix="FB", value="FB 100R 3A",
                  footprint="Inductor_SMD:L_0603_1608Metric", fields={"Op_I": 0.2, "Rated_I": 3.0})
    D.C(sh, "C_10u_16V", "V3V3_PHYA", G)
    # RTL8221B core: TPS62933F FCCM 1.2 MHz from V5_ETH (H-10), local to the PHY on board B
    D.v("V0V95_PHY_SW", 5.5)
    D.IC(sh, "TPS62933FDRLR", {"RT": "GND", "EN": "EXP_EN_ETH", "VIN": "V5_ETH", "GND": "GND", "SW": "V0V95_PHY_SW",
                               "BST": "V09PHY_BST", "SS": "V09PHY_SS", "FB": "V09PHY_FB"},
         fields={"Op_I": 0.5, "Rated_I": 3.0, "Note": "RTL8221B 0.95 V (DVDD09/AVDD09/EVDD09), <= 15 mVpp, PWM > 1 MHz"})
    D.C(sh, "C_33n_50V", "V09PHY_SS", "GND")
    D.C(sh, "C_100n_16V", "V09PHY_BST", "V0V95_PHY_SW", fields={"V_across": 5.5})
    D.L(sh, "FNR6045S2R2MT", "V0V95_PHY_SW", "V0V95_PHY", rated_i=5.0, isat=7.4, irms=0.5, ipk=0.7, value="2.2uH 5A")
    D.R(sh, "1.87k", "V0V95_PHY", "V09PHY_FB", fields={"Note": "0.950 V"})
    D.R(sh, "10k", "V09PHY_FB", "GND")
    D.C(sh, "C_10u_16V", "V5_ETH", "GND")
    D.C(sh, "C_22u_6V3", "V0V95_PHY", "GND")
    D.C(sh, "C_22u_6V3", "V0V95_PHY", "GND")
    D.TP(sh, "V0V95_PHY")

    # RTL8221B PHY for the RJ45''')
sub(E, '''"AVDD33": "V3V3_ETHA", "AVDD33_XTAL": "V3V3_ETHA", "CKXTAL2": "ETH_PHY_XO",''',
    '''"AVDD33": "V3V3_PHYA", "AVDD33_XTAL": "V3V3_PHYA", "CKXTAL2": "ETH_PHY_XO",''')
sub(E, '''    for _ in range(5):
        D.C(sh, "C_100n_16V", "V3V3_ETHA", G)
    # SerDes S1 <-> PHY: 100 nF both directions
    for a, b in [("ETH_S1TXP", "ETH_PHY_HSIP"), ("ETH_S1TXN", "ETH_PHY_HSIN"), ("ETH_PHY_HSOP", "ETH_S1RXP"), ("ETH_PHY_HSON", "ETH_S1RXN")]:
        D.C(sh, "C_100n_16V", a, b, fields={"Note": "SerDes AC coupling"})
    # SerDes S0 -> router (switch TX caps here; router module carries caps on its own TX)
    D.C(sh, "C_100n_16V", "ETH_S0TXP", "RTR_RXP")
    D.C(sh, "C_100n_16V", "ETH_S0TXN", "RTR_RXN")
    D.C(sh, "C_100n_16V", "RTR_TXP", "ETH_S0RXP", fields={"Note": "router->switch AC coupling (module caps unverified; 2 in series = 50 nF OK)"})
    D.C(sh, "C_100n_16V", "RTR_TXN", "ETH_S0RXN")''',
    '''    for _ in range(5):
        D.C(sh, "C_100n_16V", "V3V3_PHYA", G)
    # SerDes AC coupling next to each TRANSMITTER: switch TX caps on board A, PHY/router TX caps on board B
    for a, b in [("ETH_S1TXP", "ETH_PHY_HSIP"), ("ETH_S1TXN", "ETH_PHY_HSIN"), ("ETH_S0TXP", "RTR_RXP"), ("ETH_S0TXN", "RTR_RXN")]:
        D.C(shA, "C_100n_16V", a, b, fields={"Note": "SerDes AC coupling at the switch transmitter (board A)"})
    for a, b in [("ETH_PHY_HSOP", "ETH_S1RXP"), ("ETH_PHY_HSON", "ETH_S1RXN"), ("RTR_TXP", "ETH_S0RXP"), ("RTR_TXN", "ETH_S0RXN")]:
        D.C(sh, "C_100n_16V", a, b, fields={"Note": "SerDes AC coupling at the PHY/router transmitter (board B)"})''')
sub(E, '''    D.IC(sh, "TS-1187A-B-A-B", {"A": "RTR_BOOT", "B": "RTR_BOOT", "C": G, "D": G}, prefix="SW", value="ROUTER RECOVERY")''',
    '''    D.IC(sh, "TS-1187A-B-A-B", {"A": "RTR_BOOT", "D": G}, nc=["B", "C"], prefix="SW", value="ROUTER RECOVERY")''')

# remove the PHY buck from aux_power (now local on board B)
A = "blocks/aux_power.py"
path = os.path.join(GEN, A)
t = open(path, encoding="utf-8").read()
s = t.index("    # RTL8221B core: TPS62933F FCCM 1.2 MHz from V5_ETH")
e = t.index("    # load switches")
t = t[:s] + t[e:]
open(path, "w", encoding="utf-8").write(t)

# glow strip -> its own sheet on board B; LED-board parts labelled Board "LED"
L = "blocks/lighting.py"
sub(L, '''    # glow strip: 8x SK6812MINI-E chained''', '''    # glow strip: 8x SK6812MINI-E chained, on board B along the front-top edge light pipe
    sh = D.sheet("glow", "Attention-glow strip: 8x SK6812MINI-E (board B, front-top light pipe)", board="B")''')
t = open(os.path.join(GEN, L), encoding="utf-8").read()
t = t.replace('"Board": "LED (aluminium core)"', '"Board": "LED"')
open(os.path.join(GEN, L), "w", encoding="utf-8").write(t)
# mating harness connector on the LED board
sub(L, '''    D.IC(sh, "XPGDWT-01-0000-00ME2",''', '''    D.CONN(sh, "LED_BOARD_HDR", ["LED_A", "LED_K", "RED_A", "RED_K", "NTC", "GND"],
           {"LED_A": "LED_RS", "LED_K": "LED_K", "RED_A": "LED_RED_A", "RED_K": "LED_RED_K", "NTC": "LED_NTC", "GND": G},
           footprint="Connector_JST:JST_PH_B6B-PH-K_1x06_P2.00mm_Vertical", prefix="J",
           fields={"LCSC": "C131342", "MPN": "B6B-PH-K-S(LF)(SN)", "Board": "LED", "B2B": True, "Op_I": 0.5, "Rated_I": 2.0,
                   "Note": "LED-board end of the 6-wire harness"})
    D.IC(sh, "XPGDWT-01-0000-00ME2",''')
sub(L, '''           fields={"LCSC": "C131342", "MPN": "B6B-PH-K-S(LF)(SN)", "Op_I": 0.5, "Rated_I": 2.0,
                   "Note": "JST PH 6-pin harness to the aluminium LED board (2 A contacts -> 4:1)"})''',
    '''           fields={"LCSC": "C131342", "MPN": "B6B-PH-K-S(LF)(SN)", "B2B": True, "Op_I": 0.5, "Rated_I": 2.0,
                   "Note": "JST PH 6-pin harness to the aluminium LED board (2 A contacts -> 4:1)"})''')
print("partition patch applied")

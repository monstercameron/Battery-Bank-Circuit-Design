"""2.5G switch (RTL8372N, integrated 4x 2.5GBASE-T PHYs) + RTL8221B PHY for the RJ45 + router module (Acelink SM81).
Switch on board A, PHY/router on board B.

RTL8372N (datasheet Rev 0.3): 0.95 V core + 3.3 V; 25 MHz +-50 ppm; RSET 2.49k 1 %; RSV_TEST0 4.7k to GND;
  INI_MODE default 11 (internal pull-ups) = CPU boots from SPI flash; SerDes 100 nF AC coupling.
  Table 40: t5 reset delay >= 10.5 ms from 'all power steady'; t6 reset low time >= 10.5 ms.
RTL8221B (Rev 1.2): SerDes HiSGMII/2500BASE-X, 0.1 uF AC caps both directions; MDIO pull-up 1.5k; PHYRSTB >= 10 ms
  after all rails valid (power-on timing; the extracted text in docs/ is TOC-only, value per review X-29 / H-20).

X-29 reset supervision (per reset domain, open-drain wired-AND on the reset net):
  TPS3808G33 (fixed 3.07 V, SENSE = the domain's 3.3 V after its isolation jumper, MR = expander reset request)
  + TPS3808G01 (SENSE = 0.95 V core through 11k/10k -> 0.405 V x 2.1 = 0.851 V falling threshold).
  Both run from always-on V3V3, so RESET is defined (low) whenever the monitored rails are off.
  Release = max(t_3V3_valid, t_0V95_valid) + tD, i.e. tD after the LAST rail is valid; any MR pulse also gives >= tD low.
  TPS3808 DS eq. 1: CT(nF) = (tD(s) - 0.5 ms) x 175  ->  CT = 22 nF: tD = 22/175 + 0.5 ms = 126 ms typ.
  Spread: DS switching table 130 pF -> 0.75/1.25/1.75 ms and 180 nF -> 0.62/1.03/1.44 s (+-40 %), CT X7R +-10 %:
  tD(min) = 126 x 0.60 x 0.90 = 68 ms >= 6.5 x 10.5 ms;  tD(max) = 126 x 1.40 x 1.10 = 194 ms (boot latency only).
  0.95 V threshold: VIT +-2 % (G01, full temp) and 1 % divider -> 0.829-0.872 V falling, <= 0.898 V rising (3 % max hyst),
  below the 0.935 V worst-case rail (0.95 V -1.5 %) and above 85 % of nominal.
  3.3 V threshold: 3.07 V +-1.5 % -> 3.02-3.12 V falling, <= 3.19 V rising, below the 3.26 V worst-case V3V3_ETH.
"""

ROUTER_PINS = (["VCC_3V3"] * 10 + ["GND"] * 12 +
               ["HSGMII_TXP", "HSGMII_TXN", "HSGMII_RXP", "HSGMII_RXN", "SMI_MDC", "SMI_MDIO", "GPIO_SW_INT",
                "UART0_TXD", "UART0_RXD", "SYS_RST_N", "WPS_RECOVERY", "LED_STATUS"])


def reset_supervisor(D, sh, v33_sense, core_sense, rst, exp_req, pullup_rail, tag):
    """X-29: open-drain wired-AND reset = (3.3 V ok) AND (0.95 V core ok) AND (expander released), each delayed >= tD."""
    G = "GND"
    D.IC(sh, "TPS3808G33DBVR", {"VDD": "V3V3", "GND": G, "SENSE": v33_sense, "~{MR}": exp_req, "CT": f"{tag}_CT33",
                                "~{RESET}": rst},
         fields={"Note": f"X-29: {v33_sense} >= 3.07 V and {exp_req} high, then tD (CT 22 nF: 126 ms typ, 68 ms min). "
                         "VDD on always-on V3V3 so RESET stays low while the domain is off."})
    D.C(sh, "C_22n_50V", f"{tag}_CT33", G, fields={"Note": "tD = 22/175 + 0.5 ms = 126 ms typ (TPS3808 eq. 1)"})
    D.C(sh, "C_100n_16V", "V3V3", G)
    D.IC(sh, "TPS3808G01DBVT", {"VDD": "V3V3", "GND": G, "SENSE": f"{tag}_SNS09", "CT": f"{tag}_CT09", "~{RESET}": rst},
         nc=["~{MR}"],
         fields={"Note": f"X-29: {core_sense} via 11k/10k -> 0.851 V falling threshold; MR unused (internal 90k pull-up)."})
    D.R(sh, "11k", core_sense, f"{tag}_SNS09", fields={"Note": "0.405 V x (1 + 11k/10k) = 0.851 V"})
    D.R(sh, "10k", f"{tag}_SNS09", G)
    D.C(sh, "C_1n_50V", f"{tag}_SNS09", G, fields={"Note": "SENSE bypass 1-10 nF (TPS3808 DS 7.3.1)"})
    D.C(sh, "C_22n_50V", f"{tag}_CT09", G)
    D.C(sh, "C_100n_16V", "V3V3", G)
    D.R(sh, "10k", rst, pullup_rail, fields={"Note": "reset pull-up in the target's own I/O domain (open-drain wired-AND)"})
    D.R(sh, "22k", exp_req, G, fields={"Note": "expander input at power-up: 22k vs MR internal 70-90k -> <= 0.79 V < 0.3 VDD, "
                                                "so the reset is HELD until firmware drives the expander pin high"})
    D.TP(sh, rst, small=True)
    D.TP(sh, exp_req, small=True)
    D.TP(sh, "GND", small=True)


def build(D):
    G = "GND"
    sh = D.sheet("eth_switch", "2.5G switch RTL8372N + SPI flash (board A, beside the 4 NICs)", board="A")
    sh.note("Switch ports P0-P3 = USB-C ports 1-4 (PHY-to-PHY to each RTL8156BG). S0 -> router SerDes (LAN). S1 -> RTL8221B -> RJ45 (WAN, PoE in).")
    sh.note("Management: the router owns the switch (DSA) over SMDC/SMDIO (through the router-domain isolation FETs on board B); "
            "switch MDC0/MDIO0 manages the RTL8221B. SDK firmware in SPI flash.")
    sh.note("X-29 reset: ETH_SW_RST_N = TPS3808G33(V3V3_SW, MR=EXP_SW_RST_N) AND TPS3808G01(V0V95_SWA). Release 126 ms typ / "
            "68 ms min after the LAST rail is valid (needs >= 10.5 ms). Expander-initiated resets are also stretched to >= 68 ms (t6 >= 10.5 ms).")
    sh.note("X-28 first boot: OPEN - the RTL8372N image is the Realtek SDK build (NDA). No image is in this repository and no "
            "blank-flash host-init mode is verified. Bring-up: EXP_EN_ETH=1, EXP_SW_RST_N=0 (or hold J pin 7 low), program U(flash) "
            "through the 2x4 ISP header, read back, then release reset.")
    # C-17 / X-42 isolation links: switch I/O + flash and switch core behind copper jumpers (layout: >= 3x current width)
    V33, V09 = "V3V3_SW", "V0V95_SWD"
    D.v(V33, 3.6)
    D.v(V09, 1.0)
    D.v("V0V95_SWA", 1.0)
    D.v("V3V3_ETHA", 3.6)
    D.JP(sh, "V3V3_ETH", V33, i_op=0.5, note="ISO 3V3 switch")
    D.JP(sh, "V0V95_SW", V09, i_op=2.5, note="ISO 0V95 switch core (7.5 A copper)")
    D.TP(sh, V33)
    D.TP(sh, V09)
    D.TP(sh, "V0V95_SWA", small=True)
    D.TP(sh, "V3V3_ETHA", small=True)
    D.TP(sh, "GND")
    mdi = {}
    for p in range(4):
        for pair in "ABCD":
            for pol in "PN":
                mdi[f"P{p}MDI{pair}{pol}"] = f"SW_P{p}MDI{pair}{pol}"
    D.IC(sh, "RTL8372N-CG", {
        **mdi, "DVDDL": V09, "AVDDL_P0": "V0V95_SWA", "AVDDL_P1": "V0V95_SWA", "AVDDL_P2": "V0V95_SWA", "AVDDL_P3": "V0V95_SWA",
        "AVDDL_1GXG": "V0V95_SWA", "AVDDLC": "V0V95_SWA", "SVDDL_CMU0": "V0V95_SWA", "SVDDL_CMU1": "V0V95_SWA",
        "SVDDL_TRX0": "V0V95_SWA", "SVDDL_TRX1": "V0V95_SWA",
        "AVDD33": "V3V3_ETHA", "AVDDHC": "V3V3_ETHA", "DVDDIO5": V33, "DVDDIO0": V33,
        "SPF_SCK": "ETH_SPF_SCK_SW", "SPF_SDI": "ETH_SPF_MOSI_SW", "SPF_SDO": "ETH_SPF_MISO_SW", "SPF_CSN": "ETH_SPF_CS_SW",
        "RSET": "ETH_SW_RSET", "XI": "ETH_SW_XI", "XO": "ETH_SW_XO", "RSV_TEST0": "ETH_SW_TEST0",
        "LED_9/STR_REG_IF_SEL_1": "ETH_STR_IF1", "LED_12/STR_REG_IF_SEL_0": "ETH_STR_IF0", "LED_18/STR_EN_PHY": "ETH_STR_ENPHY", "SEL_XTAL": "ETH_SW_SELX",
        "nReset": "ETH_SW_RST_N", "INT": "ETH_SW_INT", "GPIO31/U0TXD": "ETH_SW_TXD", "GPIO32/U0RXD": "ETH_SW_RXD",
        "MDIO0": "ETH_MDIO", "MDC0": "ETH_MDC", "SSDI/SSDA/SMDIO/EE_SDA": "ETH_SW_SMDIO", "SSCK/SSCL/SMDC/EE_SCL": "ETH_SW_SMDC",
        "S0TXP": "ETH_S0TXP", "S0TXN": "ETH_S0TXN", "S0RXP": "ETH_S0RXP", "S0RXN": "ETH_S0RXN",
        "S1TXP": "ETH_S1TXP", "S1TXN": "ETH_S1TXN", "S1RXP": "ETH_S1RXP", "S1RXN": "ETH_S1RXN", "EP": G},
        nc=["GLB_RLDP_LED", "GPIO30", "LED_0/STR_INI_MODE_1", "LED_2", "LED_1", "LED_3/STR_INI_MODE_0", "LED_4", "LED_5", "LED_6",
            "LED_8", "LED_15/STR_EN_PHY_R_FRC", "LED_10", "LED_21/STR_EN_SLV_MDC_DEG", "NC", "SYNCE_CLK_OUT_1", "LED_27/STR_EEPROM_MOD", "LED_26/STR_EN_PLED",
            "LED_25", "LED_24/STR_POB_EN", "GPIO37", "GPIO38", "MSDA4/GPIO39", "MSCK3/MDC1", "MSDA3/MDIO1", "PTP_SYNC",
            "SCSN", "SSDO", "MSCL0/MSCK", "MSCL1/MOSI", "MSDA0/MISO", "MSDA1/MCSN", "SYS_LED/STR_SYS_LED_EN"],
        fields={"Note": "Straps left at internal defaults (INI_MODE=11 boot from SPI flash). REG_IF_SEL straps decide SMI/I2C/SPI slave - VERIFY for router DSA."})
    # supplies: analog rails through ferrite beads
    D.jlc_generic(sh, "FB", "FB_3A_0603", {"1": V09, "2": "V0V95_SWA"}, prefix="FB", value="FB 100R 3A",
                  footprint="Inductor_SMD:L_0603_1608Metric", fields={"Op_I": 0.8, "Rated_I": 3.0})
    D.jlc_generic(sh, "FB", "FB_3A_0603", {"1": V33, "2": "V3V3_ETHA"}, prefix="FB", value="FB 100R 3A",
                  footprint="Inductor_SMD:L_0603_1608Metric", fields={"Op_I": 0.5, "Rated_I": 3.0})
    for _ in range(12):
        D.C(sh, "C_100n_16V", V09, G)
    for _ in range(8):
        D.C(sh, "C_100n_16V", "V0V95_SWA", G)
    for _ in range(3):
        D.C(sh, "C_22u_6V3", V09, G)
    D.C(sh, "C_22u_6V3", "V0V95_SWA", G)
    for _ in range(6):
        D.C(sh, "C_100n_16V", "V3V3_ETHA", G)
    for _ in range(4):
        D.C(sh, "C_100n_16V", V33, G)
    D.C(sh, "C_10u_16V", "V3V3_ETHA", G)
    D.C(sh, "C_10u_16V", V33, G)
    D.R(sh, "2.49k", "ETH_SW_RSET", G)
    D.R(sh, "4.7k", "ETH_STR_IF1", V33, fields={"Note": "REG_IF_SEL=11: slave MDC/MDIO, PHY ID 29 (DS Table 10). Confirm with router DSA driver"})
    D.R(sh, "4.7k", "ETH_STR_IF0", V33)
    D.R(sh, "4.7k", "ETH_STR_ENPHY", V33, fields={"Note": "EN_PHY=1: enable the 4 embedded 2.5G PHYs (default pull-down disables them)"})
    D.TP(sh, "ETH_SW_SELX", small=True)
    D.R(sh, "4.7k", "ETH_SW_TEST0", G, fields={"Note": "RSV_TEST0 must be pulled low (4.7k)"})
    D.IC(sh, "NX3225SA-25MHZ-STD-CSR-6", {"1": "ETH_SW_XI", "3": "ETH_SW_XO", "GND": G}, prefix="Y", value="25MHz 10pF")
    D.C(sh, "C_12p_50V", "ETH_SW_XI", G)
    D.C(sh, "C_12p_50V", "ETH_SW_XO", G)
    # X-29: supervised reset (replaces the 10k/2.2 uF RC that started timing from the 3.3 V rise)
    reset_supervisor(D, sh, V33, "V0V95_SWA", "ETH_SW_RST_N", "EXP_SW_RST_N", V33, "ETH_SWR")
    # management lines, switch side (router side + isolation FETs on board B)
    D.R(sh, "2.2k", "ETH_SW_SMDC", V33, fields={"Note": "H-23: 2.2k switch-side pull-up (FET level-shifter topology needs it for the MDC rise)"})
    D.R(sh, "2.2k", "ETH_SW_SMDIO", V33)
    D.R(sh, "10k", "ETH_SW_INT", V33)
    D.TP(sh, "ETH_SW_INT", small=True)
    D.TP(sh, "ETH_SW_SMDC", small=True)
    D.TP(sh, "ETH_SW_SMDIO", small=True)
    D.TP(sh, "ETH_SW_TXD", small=True)
    D.TP(sh, "ETH_SW_RXD", small=True)
    # X-28 SPI flash + ISP: 100R bus-ownership resistors between the switch and the flash/header node
    for sw_net, fl_net in (("ETH_SPF_SCK_SW", "ETH_SPF_SCK"), ("ETH_SPF_MOSI_SW", "ETH_SPF_MOSI"),
                           ("ETH_SPF_CS_SW", "ETH_SPF_CS"), ("ETH_SPF_MISO_SW", "ETH_SPF_MISO")):
        D.R(sh, "100", sw_net, fl_net, fields={"Note": "X-28 ISP bus ownership: limits switch-vs-programmer contention to < 25 mA if "
                                                       "the RTL8372N SPF pins are not Hi-Z in reset (unverified)"})
    D.IC(sh, "W25Q32JVZPIQ", {"/CS": "ETH_SPF_CS", "DO(IO1)": "ETH_SPF_MISO", "/WP(IO2)": "ETH_SPF_WP", "GND": G,
                               "DI(IO0)": "ETH_SPF_MOSI", "CLK": "ETH_SPF_SCK", "/HOLDor/RESET(IO3)": "ETH_SPF_HOLD", "VCC": V33, "EP": G},
         fields={"Note": "RTL8372N SDK firmware (Realtek, under NDA) - image source OPEN. Programmed in-circuit through the 2x4 ISP header."})
    D.R(sh, "10k", "ETH_SPF_WP", V33)
    D.R(sh, "10k", "ETH_SPF_HOLD", V33)
    D.R(sh, "10k", "ETH_SPF_CS", V33)
    D.C(sh, "C_100n_16V", V33, G)
    D.R(sh, "100", "ETH_ISP_VREF", V33, fields={"Note": "C-28: VREF is a sense pin only (100R); the programmer must not power V3V3_SW"})
    D.CONN(sh, "ISP_SW_FLASH_2x4", ["VREF", "GND", "CS", "CLK", "MOSI", "MISO", "SW_RST_N", "GND"],
           {"VREF": "ETH_ISP_VREF", "GND": G, "CS": "ETH_SPF_CS", "CLK": "ETH_SPF_SCK", "MOSI": "ETH_SPF_MOSI", "MISO": "ETH_SPF_MISO",
            "SW_RST_N": "ETH_SW_RST_N"},
           footprint="Connector_PinHeader_1.27mm:PinHeader_2x04_P1.27mm_Vertical", fields={"_nobom": True, "Note":
           "X-28 ISP: 1 VREF 2 GND 3 CS 4 CLK 5 DI 6 DO 7 SW_RST_N (open-drain node: programmer pulls low to own the bus) 8 GND"},
           prefix="J", dnp=True)

    # X-30 interlock: the router rail may only be enabled while V3V3_ETH is valid (router MDC/MDIO/SerDes face the switch).
    D.IC(sh, "TPS3808G33DBVR", {"VDD": "V3V3", "GND": G, "SENSE": "V3V3_ETH", "~{RESET}": "EXP_EN_RTR"}, nc=["~{MR}", "CT"],
         fields={"Note": "X-30 interlock: open-drain on the V3V3_RTR enable. Holds EXP_EN_RTR low while V3V3_ETH < 3.07 V and for "
                         "20 ms (12-28 ms, CT open) after it is valid. Expander drives EXP_EN_RTR_REQ through 10k."})
    D.C(sh, "C_100n_16V", "V3V3", G)
    D.TP(sh, "EXP_EN_RTR", small=True)

    shA = sh
    sh = D.sheet("eth_phy_router", "RTL8221B PHY + RJ45 side + router module (board B)", board="B")
    sh.note("Board B: receives the switch SerDes S0/S1 over the high-speed mezzanine. PHY analog rails filtered locally.")
    sh.note("X-29 reset: ETH_PHY_RST_N = TPS3808G33(V3V3_PHY, MR=EXP_PHY_RST_N) AND TPS3808G01(V0V95_PHY); 126 ms typ / 68 ms min "
            "after the LAST rail is valid (needs >= 10 ms).")
    sh.note("X-30 router domain V3V3_RTR_M: every pull-up the module sees (reset, recovery, MDC/MDIO, SW_INT) is on V3V3_RTR_M. "
            "MDC/MDIO/SW_INT cross to the switch through 2N7002 pass FETs (gate = V3V3_RTR_M): router off -> FETs off, the body "
            "diodes are reverse-biased by the switch-side pull-ups, nothing reaches the dead module. Router on with ETH off is "
            "prevented in hardware (TPS3808 interlock on EXP_EN_RTR, board A). SerDes are AC-coupled.")
    V33P = "V3V3_PHY"
    D.v(V33P, 3.6)
    D.v("V3V3_PHYA", 3.6)
    D.v("V5_PHYBUCK", 5.5)
    D.JP(sh, "V3V3_ETH", V33P, i_op=0.2, note="ISO 3V3 PHY")
    D.JP(sh, "V5_ETH", "V5_PHYBUCK", i_op=0.15, note="ISO 5V PHY buck")
    D.TP(sh, V33P)
    D.TP(sh, "GND")
    D.jlc_generic(sh, "FB", "FB_3A_0603", {"1": V33P, "2": "V3V3_PHYA"}, prefix="FB", value="FB 100R 3A",
                  footprint="Inductor_SMD:L_0603_1608Metric", fields={"Op_I": 0.2, "Rated_I": 3.0})
    D.C(sh, "C_10u_16V", "V3V3_PHYA", G)
    # RTL8221B core: TPS62933F FCCM 1.2 MHz from V5_ETH (H-10), local to the PHY on board B
    D.v("V0V95_PHY_SW", 5.5)
    D.IC(sh, "TPS62933FDRLR", {"RT": "GND", "EN": "EXP_EN_ETH", "VIN": "V5_PHYBUCK", "GND": "GND", "SW": "V0V95_PHY_SW",
                               "BST": "V09PHY_BST", "SS": "V09PHY_SS", "FB": "V09PHY_FB"},
         fields={"Op_I": 0.5, "Rated_I": 3.0, "Note": "RTL8221B 0.95 V (DVDD09/AVDD09/EVDD09), <= 15 mVpp, PWM > 1 MHz"})
    D.C(sh, "C_33n_50V", "V09PHY_SS", "GND")
    D.C(sh, "C_100n_16V", "V09PHY_BST", "V0V95_PHY_SW", fields={"V_across": 5.5})
    D.L(sh, "FNR6045S2R2MT", "V0V95_PHY_SW", "V0V95_PHY", rated_i=5.0, isat=7.4, irms=0.5, ipk=0.7, value="2.2uH 5A")
    D.R(sh, "1.87k", "V0V95_PHY", "V09PHY_FB", fields={"Note": "0.950 V"})
    D.R(sh, "10k", "V09PHY_FB", "GND")
    D.C(sh, "C_10u_16V", "V5_PHYBUCK", "GND")
    D.C(sh, "C_22u_6V3", "V0V95_PHY", "GND")
    D.C(sh, "C_22u_6V3", "V0V95_PHY", "GND")
    D.TP(sh, "V0V95_PHY")

    # RTL8221B PHY for the RJ45
    D.IC(sh, "RTL8221B-VB-CG", {
        "PHYRSTB": "ETH_PHY_RST_N", "MDC": "ETH_MDC", "MDIO": "ETH_MDIO", "DVDD09": "V0V95_PHY", "DVDD3318": V33P,
        "AVDD33": "V3V3_PHYA", "AVDD33_XTAL": "V3V3_PHYA", "CKXTAL2": "ETH_PHY_XO", "CKXTAL1": "ETH_PHY_XI", "AVDD09": "V0V95_PHY",
        "RSET": "ETH_PHY_RSET", "MDIP0": "RJ_TD0P", "MDIN0": "RJ_TD0N", "MDIP1": "RJ_TD1P", "MDIN1": "RJ_TD1N",
        "MDIP2": "RJ_TD2P", "MDIN2": "RJ_TD2N", "MDIP3": "RJ_TD3P", "MDIN3": "RJ_TD3N", "DVDD33": V33P,
        "EVDD09": "V0V95_PHY", "HSON": "ETH_PHY_HSON", "HSOP": "ETH_PHY_HSOP", "GND": G,
        "HSIP": "ETH_PHY_HSIP", "HSIN": "ETH_PHY_HSIN", "INTB/PMEB": "ETH_PHY_INT", "EP": G,
        "CFG_OPT0/GPIO15880": "ETH_PHY_CFG0", "CFG_OPT1/GPIO15883": "ETH_PHY_CFG1", "LED2/PHYAD2": "ETH_PHY_LED2"},
        nc=["CLKOUT/SYNCE_CLK", "SPISO", "SPICSB", "SPISCK/GPIO15882/SYNCE_LOCK",
            "SPISI/GPIO15881", "LED0/PHYAD0", "LED1/PHYAD1", "NC", "POW_EXT_SWR"],
        fields={"Note": "PHYAD2 strapped low on the poe sheet (4.7k), LED2 drives the MagJack LED via 1k. SerDes mode via MDIO MMD30 0x697A."})
    D.R(sh, "2.49k", "ETH_PHY_RSET", G)
    D.R(sh, "4.7k", "ETH_PHY_CFG0", G, fields={"Note": "CFG_OPT0 low: CLKOUT off (no internal pull, DS 7.18)"})
    D.R(sh, "4.7k", "ETH_PHY_CFG1", G, fields={"Note": "CFG_OPT1 low: no MDI swap (MDIP0..3 = RJ pairs A..D). Confirm MagJack pair order"})
    D.IC(sh, "NX3225SA-25MHZ-STD-CSR-6", {"1": "ETH_PHY_XI", "3": "ETH_PHY_XO", "GND": G}, prefix="Y", value="25MHz 10pF")
    D.C(sh, "C_12p_50V", "ETH_PHY_XI", G)
    D.C(sh, "C_12p_50V", "ETH_PHY_XO", G)
    D.R(sh, "1.5k", "ETH_MDIO", V33P, fields={"Note": "MDIO pull-up 1.5k (RTL8221B datasheet)"})
    reset_supervisor(D, sh, V33P, "V0V95_PHY", "ETH_PHY_RST_N", "EXP_PHY_RST_N", V33P, "ETH_PHYR")
    D.R(sh, "10k", "ETH_PHY_INT", V33P)
    D.TP(sh, "ETH_PHY_INT", small=True)
    D.TP(sh, "ETH_MDC", small=True)
    D.TP(sh, "ETH_MDIO", small=True)
    for _ in range(7):
        D.C(sh, "C_100n_16V", "V0V95_PHY", G)
    for _ in range(5):
        D.C(sh, "C_100n_16V", "V3V3_PHYA", G)
    # SerDes AC coupling next to each TRANSMITTER: switch TX caps on board A, PHY/router TX caps on board B
    for a, b in [("ETH_S1TXP", "ETH_PHY_HSIP"), ("ETH_S1TXN", "ETH_PHY_HSIN"), ("ETH_S0TXP", "RTR_RXP"), ("ETH_S0TXN", "RTR_RXN")]:
        D.C(shA, "C_100n_16V", a, b, fields={"Note": "SerDes AC coupling at the switch transmitter (board A)"})
    for a, b in [("ETH_PHY_HSOP", "ETH_S1RXP"), ("ETH_PHY_HSON", "ETH_S1RXN")]:
        D.C(sh, "C_100n_16V", a, b, fields={"Note": "SerDes AC coupling at the PHY transmitter (board B)"})
    for a, b in [("RTR_TXP", "ETH_S0RXP"), ("RTR_TXN", "ETH_S0RXN")]:
        D.C(sh, "C_100n_16V", a, b, fields={"Note": "SerDes AC coupling at the router transmitter (board B)"})
        r0 = D.R(sh, "0", a, b, fields={"Note": "X-28: DNP 0R bypass, overlapping the 100 nF pads (no stub). Fit INSTEAD of the cap only "
                                                "if the module's integration drawing shows on-module TX AC caps."})
        r0.dnp = True

    # ---------------------------------------------------------------- router module (X-26)
    V33R = "V3V3_RTR_M"
    for n_ in ("V3V3_RTR", V33R):
        D.v(n_, 3.6)
    D.JP(sh, "V3V3_RTR", V33R, i_op=3.33, note="ISO router 3V3 (10 A copper)")
    D.CONN(sh, "ACELINK_SM81", ROUTER_PINS,
           {"VCC_3V3": V33R, "GND": G, "HSGMII_TXP": "RTR_TXP", "HSGMII_TXN": "RTR_TXN", "HSGMII_RXP": "RTR_RXP", "HSGMII_RXN": "RTR_RXN",
            "SMI_MDC": "RTR_SMDC", "SMI_MDIO": "RTR_SMDIO", "GPIO_SW_INT": "RTR_SW_INT", "UART0_TXD": "RTR_UART_TX",
            "UART0_RXD": "RTR_UART_RX", "SYS_RST_N": "RTR_RST_N", "WPS_RECOVERY": "RTR_BOOT", "LED_STATUS": "RTR_LED"},
           footprint="", prefix="M", value="Acelink SM81 (MT7981B) 3.3V",
           fields={"Consigned": True, "Op_I": 3.33, "Rated_I": 10.0, "MPN": "Acelink SM81",
                   "Note": "X-26: CONSIGNED solder-down stamp SoM, 50x36x3.0 mm. Supply +3.3 V (Acelink spec): 8 W typ = 2.42 A, "
                           "11 W max (full TX) = 3.33 A -> rail, jumper and pad copper rated >= 10 A (3:1). PIN NUMBERS, NAMES, "
                           "COUNT AND FOOTPRINT ARE PLACEHOLDERS - VERIFY EVERY PIN against the Acelink integration drawing "
                           "(not publicly available). 10 VCC pads assume 1 A per castellation (VERIFY). The module's own GbE PHY, "
                           "USB and second UART are unused. HSGMII 2.5G to RTL8372N S0 and P/N polarity (mediatek,pn_swap) VERIFY."})
    for n_ in ("RTR_RXP", "RTR_RXN", "RTR_TXP", "RTR_TXN", "RTR_SMDC", "RTR_SMDIO", "RTR_SW_INT", "RTR_UART_TX", "RTR_UART_RX",
               "RTR_LED", "RTR_RST_N", "RTR_BOOT", "ETH_S0TXP", "ETH_S0TXN", "ETH_S0RXP", "ETH_S0RXN"):
        D.v(n_, 3.6)
    for _ in range(4):
        D.C(sh, "C_22u_10V", V33R, G)
    for _ in range(4):
        D.C(sh, "C_100n_16V", V33R, G)
    D.TP(sh, V33R)
    D.TP(sh, "V3V3_RTR", small=True)
    # X-30: router reset is open-drain from the always-on side; pull-up in the router's own domain
    D.IC(sh, "SN74LVC1G07DBVR", {"A": "EXP_RTR_RST_N", "GND": G, "Y": "RTR_RST_N", "VCC": "V3V3"}, nc=["N.C."],
         fields={"Note": "X-30: open-drain (Ioff) router reset. Expander pin default input -> 100k pull-down -> router held in reset"})
    D.C(sh, "C_100n_16V", "V3V3", G)
    D.R(sh, "100k", "EXP_RTR_RST_N", G)
    D.R(sh, "10k", "RTR_RST_N", V33R, fields={"Note": "X-30: pull-up to the router's own rail"})
    D.TP(sh, "RTR_RST_N", small=True)
    D.R(sh, "10k", "RTR_BOOT", V33R, fields={"Note": "X-30: recovery strap pull-up in the router domain (VERIFY strap polarity)"})
    D.IC(sh, "TS-1187A-B-A-B", {"A": "RTR_BOOT", "D": G}, nc=["B", "C"], prefix="SW", value="ROUTER RECOVERY")
    # X-30: management/INT isolation FETs (gate on the router rail)
    for rtr, sw, rpu in (("RTR_SMDC", "ETH_SW_SMDC", "2.2k"), ("RTR_SMDIO", "ETH_SW_SMDIO", "2.2k"), ("RTR_SW_INT", "ETH_SW_INT", "10k")):
        D.IC(sh, "2N7002", {"G": V33R, "S": rtr, "D": sw}, prefix="Q",
             fields={"Note": f"X-30 domain isolation {rtr} <-> {sw}: off when V3V3_RTR_M is off; bidirectional when on"})
        D.R(sh, rpu, rtr, V33R)
    D.TP(sh, "RTR_UART_TX", small=True)
    D.TP(sh, "RTR_UART_RX", small=True)
    D.TP(sh, "RTR_LED", small=True)
    D.TP(sh, "GND", small=True)
    for n_ in ("ETH_STR_IF1", "ETH_STR_IF0", "ETH_STR_ENPHY", "ETH_SW_SELX", "ETH_PHY_CFG0", "ETH_PHY_CFG1"):
        D.v(n_, 3.6)
    return sh

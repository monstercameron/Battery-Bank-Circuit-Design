"""2.5G switch (RTL8372N, integrated 4x 2.5GBASE-T PHYs) + RTL8221B PHY for the RJ45 + router module connector.
Logic/network board (B).

RTL8372N (datasheet Rev 0.3): 0.95 V core + 3.3 V; 25 MHz +-50 ppm; RSET 2.49k 1 %; RSV_TEST0 4.7k to GND;
  INI_MODE default 11 (internal pull-ups) = CPU boots from SPI flash; SerDes 100 nF AC coupling; nRESET low >= 10.5 ms.
RTL8221B (Rev 1.2): SerDes HiSGMII/2500BASE-X, 0.1 uF AC caps both directions; MDIO pull-up 1.5k; PHYRSTB >= 10 ms.
"""


def build(D):
    sh = D.sheet("eth_switch", "2.5G switch RTL8372N + SPI flash (board A, beside the 4 NICs)", board="A")
    sh.note("Switch ports P0-P3 = USB-C ports 1-4 (PHY-to-PHY to each RTL8156BG). S0 -> router SerDes (LAN). S1 -> RTL8221B -> RJ45 (WAN, PoE in).")
    sh.note("Management: the router owns the switch (DSA) over SMDC/SMDIO; switch MDC0/MDIO0 manages the RTL8221B. SDK firmware in SPI flash.")
    G, V09, V33 = "GND", "V0V95_SW", "V3V3_ETH"
    D.v("V0V95_SWA", 1.0)
    D.v("V3V3_ETHA", 3.6)
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
        "SPF_SCK": "ETH_SPF_SCK", "SPF_SDI": "ETH_SPF_MOSI", "SPF_SDO": "ETH_SPF_MISO", "SPF_CSN": "ETH_SPF_CS",
        "RSET": "ETH_SW_RSET", "XI": "ETH_SW_XI", "XO": "ETH_SW_XO", "RSV_TEST0": "ETH_SW_TEST0",
        "LED_9/STR_REG_IF_SEL_1": "ETH_STR_IF1", "LED_12/STR_REG_IF_SEL_0": "ETH_STR_IF0", "LED_18/STR_EN_PHY": "ETH_STR_ENPHY", "SEL_XTAL": "ETH_SW_SELX",
        "nReset": "EXP_SW_RST_N", "INT": "ETH_SW_INT", "GPIO31/U0TXD": "ETH_SW_TXD", "GPIO32/U0RXD": "ETH_SW_RXD",
        "MDIO0": "ETH_MDIO", "MDC0": "ETH_MDC", "SSDI/SSDA/SMDIO/EE_SDA": "RTR_SMDIO", "SSCK/SSCL/SMDC/EE_SCL": "RTR_SMDC",
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
    # reset: expander-driven, RC holds >= 10.5 ms after the rails settle
    D.R(sh, "10k", "EXP_SW_RST_N", V33)
    D.C(sh, "C_2u2_16V", "EXP_SW_RST_N", G, fields={"Note": "10k x 2.2 uF = 22 ms reset hold"})
    D.TP(sh, "EXP_SW_RST_N", small=True)
    D.R(sh, "10k", "ETH_SW_INT", V33)
    D.TP(sh, "ETH_SW_INT", small=True)
    D.TP(sh, "ETH_SW_TXD", small=True)
    D.TP(sh, "ETH_SW_RXD", small=True)
    # SPI flash with SDK firmware (ISP pads)
    D.IC(sh, "W25Q32JVZPIQ", {"/CS": "ETH_SPF_CS", "DO(IO1)": "ETH_SPF_MISO", "/WP(IO2)": "ETH_SPF_WP", "GND": G,
                               "DI(IO0)": "ETH_SPF_MOSI", "CLK": "ETH_SPF_SCK", "/HOLDor/RESET(IO3)": "ETH_SPF_HOLD", "VCC": V33, "EP": G},
         fields={"Note": "RTL8372N SDK firmware (Realtek, under NDA). ISP pads for in-circuit programming."})
    D.R(sh, "10k", "ETH_SPF_WP", V33)
    D.R(sh, "10k", "ETH_SPF_HOLD", V33)
    D.R(sh, "10k", "ETH_SPF_CS", V33)
    D.C(sh, "C_100n_16V", V33, G)
    D.CONN(sh, "ISP_SW_FLASH", ["GND", "3V3", "CS", "CLK", "MOSI", "MISO"],
           {"GND": G, "3V3": V33, "CS": "ETH_SPF_CS", "CLK": "ETH_SPF_SCK", "MOSI": "ETH_SPF_MOSI", "MISO": "ETH_SPF_MISO"},
           footprint="Connector_PinHeader_1.27mm:PinHeader_1x06_P1.27mm_Vertical", fields={"_nobom": True}, prefix="J", dnp=True)

    shA = sh
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

    # RTL8221B PHY for the RJ45
    D.IC(sh, "RTL8221B-VB-CG", {
        "PHYRSTB": "EXP_PHY_RST_N", "MDC": "ETH_MDC", "MDIO": "ETH_MDIO", "DVDD09": "V0V95_PHY", "DVDD3318": V33,
        "AVDD33": "V3V3_PHYA", "AVDD33_XTAL": "V3V3_PHYA", "CKXTAL2": "ETH_PHY_XO", "CKXTAL1": "ETH_PHY_XI", "AVDD09": "V0V95_PHY",
        "RSET": "ETH_PHY_RSET", "MDIP0": "RJ_TD0P", "MDIN0": "RJ_TD0N", "MDIP1": "RJ_TD1P", "MDIN1": "RJ_TD1N",
        "MDIP2": "RJ_TD2P", "MDIN2": "RJ_TD2N", "MDIP3": "RJ_TD3P", "MDIN3": "RJ_TD3N", "DVDD33": V33,
        "EVDD09": "V0V95_PHY", "HSON": "ETH_PHY_HSON", "HSOP": "ETH_PHY_HSOP", "GND": G,
        "HSIP": "ETH_PHY_HSIP", "HSIN": "ETH_PHY_HSIN", "INTB/PMEB": "ETH_PHY_INT", "EP": G,
        "CFG_OPT0/GPIO15880": "ETH_PHY_CFG0", "CFG_OPT1/GPIO15883": "ETH_PHY_CFG1"},
        nc=["CLKOUT/SYNCE_CLK", "SPISO", "SPICSB", "SPISCK/GPIO15882/SYNCE_LOCK",
            "SPISI/GPIO15881", "LED0/PHYAD0", "LED1/PHYAD1", "LED2/PHYAD2", "NC", "POW_EXT_SWR"],
        fields={"Note": "PHYAD straps default (LED pins NC). SerDes mode set via MDIO MMD30 0x697A by the switch/router."})
    D.R(sh, "2.49k", "ETH_PHY_RSET", G)
    D.R(sh, "4.7k", "ETH_PHY_CFG0", G, fields={"Note": "CFG_OPT0 low: CLKOUT off (no internal pull, DS 7.18)"})
    D.R(sh, "4.7k", "ETH_PHY_CFG1", G, fields={"Note": "CFG_OPT1 low: no MDI swap (MDIP0..3 = RJ pairs A..D). Confirm MagJack pair order"})
    D.IC(sh, "NX3225SA-25MHZ-STD-CSR-6", {"1": "ETH_PHY_XI", "3": "ETH_PHY_XO", "GND": G}, prefix="Y", value="25MHz 10pF")
    D.C(sh, "C_12p_50V", "ETH_PHY_XI", G)
    D.C(sh, "C_12p_50V", "ETH_PHY_XO", G)
    D.R(sh, "1.5k", "ETH_MDIO", V33, fields={"Note": "MDIO pull-up 1.5k (RTL8221B datasheet)"})
    D.R(sh, "10k", "EXP_PHY_RST_N", V33)
    D.C(sh, "C_2u2_16V", "EXP_PHY_RST_N", G)
    D.R(sh, "10k", "ETH_PHY_INT", V33)
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
    for a, b in [("ETH_PHY_HSOP", "ETH_S1RXP"), ("ETH_PHY_HSON", "ETH_S1RXN"), ("RTR_TXP", "ETH_S0RXP"), ("RTR_TXN", "ETH_S0RXN")]:
        D.C(sh, "C_100n_16V", a, b, fields={"Note": "SerDes AC coupling at the PHY/router transmitter (board B)"})

    # Router module (OpenWrt MT7981B, 12 V input, HSGMII). Consigned; pinout to confirm with vendor.
    D.CONN(sh, "ROUTER_MODULE", ["V12", "V12", "GND", "GND", "GND", "GND", "GND", "GND", "HS_RXP", "HS_RXN", "HS_TXP", "HS_TXN",
                                 "MDC", "MDIO", "SW_INT", "VIO_3V3", "UART_TX", "UART_RX", "RESET_N", "BOOT_RECOVERY", "PWR_LED"],
           {"V12": "V12_RTR", "GND": G, "HS_RXP": "RTR_RXP", "HS_RXN": "RTR_RXN", "HS_TXP": "RTR_TXP", "HS_TXN": "RTR_TXN",
            "MDC": "RTR_SMDC", "MDIO": "RTR_SMDIO", "SW_INT": "ETH_SW_INT", "VIO_3V3": V33, "UART_TX": "RTR_UART_TX",
            "UART_RX": "RTR_UART_RX", "RESET_N": "EXP_RTR_RST_N", "BOOT_RECOVERY": "RTR_BOOT", "PWR_LED": "RTR_LED"},
           footprint="", fields={"Consigned": True, "Op_I": 0.92, "Rated_I": 3.0,
                                 "Note": "Placeholder for GainStrong Oolite MT7981B / Acelink SM81. VERIFY pinout, 2.5G HSGMII and 12 V input."},
           prefix="M")
    for n_ in ("RTR_RXP", "RTR_RXN", "RTR_TXP", "RTR_TXN", "RTR_SMDC", "RTR_SMDIO", "RTR_UART_TX", "RTR_UART_RX", "RTR_LED", "ETH_S0TXP", "ETH_S0TXN"):
        D.v(n_, 3.6)
    D.R(sh, "10k", "EXP_RTR_RST_N", V33, fields={"Note": "C-10: pull-up in the router/ETH domain, not always-on 3V3"})
    D.R(sh, "10k", "RTR_SMDIO", V33, fields={"Note": "management pull-up (MDIO-style) VERIFY"})
    D.TP(sh, "RTR_UART_TX", small=True)
    D.TP(sh, "RTR_UART_RX", small=True)
    D.TP(sh, "RTR_LED", small=True)
    D.R(sh, "10k", "RTR_BOOT", V33)
    D.IC(sh, "TS-1187A-B-A-B", {"A": "RTR_BOOT", "D": G}, nc=["B", "C"], prefix="SW", value="ROUTER RECOVERY")
    for n_ in ("ETH_S0RXP", "ETH_S0RXN", "RTR_BOOT", "ETH_STR_IF1", "ETH_STR_IF0", "ETH_STR_ENPHY", "ETH_SW_SELX", "ETH_PHY_CFG0", "ETH_PHY_CFG1"):
        D.v(n_, 3.6)
    for _ in range(2):
        D.C(sh, "C_22u_25V", "V12_RTR", G)
    D.TP(sh, "V12_RTR")
    return sh

"""Controller: ESP32-WROOM-32UE (Wi-Fi + Classic BT, U.FL), TCA9548A I2C mux, 2x TCA9535 expanders,
PCF85063A RTC, NT3H2111 NFC, buttons, SLOW switch, fan, microSD, debug pads.

I2C map (main bus I2C_SDA/SCL): TPS26750 x4 0x20-0x23, TCA9535 0x26/0x27, PCF85063A 0x51, TCA9548A 0x70.
Mux channels: 0-3 spare (port BQ25756s moved to each TPS26750 I2Cc), 4 = input stage BQ25756, 5 = DC-out BQ25756,
6 = NFC NT3H2111 (0x55), 7 = cartridge gauge BQ34Z100 (0x55) via pogo pads.
ESP32 pins (datasheet: GPIO34-39 input only; GPIO0/2/5/12/15 straps; ADC2 unusable with Wi-Fi):
  IO21 SDA, IO22 SCL | IO34 PD_INT_N, IO35 CHG_INT_N, IO36 LED_NTC, IO39 FAN_TACH
  IO25 BCLK, IO26 LRCLK, IO27 DIN (I2S1 -> amp) | IO32 PDM CLK, IO33 PDM DATA (I2S0 PDM RX)
  IO4 glow data | IO13 flashlight PWM (high = on, X-39) | IO14 fan PWM | IO16/17 UART2 <-> nRF52840
  IO18/19/23/5 microSD SPI | IO2 mux reset (strap low) | IO15 flashlight button (strap high) | IO12 amp enable (strap low)

X-30 power-state table (domains, when they may be off, and how every crossing signal is protected):
  V3V3        TPS62933, always on with VBAT        reference domain: ESP32 island, expanders, mux, RTC, NFC, SD, mics
  V3V3_ESP    V3V3 via JP (C-17)                   off only with the JP cut; ESP straps/EN on V3V3_ESP, bus pull-ups on V3V3
  V5_AUX      TPS62933, always on                  amp (V5_AMP via JP), red LED, fan switch input
  V3V3_ETH / V5_ETH / V0V95_SW  EXP_EN_ETH         default off. Resets: TPS3808 open-drain powered from V3V3, pull-ups on the
                                                   target rail; expander reset pins only reach TPS3808 MR (same V3V3 domain)
  V3V3_RTR(_M) EXP_EN_RTR = EXP_EN_RTR_REQ AND     default off. Hardware interlock: TPS3808G33 on V3V3_ETH pulls EXP_EN_RTR low,
              V3V3_ETH valid (+20 ms)              so "router on / ETH off" cannot occur. "Router off / ETH on": MDC/MDIO/INT
                                                   through 2N7002 pass FETs gated by V3V3_RTR_M; reset via LVC1G07 open-drain;
                                                   recovery/reset pull-ups on V3V3_RTR_M; SerDes AC-coupled.
  V3V3_LORA   TPS22965, EXP_EN_LORA                default off. ESP TX -> nRF RX via SN74LVC1G125 powered by V3V3_NRF (Ioff);
                                                   nRF TX -> ESP RX via SN74LVC1G125 on V3V3; nRF reset via LVC1G07 open-drain.
  V5_GLOW     TPS22965, EXP_EN_GLOW                default off. AHCT1G125 now powered by V5_GLOW_L: its inputs (IO4, OE) have
                                                   no VCC clamp (VI abs-max 7 V at any VCC); output lives in the strip domain.
  V5_FAN      TPS22965, EXP_EN_FAN                 default off. TACH open-collector to V3V3; PWM open-drain (C-12).
  LED_VIN     VBAT via JP                          flashlight CTRL clamp biased from LED_VIN itself (X-39); ESP only releases it.
  Audio       V5_AMP / V3V3_MIC via JPs            I2S/PDM sources and loads both in always-on domains: no gated crossing.
  Firmware-only rules: switch ETH off only after the router (hold RTR reset, EXP_EN_RTR_REQ low, then EXP_EN_ETH low), and keep
  ETH off >= 200 ms before re-enabling (H-20).
"""


def button(D, sh, net, note):
    # C-18: diagonal pads (A = pad 1 top-left, D = pad 4 bottom-right) are always across the switch
    D.IC(sh, "TS-1187A-B-A-B", {"A": net, "D": "GND"}, nc=["B", "C"], prefix="SW", value=note)


# Expander #2 (0x26) spare-pin assignments requested by the power/PoE blocks: (pin, net, direction, note)
EXP2_REQUESTS = [
    ("P04", "EXP_ORING_DC_DIS", "out", "DC-jack ideal-diode disable (active high, 100k pull-down on power_input)"),
    ("P05", "EXP_ORING_POE_DIS", "out", "PoE ideal-diode disable (active high, 100k pull-down on power_input)"),
    ("P06", "EXP_INS_ILIM_A", "out", "input-stage ILIM step A (active high, pull-down on power_input)"),
    ("P07", "EXP_INS_ILIM_B", "out", "input-stage ILIM step B (active high, pull-down on power_input)"),
    ("P10", "EXP_INS_CHG_DIS", "out", "input-stage charger ~CE disable (active high, 100k pull-down on power_input)"),
    ("P11", "EXP_POE_CLASS", "in", "TPS2373 TPH (active low, 47k pull-up on poe)"),
    ("P12", "EXP_POE_CLASS_TPL", "in", "TPS2373 TPL (active low, 47k pull-up on poe)"),
]


def build(D):
    sh = D.sheet("mcu", "ESP32 controller, I2C mux/expander, RTC, NFC, buttons, fan, microSD, debug")
    G, V = "GND", "V3V3"
    VE = "V3V3_ESP"
    D.v(VE, 3.6)
    D.JP(sh, V, VE, i_op=0.5, note="ISO ESP32 3V3")
    D.TP(sh, VE)
    D.TP(sh, "GND")
    D.IC(sh, "ESP32-WROOM-32UE", {
        "GND": G, "3V3": VE, "EN": "ESP_EN", "SENSOR_VP": "LED_NTC", "SENSOR_VN": "FAN_TACH", "IO34": "PD_INT_N", "IO35": "CHG_INT_N",
        "IO32": "MIC_CLK", "IO33": "MIC_DATA", "IO25": "AUD_BCLK", "IO26": "AUD_LRCLK", "IO27": "AUD_DIN", "IO14": "FAN_PWM",
        "IO12": "AMP_EN", "IO13": "FLASH_PWM", "IO15": "BTN_FLASH", "IO2": "I2C_MUX_RST_N", "IO0": "ESP_IO0", "IO4": "GLOW_D3V3",
        "IO16": "LORA_TX", "IO17": "LORA_RX", "IO5": "SD_CS", "IO18": "SD_CLK", "IO19": "SD_MISO", "IO21": "I2C_SDA",
        "RXD0": "ESP_RXD0", "TXD0": "ESP_TXD0", "IO22": "I2C_SCL", "IO23": "SD_MOSI"},
        nc=["NC"], fields={"Note": "U.FL antenna to FPC in the RF end cap (metal case). Strapping pins per datasheet."})
    D.C(sh, "C_22u_10V", VE, G)
    D.C(sh, "C_1u_16V", VE, G)
    D.C(sh, "C_100n_16V", VE, G)
    D.R(sh, "10k", "ESP_EN", VE)
    D.C(sh, "C_1u_16V", "ESP_EN", G, fields={"Note": "EN RC delay (Espressif HW guidelines)"})
    D.R(sh, "10k", "ESP_IO0", VE)
    button(D, sh, "ESP_EN", "RESET")
    button(D, sh, "ESP_IO0", "BOOT")
    button(D, sh, "BTN_FLASH", "FLASH")
    D.R(sh, "10k", "BTN_FLASH", VE, fields={"Note": "IO15 strap high"})
    D.TP(sh, "ESP_EN", small=True)
    D.TP(sh, "ESP_IO0", small=True)
    D.R(sh, "100k", "I2C_MUX_RST_N", G, fields={"Note": "IO2 strap low; holds the I2C mux in reset until firmware releases it (C-7 bus recovery)"})
    D.R(sh, "100k", "AMP_EN", G, fields={"Note": "IO12 strap low (3.3 V flash)"})
    D.R(sh, "10k", "SD_CS", V, fields={"Note": "IO5 strap high"})
    sh.note("X-42 shared interrupt PD_INT_N (IO34, level): 4x TPS26750 I2Ct_IRQ + both TCA9535 INT. Firmware drain-all: on low, read "
            "the IRQ status of all 4 PD controllers and both expander input ports (each read clears its source) and repeat until "
            "the line is high; never stop at the first source found. Poll all six once after every ESP32 reset.")
    sh.note("X-42 shared interrupt CHG_INT_N (IO35, 256 us pulses): every BQ25756 ~INT on the line. On a falling edge read "
            "FAULT/FLAG of every BQ25756 on it; also poll them every 1 s and after reset (overlapping pulses merge). "
            "Latch safety faults in firmware until acknowledged.")
    for net in ("PD_INT_N", "CHG_INT_N", "FAN_TACH"):
        D.R(sh, "10k", net, V)
    D.TP(sh, "PD_INT_N", small=True)
    D.TP(sh, "CHG_INT_N", small=True)
    for net in ("I2C_SDA", "I2C_SCL"):
        D.R(sh, "2.2k", net, V)
        D.TP(sh, net, small=True)
    D.TP(sh, "GND", small=True)          # X-42: ground pad beside the main-bus SDA/SCL pair
    D.R(sh, "100", "ESP_DBG_VREF", VE, fields={"Note": "C-28: header 3V3 is a VTref sense pin (100R), not a supply input"})
    D.CONN(sh, "DEBUG_ESP32", ["GND", "3V3", "TXD0", "RXD0", "EN", "IO0"],
           {"GND": G, "3V3": "ESP_DBG_VREF", "TXD0": "ESP_TXD0", "RXD0": "ESP_RXD0", "EN": "ESP_EN", "IO0": "ESP_IO0"},
           footprint="Connector_PinHeader_1.27mm:PinHeader_1x06_P1.27mm_Vertical", fields={"_nobom": True}, prefix="J", dnp=True)
    D.IC(sh, "SM04B-SRSS-TB", {"1": G, "2": V, "3": "I2C_SDA", "4": "I2C_SCL"}, nc=["5", "6"], prefix="J",
         value="Qwiic (DNP)", dnp=True, fields={"Note": "Qwiic/STEMMA QT debug tap on the main I2C bus"})

    # I2C mux
    mux = {"A0": G, "A1": G, "A2": G, "~{RESET}": "I2C_MUX_RST_N", "GND": G, "SCL": "I2C_SCL", "SDA": "I2C_SDA", "VCC": V}
    for ch in range(8):
        mux[f"SD{ch}"] = f"I2C{ch}_SDA"
        mux[f"SC{ch}"] = f"I2C{ch}_SCL"
    D.IC(sh, "TCA9548APWR", mux, fields={"Note": "0x70"})
    sh.note("Mux channels 0-3 are no longer used by the USB-C ports (their BQ25756s moved to each TPS26750 I2Cc bus); "
            "they keep pull-ups and test pads as spare/debug branches.")
    D.C(sh, "C_100n_16V", V, G)
    for ch in range(8):
        for s in ("SDA", "SCL"):
            D.R(sh, "4.7k", f"I2C{ch}_{s}", V)
            D.TP(sh, f"I2C{ch}_{s}", small=True)
        D.TP(sh, "GND", small=True)      # X-42: ground pad next to each branch SDA/SCL pair

    # IO expander (enables default OFF: pull-downs on every EXP_EN_* net; expander powers up as inputs)
    D.IC(sh, "TCA9535PWR_C130204", {
        "~{INT}": "PD_INT_N", "A0": V, "A1": V, "A2": V, "GND": G, "SCL": "I2C_SCL", "SDA": "I2C_SDA", "VCC": V,
        "P00": "EXP_EN_ETH", "P01": "EXP_EN_RTR_REQ", "P02": "EXP_EN_QI", "P03": "EXP_EN_LORA", "P04": "EXP_EN_GLOW",
        "P05": "EXP_P05_SPARE", "P06": "EXP_SW_RST_N", "P07": "EXP_PHY_RST_N", "P10": "EXP_RTR_RST_N", "P11": "EXP_LORA_RST_N",
        "P12": "EXP_DCI_DIS", "P13": "EXP_P13_SPARE", "P14": "DCOF_EN", "P15": "SD_DET", "P16": "NFC_FD", "P17": "EXP_EN_FAN"},
        fields={"Note": "0x27. TCA9535: NO internal pull-ups, so the EXP_EN_* pull-downs hold gated rails OFF until firmware (C-1). "
                        "P06/P07 -> TPS3808 MR (V3V3 domain); P10/P11 -> LVC1G07 open-drain buffers; P12 EXP_DCI_DIS active-high "
                        "eFuse disable (2N7002 on power_input). INT on level-type PD_INT_N (C-8)."})
    D.R(sh, "10k", "EXP_EN_RTR_REQ", "EXP_EN_RTR",
        fields={"Note": "X-30: router-rail request; the V3V3_ETH TPS3808 interlock (eth_switch) pulls EXP_EN_RTR low through this 10k"})
    # second expander 0x26: static I/O moved off the ESP32 + power/PoE control requested by those blocks
    existing = set(D.netlist())
    exp2 = {"~{INT}": "PD_INT_N", "A0": G, "A1": V, "A2": V, "GND": G, "SCL": "I2C_SCL", "SDA": "I2C_SDA", "VCC": V,
            "P00": "SLOW_SW", "P01": "RED_LED", "P02": "GLOW_OE_N", "P03": "EXP_USBA_DIS"}
    for pin, net, _dir, _note in EXP2_REQUESTS:
        # guarded: a requested net that does not exist yet in the build stays on a spare test pad
        exp2[pin] = net if net in existing else f"EXP2_{pin}"
    for pin in ("P13", "P14", "P15", "P16", "P17"):
        exp2[pin] = f"EXP2_{pin}"
    D.IC(sh, "TCA9535PWR_C130204", exp2,
         fields={"Note": "0x26: SLOW switch, red LED, glow OE, USB-A disable; P04-P12 power/PoE control: "
                         + "; ".join(f"{p} {n} ({d})" for p, n, d, _ in EXP2_REQUESTS) + "; P13-P17 spare on test pads"})
    D.C(sh, "C_100n_16V", V, G)
    D.R(sh, "10k", "SLOW_SW", V)
    D.R(sh, "100k", "RED_LED", G, fields={"Note": "night LED off by default"})
    D.R(sh, "10k", "EXP_USBA_DIS", V, fields={"Note": "C-14: USB-A disabled by default"})
    for pin, net in exp2.items():
        if net.startswith("EXP2_P"):
            D.TP(sh, net, small=True)
    D.C(sh, "C_100n_16V", V, G)
    D.TP(sh, "EXP_P05_SPARE", small=True)
    D.TP(sh, "EXP_P13_SPARE", small=True)
    D.R(sh, "100k", "EXP_EN_FAN", G)

    # RTC
    D.IC(sh, "PCF85063AT_AY_C5151540", {"OSCI": "RTC_XI", "OSCO": "RTC_XO", "~{INT}": "RTC_INT_N", "VSS": G, "SDA": "I2C_SDA",
                                        "SCL": "I2C_SCL", "VDD": V}, nc=["CLKOUT"], fields={"Note": "0x51; internal 7 pF load (CAP_SEL default)"})
    D.IC(sh, "7LC32768F07UC", {"OSC1": "RTC_XI", "OSC2": "RTC_XO"}, prefix="Y", value="32.768k 7pF")
    D.R(sh, "10k", "RTC_INT_N", V)
    D.TP(sh, "RTC_INT_N", small=True)
    D.C(sh, "C_100n_16V", V, G)

    # NFC tag (mux ch6)
    D.IC(sh, "NT3H2111W0FHKH", {"LA": "NFC_LA", "VSS": G, "SCL": "I2C6_SCL", "FD": "NFC_FD", "SDA": "I2C6_SDA", "VCC": V, "LB": "NFC_LB"},
         nc=["VOUT"], fields={"Note": "0x55 on mux ch6. Antenna coil tuned to 13.56 MHz with the 50 pF input cap."})
    D.CONN(sh, "NFC_ANTENNA", ["LA", "LB"], {"LA": "NFC_LA", "LB": "NFC_LB"}, footprint="", prefix="ANT",
           fields={"_nobom": True, "Note": "PCB-trace coil under a non-metal window (layout TODO)"})
    D.R(sh, "10k", "NFC_FD", V)
    D.C(sh, "C_100n_16V", V, G)

    # SLOW switch
    D.IC(sh, "MST-12D18G2SMDSLIDESWITCH", {"2": "SLOW_SW", "1": G}, nc=["3"], prefix="SW", value="SLOW")

    # fan: 4-wire 5 V; high-side power switch (EXP_EN_FAN) + open-drain PWM
    D.IC(sh, "SM04B-SRSS-TB", {"1": G, "2": "V5_FAN", "3": "FAN_TACH", "4": "FAN_PWM_OD"}, nc=["5", "6"], prefix="J", value="FAN")
    D.IC(sh, "TPS22965DSGR", {"VIN": "V5_AUX", "ON": "EXP_EN_FAN", "VBIAS": "V5_AUX", "GND": G, "CT": "FAN_CT", "VOUT": "V5_FAN", "EP": G},
         fields={"Op_I": 0.2, "Rated_I": 6.0, "Note": "C-12: high-side fan switch; solid fan ground so the tach can't back-feed IO39"})
    D.C(sh, "C_1n_50V", "FAN_CT", G)
    D.C(sh, "C_1u_16V", "V5_FAN", G)
    D.v("V5_FAN", 5.5)
    D.IC(sh, "AO3400A", {"D": "FAN_PWM_OD", "G": "FAN_PWMG", "S": G}, prefix="Q")
    D.R(sh, "100", "FAN_PWM", "FAN_PWMG")
    D.R(sh, "100k", "FAN_PWMG", G)
    D.v("FAN_PWM_OD", 5.5)

    # microSD (SPI)
    D.IC(sh, "TF-01A", {"CDDAT3(CS)": "SD_CS", "CMD(DI)": "SD_MOSI", "VDD": V, "CLK(SCLK)": "SD_CLK", "VSS": G, "DAT0(D0)": "SD_MISO",
                        "CD": "SD_DET", "GND": G}, nc=["DAT2(RSV)", "DAT1(RSV)"], prefix="J", value="microSD")
    D.R(sh, "10k", "SD_DET", V)
    D.R(sh, "10k", "SD_MISO", V)
    D.C(sh, "C_10u_16V", V, G)

    # glow data: IO4 defined low at boot; the 3.3 -> 5 V buffer now sits on the glow sheet in the strip's own domain (X-30)
    D.R(sh, "10k", "GLOW_D3V3", G, fields={"Note": "C-11: defined low at boot"})
    return sh

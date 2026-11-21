"""Controller: ESP32-WROOM-32UE (Wi-Fi + Classic BT, U.FL), TCA9548A I2C mux, TCA9555 expander,
PCF85063A RTC, NT3H2111 NFC, buttons, SLOW switch, fan, microSD, debug pads, glow-LED level shifter.

I2C map (main bus I2C_SDA/SCL): TPS26750 x4 0x20-0x23, TCA9555 0x27, PCF85063A 0x51, TCA9548A 0x70.
Mux channels: 0-3 = port BQ25756s (0x6B), 4 = input stage BQ25756, 5 = DC-out BQ25756, 6 = NFC NT3H2111 (0x55),
7 = cartridge gauge BQ34Z100 (0x55) via pogo pads.
ESP32 pins (datasheet: GPIO34-39 input only; GPIO0/2/5/12/15 straps; ADC2 unusable with Wi-Fi):
  IO21 SDA, IO22 SCL | IO34 PD_INT_N, IO35 CHG_INT_N (also expander INT), IO36 SLOW_SW, IO39 FAN_TACH
  IO25 BCLK, IO26 LRCLK, IO27 DIN (I2S1 -> amp) | IO32 PDM CLK, IO33 PDM DATA (I2S0 PDM RX)
  IO4 glow data | IO13 flashlight PWM (low = on) | IO14 fan PWM | IO16/17 UART2 <-> nRF52840
  IO18/19/23/5 microSD SPI | IO2 red night LED (strap low) | IO15 flashlight button (strap high) | IO12 amp enable (strap low)
"""


def button(D, sh, net, note):
    D.IC(sh, "TS-1187A-B-A-B", {"A": net, "B": net, "C": "GND", "D": "GND"}, prefix="SW", value=note)


def build(D):
    sh = D.sheet("mcu", "ESP32 controller, I2C mux/expander, RTC, NFC, buttons, fan, microSD, debug")
    G, V = "GND", "V3V3"
    D.IC(sh, "ESP32-WROOM-32UE", {
        "GND": G, "3V3": V, "EN": "ESP_EN", "SENSOR_VP": "SLOW_SW", "SENSOR_VN": "FAN_TACH", "IO34": "PD_INT_N", "IO35": "CHG_INT_N",
        "IO32": "MIC_CLK", "IO33": "MIC_DATA", "IO25": "AUD_BCLK", "IO26": "AUD_LRCLK", "IO27": "AUD_DIN", "IO14": "FAN_PWM",
        "IO12": "AMP_EN", "IO13": "FLASH_PWM_N", "IO15": "BTN_FLASH", "IO2": "RED_LED", "IO0": "ESP_IO0", "IO4": "GLOW_D3V3",
        "IO16": "LORA_TX", "IO17": "LORA_RX", "IO5": "SD_CS", "IO18": "SD_CLK", "IO19": "SD_MISO", "IO21": "I2C_SDA",
        "RXD0": "ESP_RXD0", "TXD0": "ESP_TXD0", "IO22": "I2C_SCL", "IO23": "SD_MOSI"},
        nc=["NC"], fields={"Note": "U.FL antenna to FPC in the RF end cap (metal case). Strapping pins per datasheet."})
    D.C(sh, "C_22u_10V", V, G)
    D.C(sh, "C_1u_16V", V, G)
    D.C(sh, "C_100n_16V", V, G)
    D.R(sh, "10k", "ESP_EN", V)
    D.C(sh, "C_1u_16V", "ESP_EN", G, fields={"Note": "EN RC delay (Espressif HW guidelines)"})
    D.R(sh, "10k", "ESP_IO0", V)
    button(D, sh, "ESP_EN", "RESET")
    button(D, sh, "ESP_IO0", "BOOT")
    button(D, sh, "BTN_FLASH", "FLASH")
    D.R(sh, "10k", "BTN_FLASH", V, fields={"Note": "IO15 strap high"})
    D.R(sh, "100k", "RED_LED", G, fields={"Note": "IO2 strap low"})
    D.R(sh, "100k", "AMP_EN", G, fields={"Note": "IO12 strap low (3.3 V flash)"})
    D.R(sh, "10k", "SD_CS", V, fields={"Note": "IO5 strap high"})
    for net in ("PD_INT_N", "CHG_INT_N", "FAN_TACH", "SLOW_SW"):
        D.R(sh, "10k", net, V)
    for net in ("I2C_SDA", "I2C_SCL"):
        D.R(sh, "2.2k", net, V)
        D.TP(sh, net, small=True)
    D.CONN(sh, "DEBUG_ESP32", ["GND", "3V3", "TXD0", "RXD0", "EN", "IO0"],
           {"GND": G, "3V3": V, "TXD0": "ESP_TXD0", "RXD0": "ESP_RXD0", "EN": "ESP_EN", "IO0": "ESP_IO0"},
           footprint="Connector_PinHeader_1.27mm:PinHeader_1x06_P1.27mm_Vertical", fields={"_nobom": True}, prefix="J", dnp=True)
    D.IC(sh, "SM04B-SRSS-TB", {"1": G, "2": V, "3": "I2C_SDA", "4": "I2C_SCL"}, nc=["5", "6"], prefix="J",
         value="Qwiic (DNP)", dnp=True, fields={"Note": "Qwiic/STEMMA QT debug tap on the main I2C bus"})

    # I2C mux
    mux = {"A0": G, "A1": G, "A2": G, "~{RESET}": "I2C_MUX_RST_N", "GND": G, "SCL": "I2C_SCL", "SDA": "I2C_SDA", "VCC": V}
    for ch in range(8):
        mux[f"SD{ch}"] = f"I2C{ch}_SDA"
        mux[f"SC{ch}"] = f"I2C{ch}_SCL"
    D.IC(sh, "TCA9548APWR", mux, fields={"Note": "0x70"})
    D.R(sh, "10k", "I2C_MUX_RST_N", V)
    D.C(sh, "C_100n_16V", V, G)
    for ch in range(8):
        for s in ("SDA", "SCL"):
            D.R(sh, "4.7k", f"I2C{ch}_{s}", V)
            D.TP(sh, f"I2C{ch}_{s}", small=True)

    # IO expander (enables default OFF: pull-downs on every EXP_EN_* net; expander powers up as inputs)
    D.IC(sh, "TCA9555PWR", {
        "~{INT}": "CHG_INT_N", "A0": V, "A1": V, "A2": V, "GND": G, "SCL": "I2C_SCL", "SDA": "I2C_SDA", "VCC": V,
        "P00": "EXP_EN_ETH", "P01": "EXP_EN_RTR", "P02": "EXP_EN_QI", "P03": "EXP_EN_LORA", "P04": "EXP_EN_GLOW",
        "P05": "EXP_EN_USBA", "P06": "EXP_SW_RST_N", "P07": "EXP_PHY_RST_N", "P10": "EXP_RTR_RST_N", "P11": "EXP_LORA_RST_N",
        "P12": "DCI_EN", "P13": "EXP_P13_SPARE", "P14": "DCOF_EN", "P15": "SD_DET", "P16": "NFC_FD", "P17": "EXP_EN_FAN"},
        fields={"Note": "0x27. INT wire-ORed onto CHG_INT_N."})
    D.C(sh, "C_100n_16V", V, G)
    D.R(sh, "100k", "EXP_EN_USBA", G)
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

    # fan: 4-wire 5 V; low-side power switch (EXP_EN_FAN) + open-drain PWM
    D.IC(sh, "SM04B-SRSS-TB", {"1": "FAN_GND", "2": "V5_AUX", "3": "FAN_TACH", "4": "FAN_PWM_OD"}, nc=["5", "6"], prefix="J", value="FAN")
    D.IC(sh, "AO3400A", {"D": "FAN_GND", "G": "EXP_EN_FAN", "S": G}, prefix="Q", fields={"Op_I": 0.2, "Rated_I": 5.7})
    D.IC(sh, "AO3400A", {"D": "FAN_PWM_OD", "G": "FAN_PWMG", "S": G}, prefix="Q")
    D.R(sh, "100", "FAN_PWM", "FAN_PWMG")
    D.R(sh, "100k", "FAN_PWMG", G)
    D.v("FAN_GND", 5.5)
    D.v("FAN_PWM_OD", 5.5)

    # microSD (SPI)
    D.IC(sh, "TF-01A", {"CDDAT3(CS)": "SD_CS", "CMD(DI)": "SD_MOSI", "VDD": V, "CLK(SCLK)": "SD_CLK", "VSS": G, "DAT0(D0)": "SD_MISO",
                        "CD": "SD_DET", "GND": G}, nc=["DAT2(RSV)", "DAT1(RSV)"], prefix="J", value="microSD")
    D.R(sh, "10k", "SD_DET", V)
    D.R(sh, "10k", "SD_MISO", V)
    D.C(sh, "C_10u_16V", V, G)

    # glow data level shifter 3.3 V -> 5 V
    D.IC(sh, "SN74AHCT1G125DBVR", {"~{OE}": G, "A": "GLOW_D3V3", "GND": G, "Y": "GLOW_D5V", "VCC": "V5_AUX"}, prefix="U")
    D.C(sh, "C_100n_16V", "V5_AUX", G)
    D.v("GLOW_D5V", 5.5)
    return sh

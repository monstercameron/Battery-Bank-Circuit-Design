"""Review round 1 - control/DFM repairs (C-1, C-2, C-3, C-5, C-6, C-7, C-8, C-9, C-10, C-11, C-12, C-13, C-14, C-15 partial,
C-16, C-18). Applied to hardware/gen/blocks/*.py. Idempotence: each substitution asserts its source text exists."""
import os

GEN = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "gen")


def sub(rel, old, new):
    path = os.path.join(GEN, rel)
    t = open(path, encoding="utf-8").read()
    assert old in t, (rel, old[:90])
    open(path, "w", encoding="utf-8").write(t.replace(old, new, 1))


M = "blocks/mcu.py"
# C-18 buttons: diagonal pads only (pads 1 and 4 are across the switch whatever the internal pairing)
sub(M, '''    D.IC(sh, "TS-1187A-B-A-B", {"A": net, "B": net, "C": "GND", "D": "GND"}, prefix="SW", value=note)''',
    '''    # C-18: diagonal pads (A = pad 1 top-left, D = pad 4 bottom-right) are always across the switch
    D.IC(sh, "TS-1187A-B-A-B", {"A": net, "D": "GND"}, nc=["B", "C"], prefix="SW", value=note)''')
# C-6 / C-7 GPIO reshuffle
sub(M, '"SENSOR_VP": "SLOW_SW",', '"SENSOR_VP": "LED_NTC",')
sub(M, '"IO2": "RED_LED",', '"IO2": "I2C_MUX_RST_N",')
sub(M, '''    D.R(sh, "100k", "RED_LED", G, fields={"Note": "IO2 strap low"})''',
    '''    D.R(sh, "100k", "I2C_MUX_RST_N", G, fields={"Note": "IO2 strap low; holds the I2C mux in reset until firmware releases it (C-7 bus recovery)"})''')
sub(M, '''    for net in ("PD_INT_N", "CHG_INT_N", "FAN_TACH", "SLOW_SW"):''', '''    for net in ("PD_INT_N", "CHG_INT_N", "FAN_TACH"):''')
sub(M, '''    D.R(sh, "10k", "I2C_MUX_RST_N", V)\n''', '')
# C-1 TCA9555 -> TCA9535; C-8 INT onto the level-type PD_INT_N
sub(M, '''    D.IC(sh, "TCA9555PWR", {
        "~{INT}": "CHG_INT_N", "A0": V, "A1": V, "A2": V,''', '''    D.IC(sh, "TCA9535PWR_C130204", {
        "~{INT}": "PD_INT_N", "A0": V, "A1": V, "A2": V,''')
sub(M, '''        fields={"Note": "0x27. INT wire-ORed onto CHG_INT_N."})''',
    '''        fields={"Note": "0x27. TCA9535: NO internal pull-ups, so the EXP_EN_* pull-downs hold gated rails OFF until firmware (C-1). INT on level-type PD_INT_N (C-8)."})
    # second expander 0x26: static I/O moved off the ESP32
    D.IC(sh, "TCA9535PWR_C130204", {
        "~{INT}": "PD_INT_N", "A0": G, "A1": V, "A2": V, "GND": G, "SCL": "I2C_SCL", "SDA": "I2C_SDA", "VCC": V,
        "P00": "SLOW_SW", "P01": "RED_LED", "P02": "GLOW_OE_N", "P03": "EXP_USBA_DIS", "P04": "EXP2_P04",
        "P05": "EXP2_P05", "P06": "EXP2_P06", "P07": "EXP2_P07", "P10": "EXP2_P10", "P11": "EXP2_P11", "P12": "EXP2_P12",
        "P13": "EXP2_P13", "P14": "EXP2_P14", "P15": "EXP2_P15", "P16": "EXP2_P16", "P17": "EXP2_P17"},
        fields={"Note": "0x26: SLOW switch, red LED, glow OE, USB-A disable, spares on test points"})
    D.C(sh, "C_100n_16V", V, G)
    D.R(sh, "10k", "SLOW_SW", V)
    D.R(sh, "100k", "RED_LED", G, fields={"Note": "night LED off by default"})
    D.R(sh, "10k", "GLOW_OE_N", "V5_AUX", fields={"Note": "C-11: level shifter disabled (Hi-Z) by default"})
    D.R(sh, "10k", "EXP_USBA_DIS", V, fields={"Note": "C-14: USB-A disabled by default"})
    for p_ in ("04", "05", "06", "07", "10", "11", "12", "13", "14", "15", "16", "17"):
        D.TP(sh, f"EXP2_P{p_}", small=True)''')
# C-11 glow level shifter
sub(M, '''    D.IC(sh, "SN74AHCT1G125DBVR", {"~{OE}": G, "A": "GLOW_D3V3",''',
    '''    D.R(sh, "10k", "GLOW_D3V3", G, fields={"Note": "C-11: defined low at boot"})
    D.IC(sh, "SN74AHCT1G125DBVR", {"~{OE}": "GLOW_OE_N", "A": "GLOW_D3V3",''')
# C-12 fan high-side switch
sub(M, '''    D.IC(sh, "SM04B-SRSS-TB", {"1": "FAN_GND", "2": "V5_AUX", "3": "FAN_TACH", "4": "FAN_PWM_OD"}, nc=["5", "6"], prefix="J", value="FAN")
    D.IC(sh, "AO3400A", {"D": "FAN_GND", "G": "EXP_EN_FAN", "S": G}, prefix="Q", fields={"Op_I": 0.2, "Rated_I": 5.7})''',
    '''    D.IC(sh, "SM04B-SRSS-TB", {"1": G, "2": "V5_FAN", "3": "FAN_TACH", "4": "FAN_PWM_OD"}, nc=["5", "6"], prefix="J", value="FAN")
    D.IC(sh, "TPS22965DSGR", {"VIN": "V5_AUX", "ON": "EXP_EN_FAN", "VBIAS": "V5_AUX", "GND": G, "CT": "FAN_CT", "VOUT": "V5_FAN", "EP": G},
         fields={"Op_I": 0.2, "Rated_I": 6.0, "Note": "C-12: high-side fan switch; solid fan ground so the tach can't back-feed IO39"})
    D.C(sh, "C_1n_50V", "FAN_CT", G)
    D.C(sh, "C_1u_16V", "V5_FAN", G)
    D.v("V5_FAN", 5.5)''')
sub(M, '''    D.v("FAN_GND", 5.5)\n''', '')

# C-15 / C-16 Qi
Q = "blocks/qi.py"
sub(Q, 'nc=["CC1", "CC2", "DEBUG", "IO4", "IO7", "NC", "DM", "DP"],', 'nc=["CC1", "CC2", "IO4", "IO7", "NC", "DM", "DP"],')
sub(Q, '"BST2": "QI_BST2", "VIN": "V12_QI"},', '"BST2": "QI_BST2", "VIN": "V12_QI", "DEBUG": "QI_DEBUG_TX"},')
sub(Q, '"Note": "Needs factory firmware burn (JLCPCB listing). CC/DP/DM unused (fixed 12 V input)."})',
    '''"Note": "C-16: order PRE-PROGRAMMED (LCSC/JLC programming service, Injoinic 5 W firmware). CC/DP/DM unused."})
    D.TP(sh, "QI_DEBUG_TX", small=True)
    D.C(sh, "C_2n2_50V", "QI_VDET", G, fields={"Note": "C-15: static-FOD 2.2 nF on VDET (datasheet default). Rest of demod network: copy reference schematic (VERIFY)"})''')
sub(Q, '''    for n_ in ("QI_NTC", "QI_FOD", "QI_LED1", "QI_LED2", "QI_LED3", "QI_XI", "QI_XO", "QI_VDET"):''',
    '''    for n_ in ("QI_NTC", "QI_FOD", "QI_LED1", "QI_LED2", "QI_LED3", "QI_XI", "QI_XO", "QI_VDET", "QI_DEBUG_TX"):''')

# C-9 LoRa back-powering
L = "blocks/lora.py"
sub(L, '"P0.06": "LORA_TX", "P0.08": "LORA_RX",', '"P0.06": "LORA_TXR", "P0.08": "LORA_RXR",')
sub(L, '''    D.R(sh, "10k", "EXP_LORA_RST_N", "V3V3")''',
    '''    D.R(sh, "10k", "EXP_LORA_RST_N", V, fields={"Note": "C-9: pull-up to the node's own gated rail"})
    D.R(sh, "1k", "LORA_TX", "LORA_TXR", fields={"Note": "C-9: series R limits back-power from the ESP32 UART when V3V3_LORA is off"})
    D.R(sh, "1k", "LORA_RX", "LORA_RXR")''')
sub(L, '"RESET": "EXP_LORA_RST_N", "TX": "LORA_TX"},', '"RESET": "EXP_LORA_RST_N", "TX": "LORA_TXR"},')

# C-10 router reset pull-up in its own domain
sub("blocks/ethernet.py", '''    D.R(sh, "10k", "EXP_RTR_RST_N", "V3V3")''',
    '''    D.R(sh, "10k", "EXP_RTR_RST_N", V33, fields={"Note": "C-10: pull-up in the router/ETH domain, not always-on 3V3"})''')

# C-2 always-on buck EN floating (6 V abs-max)
sub("blocks/aux_power.py", '''        if en is None:
            D.R(sh, "100k", f"{t}_ENP", "VBAT", pkg="0603", fields={"Note": "always on (EN pull-up; floating also enables)"})
        else:''', '''        if en is None:
            u.conns.pop("EN")   # C-2: EN abs-max 6 V; floating enables via the internal pull-up current (datasheet)
            u.nc.add("EN")
        else:''')

# C-3 / C-13 / C-14 USB-A
UA = "blocks/usb_a.py"
sub(UA, '"HLED/PS/EN": "EXP_EN_USBA",', '"HLED/PS/EN": "USBA_EN_OD",')
sub(UA, '''    D.IC(sh, "MSA75-6R8M", {"1": "USBA_SW", "2": "USBA_VBUS"}, prefix="L", value="6.8uH 5A",
         fields={"Rated_I": 5.0, "Isat": 5.0, "Op_Irms": 1.5, "Op_Ipk": 2.0, "Note": "inductor value per IP6525S app note VERIFY"})''',
    '''    D.IC(sh, "SLO1365H220MTT", {"1": "USBA_SW", "2": "USBA_VBUS"}, prefix="L", value="22uH 6A",
         fields={"Rated_I": 6.0, "Isat": 12.0, "Op_Irms": 1.5, "Op_Ipk": 2.4, "Note": "C-3: 22 uH per IP6525S reference (100 kHz); 1.7 A p-p at 21 V in"})
    D.R(sh, "2.2", "USBA_SW", "USBA_SNB", pkg="0603", p_op=0.03, fields={"Note": "C-13: SW snubber ~2 ohm + 1 nF (reference design)"})
    D.C(sh, "C_1n_50V", "USBA_SNB", G)
    D.v("USBA_SNB", 21.0)
    D.IC(sh, "JBLM2101M025C058RTM100UF25V", {"1": "USBA_VBUS", "2": G}, prefix="C", value="100uF 25V polymer",
         fields={"Rated_V": 25, "Note": "C-13: solid output cap (~50 mOhm) per reference; pin 1 = + VERIFY"})
    D.IC(sh, "AO3400A", {"D": "USBA_EN_OD", "G": "EXP_USBA_DIS", "S": G}, prefix="Q",
         fields={"Note": "C-14: open-drain disable (pin 4 acts only when pulled low). Gate pulled up by default -> USB-A off"})
    D.v("USBA_EN_OD", 5.5)''')

# C-5 eFuse in stock package
P = "blocks/power_input.py"
sub(P, '''    D.IC(sh, "TPS26631PWPR", {''', '''    D.IC(sh, "TPS26631RGER", {''')
sub(P, '''        "OUT": vout, "EP": "GND"},''', '''        "OUT": vout, "EP": "GND"}, nc=["N.C"],''')
print("round-1 control/DFM patch applied")

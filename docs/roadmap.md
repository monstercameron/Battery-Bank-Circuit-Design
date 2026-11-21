---
layout: default
title: Roadmap
nav_order: 10
---

# Roadmap

## Status

Design in progress. Not reviewed, not laid out, not built. Details: [Status](status.html).

1. Schematic generated from Python (`hardware/gen`) with JLCPCB part lookups (`hardware/tools/jlc.py`).
2. Adversarial design-review loop; no open critical or major findings allowed before layout.
3. KiCad 10 layout, then JLCPCB BOM/CPL export.

## Open decisions

- **Control MCU:** ESP32-WROOM-32UE (U.FL for the metal case) is the working choice; confirm it.
- **Per-port power stage:** lock after the stock check; TPS26750 stock is low.
- **Router module:** confirm vendor, 2.5G HSGMII interoperability with the RTL8372N, and pinout.
- **Flashlight driver:** AL8860 limits it to 0.5 A; the reviewer decides on a larger driver.
- **Power-stage FETs:** 100 V parts still to be chosen.
- **PoE RJ45:** no 2.5G 802.3bt MagJack at LCSC; pick a candidate.

## Risks

- **Router module vendor confirmation** and sourcing (probably consigned or a module board).
- **PoE-rated 2.5G RJ45 sourcing.**
- **TPS26750 low JLCPCB stock** (4 needed per board).
- DR_Swap interop: some phones may refuse the data-role swap Ethernet needs.
- Pass-through charge termination with loads on the battery node.
- Thermal: four high-power ports in a small case; throttling must work if the fan fails.
- PD 3.3 compliance depends on vendor firmware updates.
- Cartridge connector carrying about 25 A through many swaps.
- Open firmware versus safety: every limit enforced in hardware.
- RF in a metal case, with several antennas needing separation.
- Qi coil heating nearby metal; needs a non-metal top and ferrite.
- PoE isolation (1500 V flyback, transformer, spacing).
- Four-port Ethernet density and unverified switch PHY integration.
- Short runtime when everything is on; the power allocator is essential.
- Feature creep: bring up and test each block on its own.
- Microphone last-time-buy notice; plan an alternate.

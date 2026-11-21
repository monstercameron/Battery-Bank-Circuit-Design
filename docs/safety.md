---
layout: default
title: Safety
nav_order: 4
---

# Safety

{: .warning }
> Design in progress and not reviewed. Do not build or charge a pack from these pages.

## The 3:1 policy

Every part that carries current or dissipates power is rated for at least 3x its worst-case operating current or power. The 3:1 buffer applies to **current, power and thermal capacity, not voltage**. Voltage uses standard derating (for example ceramic capacitors at 2x, MOSFET V_DS at 1.5x plus ringing). Where a standard makes 3:1 impossible (USB-C contacts, USB-A, PoE magnetics, IC internal switches), the exceptions table records what is done instead.

Examples: the Samsung 50S is rated 25 A, so design discharge is 8.3 A at most with an 8.0 A firmware limit; the 5 A DC jack is limited to 1.67 A (40 W at 24 V); junction temperature stays at least 40 C below Tj(max).

Full rules, tables and exceptions: [design-rules.md](design-rules.html).

## Battery and airline notes

- Pack: 5S1P Samsung 50S, 90 Wh, under the 100 Wh limit so it flies without airline approval.
- Protection: BQ77915 standalone protector (order the -00, -02 or -08 variants; avoid -04 and -13, which disable current and temperature protections), plus the BQ34Z100 fuel gauge and cell NTCs.
- The cartridge connector must carry about 25 A safely through many swaps. A poor connector is a fire risk and an open risk.
- Check current airline rules before travel.

## Hardware-enforced limits under open firmware

Firmware is open and can be replaced, so safety does not depend on it:

- BQ25756 ICHG and ILIM_HIZ resistors cap current; the effective limit is the lower of the pin setting and the register.
- BQ77915 over-current, over-voltage, under-voltage and temperature protection run in hardware.
- eFuse or load switch with power-good on every gated block.
- NTCs at connectors, stages, cells, LED and router, with thermal foldback.
- Review gate: no open critical or major findings before layout starts.

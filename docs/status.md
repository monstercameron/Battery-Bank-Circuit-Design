---
layout: default
title: Status
nav_order: 9
---

# Status

The first-pass schematic is complete for both the main board and the battery cartridge. Adversarial review round 1 is in progress. Nothing is laid out or built yet.

## Done

- Requirements, decisions and the 3:1 safety policy (current, power and thermal; not voltage).
- Design rules, power budget, chip metadata and JLCPCB rules; datasheets downloaded and indexed.
- Generator framework: helpers, KiCad writer, symbol library access, passive picker, design checks.
- All 13 main-board blocks generated: USB-C port (x4), power input, PoE, battery interface, aux rails, Ethernet switch and router connector, MCU, LoRa, audio, lighting, DC out, USB-A and Qi.
- The battery cartridge is a separate project (`hardware/kicad_cartridge/`): BQ7791500 protector, BQ34Z100-G1 gauge, STS2250 fuse, back-to-back discharge/charge FETs and a presence loop that hibernates a removed cartridge.

## In progress

- **Review round 1.** Three Claude adversarial reviewers (power/safety, high-speed/networking, control/radios/DFM) and an independent OpenAI Codex gpt-6.2-astra reviewer, run read-only through the Codex CLI. Reports go to `hardware/review/`. See [Review process](review-process.html).

## Pending

- Repair of the round 1 findings, then review round 2, repeated until no critical or major findings remain.
- Layout in KiCad 10, then JLCPCB BOM/CPL export and ordering.
- Bring-up of each block on its own, then all together.
- Open decisions and risks: see [Roadmap](roadmap.html).

## Latest generated build check

| Item | Main board | Cartridge |
|---|---|---|
| Schematic sheets | 16 | 1 project |
| Parts | 1,115 | 60 |
| BOM lines | 159 | n/a |
| Design check | 0 errors, 3 warnings | 0 errors |
| KiCad ERC | 21 warnings, no errors | n/a |

- **Design check warnings (3):** consigned parts with no LCSC number: the RJ45 PoE MagJack, the router module and the PoE transformer.
- **Accepted 3:1 exceptions** are listed as INFO lines, not errors: USB-C 5 A contacts, the USB-A 2 A connector, 802.3bt per-pair current and the TPS2373 internal hot-swap FET. See [design rules](design-rules.html) section 1.4.
- **KiCad ERC warnings (21):** all library-copy mismatches on 2-pin EasyEDA inductor and jack symbols. They are cosmetic and still being investigated.

Open VERIFY items in the code: PoE flyback compensation, turns ratio and snubber; IP6826 crystal and demodulation network; IP6525S enable behaviour; TPS56A37 FB/MODE; RTL8156BG RSET; router module pinout. These numbers change with every build; see the [Dev log](devlog.html).

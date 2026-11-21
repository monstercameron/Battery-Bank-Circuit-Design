# JLCPCB fabrication and assembly rules (as applied to this board)

Source pages, read 2026-11-21:
- https://jlcpcb.com/capabilities/pcb-capabilities
- https://jlcpcb.com/capabilities/pcb-assembly-capabilities

Re-check before ordering; JLCPCB updates these.

## Board / stackup choices
| Item | JLCPCB capability | Our choice |
|---|---|---|
| Layers | 1–32; controlled impedance on 4+ layers, ±10% | **6 layers**, impedance-controlled (USB 3 90 Ω diff, Ethernet MDI 100 Ω diff, SerDes 100 Ω diff, RF 50 Ω) |
| Thickness | FR4 0.4/0.6/0.8/1.0/1.2/1.6/2.0 mm | **1.6 mm** |
| Copper | Multilayer outer 1 or 2 oz; inner 0.5 (default) / 1 / 2 oz | **2 oz outer, 1 oz inner** (power). Note 2 oz raises minimum track/space to 0.15/0.15 mm on outer layers |
| Surface finish | HASL not available on 6+ layers | **ENIG** (also needed for fine-pitch QFN/0.35 mm pitch) |
| Via-in-pad | Epoxy-filled and capped, default on 6+ layers, 0.15–0.55 mm | Use under QFN thermal pads and in fine-pitch fan-out |
| Assembly | Standard PCBA: single and double sided, 70×70–460×500 mm single board, ≥0.35 mm IC pitch, 0201 minimum; fiducials and edge rails required | **Standard PCBA**, SMT on **top side only** wherever possible (one stencil, one reflow pass, cheaper). THT parts (connectors) by wave/selective solder |

## Geometry rules (KiCad design-rule values, set in the .kicad_pro file)
| Rule | JLCPCB minimum | Our rule (margin) |
|---|---|---|
| Track / space, 1 oz inner | 0.09 / 0.09 mm | **0.10 / 0.10 mm** |
| Track / space, 2 oz outer | 0.15 / 0.15 mm | **0.16 / 0.16 mm** |
| Via drill / diameter | 0.15 / 0.25 mm (0.2 mm drill preferred, cheaper) | **0.30 / 0.55 mm** standard; **0.20 / 0.40 mm** for fine pitch only |
| Via-to-via (hole to hole) | 0.2 mm | 0.25 mm |
| PTH annular ring (multilayer, 1 oz) | 0.15 mm absolute, 0.20 mm recommended | **0.20 mm**; **0.254 mm** on 2 oz layers |
| Pad to track | 0.1 mm | 0.15 mm |
| SMD pad to pad (different nets) | 0.15 mm | 0.15 mm (footprint-defined) |
| Via hole to track | 0.2 mm | 0.2 mm |
| PTH to track | 0.28 mm (0.35 mm recommended) | **0.35 mm** |
| Inner-layer via-to-copper / PTH-to-copper | 0.2 / 0.3 mm | 0.25 / 0.35 mm |
| Copper to routed board edge | 0.2 mm | **0.5 mm** (1.0 mm for high-voltage/power nets) |
| Solder mask bridge, 2 oz | 0.20 mm | 0.20 mm |
| Solder mask clearance to neighbouring trace | 0.09 mm | 0.1 mm |
| Silkscreen line width / text height | ≥0.15 mm / ≥1.0 mm | **0.15 mm / 1.0 mm** (refdes), 1.27 mm labels |
| Pad to silkscreen | 0.15 mm | 0.2 mm |
| Plated slot width (multilayer) | 0.35 mm (length ≥2× width) | for USB-C/USB-A shell legs per footprint |
| Min NPTH | 0.5 mm | per footprint |

## Panel / assembly
- **Panel rails:** 5 mm tooling edges, 2 mm tooling holes, 1 mm fiducials centred 3.85 mm from the panel edge (JLCPCB's SMT guidance).
- **Board fiducials:** 3 global fiducials on the board as well, 1 mm copper with 2 mm mask opening, plus local fiducials near the 0.35–0.5 mm pitch QFNs (RTL8156BG, RTL8372N).
- **X-ray:** QFN/LGA/BGA parts trigger automatic X-ray inspection (cost included).
- **Part classes:** use **Basic / Preferred** parts for every passive where one meets the 3:1 rule, because each unique **Extended** part adds a loading fee. Keep a small number of unique passive values.
- **Placement:**
  - Keep components ≥0.5 mm apart (≥1 mm around tall parts and connectors for the AOI camera and nozzle access).
  - Keep the same orientation for polarized parts where possible.
  - Pin 1 marked on silkscreen outside the body.
- **Programming:** JLCPCB can pre-program some MCUs on request (HEX/BIN plus the programming interface on the board). We plan in-system programming through debug pads instead, so it's not required.
- **Mixed components:** JLCPCB uses reflow for SMD and wave for THT. Unused through-holes are protected, so DNP debug headers stay open.

# Peaky 8-bit v2.0 — PCB Production Files

Generated from KiCad using the PCBWay plugin on 2026-06-01.

## Files
- Wireless_1.kicad_pcb.zip — Gerber files
- BOM_Wireless_1.kicad_pcb.xls — Full BOM (all components)
- Centroid_Wireless_1_kicad_pcb_revised.zip — Pick-and-place file (C1, C2, D1 only)

## Important: BOM includes ALL components

The BOM exported by the KiCad plugin contains every component on the board.
If you are ordering SMT assembly, you probably only need the following
soldered by the manufacturer:

- C1 (0.1uF, 0603)
- C2 (10uF, 0603)
- D1 (SS14, SMA)

All other components (U1, SW1-6, J1, BT1) are through-hole and intended
to be hand-soldered. Remove them from the BOM before submitting your
assembly order, or specify to your manufacturer which components to assemble.
# Peaky 8-bit v2.2 (Wireless, Hot-swap) — PCB Files

Generated from KiCad on 2026-07-18.
The same PCB is used for both the left and right halves (order 2 boards per keyboard).

## Board specs

| Item | Value |
|---|---|
| Size | 37.55 × 114.97 mm |
| Layers | 2 |
| Thickness | 1.6 mm |

## Files

- `Gerber_wireless_v2.2_0718/` — Gerber and drill files (zip this folder when ordering)
- `bom.csv` — Component list exported from KiCad (with LCSC part numbers for the SMD parts)
- `positions.csv` — Pick-and-place / CPL data (component centers and rotation)
- `designators.csv` — Designator list

## BOM (per board)

Multiply quantities by 2 for a full keyboard (left + right).

| Ref | Part | Qty | Mounting | Source / Notes |
|---|---|---|---|---|
| C1 | Capacitor 0.1 µF, 0603 | 1 | SMD (PCBA) | LCSC [C14663](https://www.lcsc.com/product-detail/C14663.html) |
| C2 | Capacitor 10 µF, 0603 | 1 | SMD (PCBA) | LCSC [C19702](https://www.lcsc.com/product-detail/C19702.html) |
| D1 | Schottky diode SS14, SMA | 1 | SMD (PCBA) | LCSC [C2480](https://www.lcsc.com/product-detail/C2480.html) |
| U1 | Seeed Studio XIAO nRF52840 (Plus) | 1 | Hand-solder | [Seeed Studio](https://www.seeedstudio.com/XIAO-p-5928.html) |
| J1 | DC-DC boost converter module | 1 | Hand-solder | [Akizuki 116116](https://akizukidenshi.com/catalog/g/g116116/) — soldered into the 3-pin through-holes |
| BT1 | AAA battery holder (1 cell) | 1 | Hand-solder | [Akizuki 102670](https://akizukidenshi.com/catalog/g/g102670/) — leads soldered into the 2-pin through-holes |
| SW1–SW4 | Kailh MX hot-swap socket | 4 | Hand-solder | For Cherry MX compatible switches |
| SW5 | Slide switch, SPDT (power) | 1 | Hand-solder | 2.54 mm pitch (e.g. Würth WS-SLTV) |
| SW6 | Tact switch, 6 mm (reset) | 1 | Hand-solder | Optional |

## Ordering the PCB with SMT assembly

The Gerber files are designed so that **C1, C2 and D1 are assembled by the PCB
manufacturer** (e.g. JLCPCB PCBA). Upload the Gerber zip, then `bom.csv` and
`positions.csv` for assembly.

All other components are through-hole and meant to be hand-soldered. Exclude
them from the assembly order (no LCSC part number is listed for them).

## Other parts (per keyboard)

| Part | Qty | Notes |
|---|---|---|
| Key switches (Cherry MX compatible) | 8 | 4 per hand |
| Keycaps (Cherry MX compatible) | 8 | Keycap STL available in [`/case`](../../case) |
| 3D-printed case | 2 | STL: [`case/P8_STL_v2.2_26-0718_hotswap`](../../case/P8_STL_v2.2_26-0718_hotswap) |
| M3 × 20 mm screws + nuts | 8 | 4 per hand |
| AAA alkaline batteries (1.5 V) | 2 | 1 per hand. Rechargeable cells not recommended |

## Tools / requirements

- Soldering iron and solder
- USB Type-C **data** cable (for flashing firmware)
- 3D printer or a printing service
- Firmware: see the [top-level README](../../README.md)

#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Binary Chords v0.3 keymap generator for ZMK firmware.

Reads a CSV file describing the 256-pattern keymap and emits a complete
ZMK keymap file (peaky8bit.keymap) with combos, macros, and layers.

Usage:
    uv run gen_keymap.py keymap_v03.csv > peaky8bit.keymap

CSV format (header row required):
    hex,layer1,with_shift,with_ctrl
    0x21,write:ka,write:ga,
    0x32,write:si,write:zi,
    ...

Action syntax (in CSV cells):
    write:abc      -> macro that taps each character of "abc" (e.g. write:ka -> &kp K, &kp A)
    key:XXX        -> single HID key (e.g. key:TAB, key:BSPC, key:RET, key:F1, key:UP)
    keys:K1+K2     -> simultaneous press (e.g. keys:LSHIFT+TAB)
    mod:Shift      -> arm a modifier layer (Shift / Ctrl / Alt / Shift+Ctrl / Shift+Alt / Ctrl+Alt / Shift+Ctrl+Alt)
    ime            -> IME on/off toggle (sends INT5 = hankaku/zenkaku)
    (empty)        -> no action
"""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass, field
from pathlib import Path

# -----------------------------------------------------------------------------
# Key-position to bit mapping (matches the v0.3 spec)
#
#   Left  (central):    pos 0=bit7, pos 1=bit6, pos 2=bit5, pos 3=bit4
#   Right (peripheral): pos 4=bit3, pos 5=bit2, pos 6=bit1, pos 7=bit0
# -----------------------------------------------------------------------------
BIT_TO_POS = {
    7: 0, 6: 1, 5: 2, 4: 3,   # left hand: bit7..bit4 -> pos 0..3
    3: 4, 2: 5, 1: 6, 0: 7,   # right hand: bit3..bit0 -> pos 4..7
}

def hex_to_positions(hex_val: int) -> list[int]:
    """Convert an 8-bit chord value to the list of ZMK key positions to press."""
    positions = []
    for bit in range(8):
        if hex_val & (1 << bit):
            positions.append(BIT_TO_POS[bit])
    return sorted(positions)


# -----------------------------------------------------------------------------
# Layer assignment
# -----------------------------------------------------------------------------
LAYER_DEFAULT = 0
LAYER_SHIFT = 1
LAYER_CTRL = 2
LAYER_ALT = 3
LAYER_SHIFT_CTRL = 4
LAYER_SHIFT_ALT = 5
LAYER_CTRL_ALT = 6
LAYER_SHIFT_CTRL_ALT = 7  # reserved for future

LAYER_NAMES = {
    LAYER_DEFAULT: "default_layer",
    LAYER_SHIFT: "shift_armed_layer",
    LAYER_CTRL: "ctrl_armed_layer",
    LAYER_ALT: "alt_armed_layer",
    LAYER_SHIFT_CTRL: "shift_ctrl_armed_layer",
    LAYER_SHIFT_ALT: "shift_alt_armed_layer",
    LAYER_CTRL_ALT: "ctrl_alt_armed_layer",
    LAYER_SHIFT_CTRL_ALT: "shift_ctrl_alt_armed_layer",
}

MOD_TO_LAYER = {
    "Shift":            LAYER_SHIFT,
    "Ctrl":             LAYER_CTRL,
    "Alt":              LAYER_ALT,
    "Shift+Ctrl":       LAYER_SHIFT_CTRL,
    "Shift+Alt":        LAYER_SHIFT_ALT,
    "Ctrl+Alt":         LAYER_CTRL_ALT,
    "Shift+Ctrl+Alt":   LAYER_SHIFT_CTRL_ALT,
}


# -----------------------------------------------------------------------------
# Character to ZMK keycode mapping (for `write:` actions)
#
# write:ka -> &kp K, &kp A
# These are HID keycodes; the host's IME handles romaji-to-kana conversion.
# -----------------------------------------------------------------------------
CHAR_TO_KP = {
    # Letters (lowercase; ZMK &kp X is case-insensitive at the HID layer,
    # capital case requires LSHIFT modifier which we add explicitly)
    "a": "A", "b": "B", "c": "C", "d": "D", "e": "E", "f": "F", "g": "G",
    "h": "H", "i": "I", "j": "J", "k": "K", "l": "L", "m": "M", "n": "N",
    "o": "O", "p": "P", "q": "Q", "r": "R", "s": "S", "t": "T", "u": "U",
    "v": "V", "w": "W", "x": "X", "y": "Y", "z": "Z",
    # Digits
    "0": "N0", "1": "N1", "2": "N2", "3": "N3", "4": "N4",
    "5": "N5", "6": "N6", "7": "N7", "8": "N8", "9": "N9",
    # Symbols (without shift)
    "-": "MINUS",
    "=": "EQUAL",
    "[": "LBKT",
    "]": "RBKT",
    "\\": "BSLH",
    ";": "SEMI",
    "'": "SQT",
    ",": "COMMA",
    ".": "DOT",
    "/": "FSLH",
    "`": "GRAVE",
    " ": "SPACE",
}

# Symbols that require LSHIFT modifier
CHAR_TO_KP_SHIFTED = {
    "!": "EXCL",      # Shift+1
    "@": "AT",        # Shift+2
    "#": "HASH",      # Shift+3
    "$": "DLLR",      # Shift+4
    "%": "PRCNT",     # Shift+5
    "^": "CARET",     # Shift+6
    "&": "AMPS",      # Shift+7
    "*": "STAR",      # Shift+8
    "(": "LPAR",      # Shift+9
    ")": "RPAR",      # Shift+0
    "_": "UNDER",     # Shift+-
    "+": "PLUS",      # Shift+=
    "{": "LBRC",      # Shift+[
    "}": "RBRC",      # Shift+]
    "|": "PIPE",      # Shift+\
    ":": "COLON",     # Shift+;
    '"': "DQT",       # Shift+'
    "<": "LT",        # Shift+,
    ">": "GT",        # Shift+.
    "?": "QMARK",     # Shift+/
    "~": "TILDE",     # Shift+`
}

def char_to_kp_binding(ch: str) -> str:
    """Return a ZMK binding fragment for a single character."""
    if ch in CHAR_TO_KP:
        return f"&kp {CHAR_TO_KP[ch]}"
    if ch in CHAR_TO_KP_SHIFTED:
        return f"&kp {CHAR_TO_KP_SHIFTED[ch]}"
    if ch.isupper() and ch.lower() in CHAR_TO_KP:
        # e.g. 'A' -> shifted 'a' -> LS(A)
        return f"&kp LS({CHAR_TO_KP[ch.lower()]})"
    raise ValueError(f"Unmapped character: {ch!r}")


# -----------------------------------------------------------------------------
# Action parsing
# -----------------------------------------------------------------------------
@dataclass
class Action:
    """Parsed action from a CSV cell."""
    kind: str       # "write" | "key" | "keys" | "mod" | "ime" | "none"
    payload: str    # "ka" / "TAB" / "LSHIFT+TAB" / "Shift" / ""

def parse_action(cell: str) -> Action:
    cell = cell.strip()
    if not cell or cell.lower() in ("none", "(none)"):
        return Action("none", "")
    if cell.startswith("write:"):
        return Action("write", cell[len("write:"):])
    if cell.startswith("key:"):
        return Action("key", cell[len("key:"):])
    if cell.startswith("keys:"):
        return Action("keys", cell[len("keys:"):])
    if cell.startswith("mod:"):
        return Action("mod", cell[len("mod:"):])
    if cell == "ime":
        return Action("ime", "")
    raise ValueError(f"Unrecognised action: {cell!r}")


# -----------------------------------------------------------------------------
# Macro generation
# -----------------------------------------------------------------------------
@dataclass
class Macro:
    name: str               # e.g. m_h_21
    bindings: list[str]     # list of "&kp K", "&kp A" etc.

def macro_for_action(action: Action, name: str, return_to_default: bool) -> Macro | None:
    """Build a macro for a given action. Returns None if action is 'none'."""
    bindings: list[str] = []

    if action.kind == "none":
        return None

    elif action.kind == "write":
        for ch in action.payload:
            bindings.append(char_to_kp_binding(ch))

    elif action.kind == "key":
        bindings.append(f"&kp {action.payload}")

    elif action.kind == "keys":
        # keys:LSHIFT+TAB -> single &kp LS(TAB)
        parts = action.payload.split("+")
        if len(parts) == 2 and parts[0] in ("LSHIFT", "RSHIFT"):
            bindings.append(f"&kp LS({parts[1]})")
        elif len(parts) == 2 and parts[0] in ("LCTRL", "RCTRL"):
            bindings.append(f"&kp LC({parts[1]})")
        elif len(parts) == 2 and parts[0] in ("LALT", "RALT"):
            bindings.append(f"&kp LA({parts[1]})")
        elif len(parts) == 2 and parts[0] in ("LGUI", "RGUI"):
            bindings.append(f"&kp LG({parts[1]})")
        else:
            # Fallback: macro_press all, macro_release all
            raise ValueError(f"Complex keys: not yet supported: {action.payload}")

    elif action.kind == "mod":
        # mod actions don't generate a regular macro; they're handled as &to <layer>
        # directly in combo bindings. Return None.
        return None

    elif action.kind == "ime":
        # MS-IME on Windows: International5 (半角/全角)
        bindings.append("&kp INT5")

    if return_to_default:
        bindings.append("&to 0")

    return Macro(name=name, bindings=bindings)


# -----------------------------------------------------------------------------
# Top-level keymap generation
# -----------------------------------------------------------------------------
@dataclass
class GeneratedKeymap:
    macros: list[Macro] = field(default_factory=list)
    # combos[(positions, layer)] = binding
    combos: dict[tuple[tuple[int, ...], int], str] = field(default_factory=dict)

    def add_macro(self, m: Macro):
        # de-dupe by name
        if not any(existing.name == m.name for existing in self.macros):
            self.macros.append(m)

    def add_combo(self, positions: list[int], layer: int, binding: str, name_hint: str = ""):
        key = (tuple(positions), layer)
        if key in self.combos:
            sys.stderr.write(f"WARNING: combo collision at positions={positions} layer={layer}\n")
        self.combos[key] = binding


def generate(rows: list[dict]) -> GeneratedKeymap:
    g = GeneratedKeymap()

    # Pre-pass: figure out which mod actions exist so we can route to layers.

    for row in rows:
        hex_str = row["hex"].strip()
        if not hex_str:
            continue
        hex_val = int(hex_str, 16)
        positions = hex_to_positions(hex_val)

        if len(positions) < 2:
            # Single-key chord - skip (cannot be a ZMK combo)
            sys.stderr.write(f"SKIP: 0x{hex_val:02X} requires only {len(positions)} key(s); "
                             f"ZMK combos require 2+\n")
            continue

        layer1 = parse_action(row.get("layer1", ""))
        with_shift = parse_action(row.get("with_shift", ""))
        with_ctrl = parse_action(row.get("with_ctrl", ""))

        # --- layer1 (L0) ---
        if layer1.kind == "mod":
            # mod arm: &to <layer>
            target_layer = MOD_TO_LAYER[layer1.payload]
            g.add_combo(positions, LAYER_DEFAULT, f"&to {target_layer}")
        elif layer1.kind != "none":
            macro_name = f"m_h_{hex_val:02x}"
            macro = macro_for_action(layer1, macro_name, return_to_default=False)
            if macro:
                g.add_macro(macro)
                g.add_combo(positions, LAYER_DEFAULT, f"&{macro_name}")

        # --- with_shift (L1) ---
        if with_shift.kind != "none":
            if with_shift.kind == "mod":
                raise ValueError(f"with_shift cannot be mod (at 0x{hex_val:02X})")
            macro_name = f"m_s_{hex_val:02x}"
            macro = macro_for_action(with_shift, macro_name, return_to_default=True)
            if macro:
                g.add_macro(macro)
                g.add_combo(positions, LAYER_SHIFT, f"&{macro_name}")

        # --- with_ctrl (L2) ---
        if with_ctrl.kind != "none":
            if with_ctrl.kind == "mod":
                raise ValueError(f"with_ctrl cannot be mod (at 0x{hex_val:02X})")
            macro_name = f"m_c_{hex_val:02x}"
            macro = macro_for_action(with_ctrl, macro_name, return_to_default=True)
            if macro:
                g.add_macro(macro)
                g.add_combo(positions, LAYER_CTRL, f"&{macro_name}")

    # Always-on: Esc (0x0E) on every armed layer should cancel back to L0.
    esc_positions = hex_to_positions(0x0E)
    for armed in (LAYER_SHIFT, LAYER_CTRL, LAYER_ALT,
                  LAYER_SHIFT_CTRL, LAYER_SHIFT_ALT, LAYER_CTRL_ALT):
        # Only add if not already defined by the CSV
        key = (tuple(esc_positions), armed)
        if key not in g.combos:
            g.add_combo(esc_positions, armed, "&to 0")

    return g


# -----------------------------------------------------------------------------
# Emit ZMK keymap DSL
# -----------------------------------------------------------------------------
HEADER = """\
// AUTO-GENERATED by gen_keymap.py from binary-chords-spec-v0.3 CSV.
// Do not edit by hand. Regenerate with `uv run gen_keymap.py keymap.csv > peaky8bit.keymap`.

#include <behaviors.dtsi>
#include <dt-bindings/zmk/keys.h>
#include <dt-bindings/zmk/bt.h>

/ {
"""

FOOTER = """\
};
"""


def emit(g: GeneratedKeymap) -> str:
    out: list[str] = [HEADER]

    # ---- macros ----
    out.append("    macros {")
    for m in g.macros:
        out.append(f"        {m.name}: {m.name} {{")
        out.append(f'            label = "{m.name.upper()}";')
        out.append(f'            compatible = "zmk,behavior-macro";')
        out.append(f"            #binding-cells = <0>;")
        bindings_str = ", ".join(f"<{b}>" for b in m.bindings)
        out.append(f"            bindings = {bindings_str};")
        out.append(f"        }};")
    out.append("    };")
    out.append("")

    # ---- combos ----
    out.append("    combos {")
    out.append('        compatible = "zmk,combos";')
    # sort by layer then by positions for stable diff
    sorted_keys = sorted(g.combos.keys(), key=lambda k: (k[1], k[0]))
    for key in sorted_keys:
        positions, layer = key
        binding = g.combos[key]
        positions_str = " ".join(str(p) for p in positions)
        combo_name = f"c_l{layer}_{'_'.join(str(p) for p in positions)}"
        out.append(f"        {combo_name} {{")
        out.append(f"            timeout-ms = <100>;")
        out.append(f"            key-positions = <{positions_str}>;")
        out.append(f"            layers = <{layer}>;")
        out.append(f"            bindings = <{binding}>;")
        out.append(f"        }};")
    out.append("    };")
    out.append("")

    # ---- keymap layers ----
    out.append("    keymap {")
    out.append('        compatible = "zmk,keymap";')
    # L0: a/b/c/d/1/2/3/4 (debug-friendly base)
    out.append("""\
        default_layer {
            bindings = <
                &kp A   &kp B   &kp C   &kp D
                &kp N1  &kp N2  &kp N3  &kp N4
            >;
        };""")
    # L1..L7: all &none (only combos work in armed layers)
    for layer_id in range(1, 8):
        out.append(f"""\
        {LAYER_NAMES[layer_id]} {{
            bindings = <
                &none  &none  &none  &none
                &none  &none  &none  &none
            >;
        }};""")
    out.append("    };")

    out.append(FOOTER)
    return "\n".join(out)


# -----------------------------------------------------------------------------
# Validation / diagnostics
# -----------------------------------------------------------------------------
def diagnose(g: GeneratedKeymap) -> None:
    """Print combo count per key position (helps size CONFIG_ZMK_COMBO_MAX_COMBOS_PER_KEY)."""
    per_key: dict[int, int] = {p: 0 for p in range(8)}
    for (positions, _layer) in g.combos.keys():
        for p in positions:
            per_key[p] += 1

    sys.stderr.write("\n=== Diagnostics ===\n")
    sys.stderr.write(f"Total macros: {len(g.macros)}\n")
    sys.stderr.write(f"Total combos: {len(g.combos)}\n")
    sys.stderr.write("Combos involving each key position:\n")
    for pos, count in per_key.items():
        sys.stderr.write(f"  pos {pos}: {count}\n")
    sys.stderr.write(f"Max combos sharing one key: {max(per_key.values())}\n")
    sys.stderr.write(f"-> CONFIG_ZMK_COMBO_MAX_COMBOS_PER_KEY should be >= {max(per_key.values())}\n")


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main():
    if len(sys.argv) != 2:
        sys.stderr.write("Usage: gen_keymap.py <keymap.csv>\n")
        sys.exit(1)

    csv_path = Path(sys.argv[1])
    if not csv_path.exists():
        sys.stderr.write(f"CSV not found: {csv_path}\n")
        sys.exit(1)

    with csv_path.open() as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    g = generate(rows)
    diagnose(g)

    sys.stdout.write(emit(g))


if __name__ == "__main__":
    main()

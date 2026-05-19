# Binary Chords Keymap Specification v0.3

**改訂日:** 2026-05-19
**v0.2からの主要変更点:**
- キーマップ配置を最新CSV準拠に更新（0x11からかな開始）
- modifier系の割り当てを変更（ZMK標準combos互換のため、すべて2キー以上のchordに変更）
- ZMK実装方針（レイヤー切替方式）を追記
- ローマ字シーケンスを訓令式ベースに統一（Python版custom0405_code.py準拠）

---

## 1. 概要

Binary Chordsは、4キー×2基板（左右）の合計8キーを使用し、各キーの押下状態を1bitとして扱うことで、1回のchord入力で最大256パターン（2^8）の出力を表現するキーボード入力方式である。

**bit配置:**
- 左基板: bit 7-4（MSB側、bit7=左SW1）
- 右基板: bit 3-0（LSB側、bit3=右SW1、bit0=右SW4）

**入力単位:** chord（8キーのうち押下したキーを同時に離した瞬間に確定）

**出力種別:**
- **write:** ローマ字シーケンス送信（IMEがかな変換）
- **key:** 単一HIDキーコード送信
- **keys:** 複数HIDキー同時押下
- **mod:** modifier arm（次のchordを修飾）
- **ime:** IME On/Off
- **None:** 未割り当て

---

## 2. レイヤー構造（ZMK実装）

modifier armは状態機械として表現される。ZMK実装では以下の7レイヤーで管理する：

| レイヤー | 用途 | 遷移元 |
|---|---|---|
| L0 | default（通常） | - |
| L1 | Shift armed | L0からShift arm発火 |
| L2 | Ctrl armed | L0からCtrl arm発火 |
| L3 | Alt armed | L0からAlt arm発火 |
| L4 | Shift+Ctrl armed | L0からShift+Ctrl arm発火 |
| L5 | Shift+Alt armed | L0からShift+Alt arm発火 |
| L6 | Ctrl+Alt armed | L0からCtrl+Alt arm発火 |

**遷移ルール:**
- armed状態でchordを送信すると、自動的にL0に復帰する
- Esc（0x0E）でarmedレイヤーからL0に復帰（キャンセル）
- armed状態の重複は許可しない（Shift armed中にCtrl armedはできない）

---

## 3. modifier系の新割り当て（v0.2からの変更点）

v0.2ではmodifier系を0x01〜0x08（右手単独キーが多い）に割り当てていたが、ZMK標準combosは2キー以上のchord前提のため、以下に変更した：

| bit値 | 物理キー | 意味 |
|---|---|---|
| **0x88** = `1000 1000` | 左SW1 + 右SW1 | **Shift+** |
| **0x84** = `1000 0100` | 左SW1 + 右SW2 | **Ctrl+** |
| **0x82** = `1000 0010` | 左SW1 + 右SW3 | **Alt+** |
| **0x8C** = `1000 1100` | 左SW1 + 右SW1 + 右SW2 | **Shift+Ctrl+** |
| **0x8A** = `1000 1010` | 左SW1 + 右SW1 + 右SW3 | **Shift+Alt+** |
| **0x86** = `1000 0110` | 左SW1 + 右SW2 + 右SW3 | **Ctrl+Alt+** |
| **0x8E** = `1000 1110` | 左SW1 + 右SW1 + 右SW2 + 右SW3 | **Shift+Ctrl+Alt+** |

**論理性:**
- 左SW1（bit7=「左の親指」）を押すと「modifier mode」
- 右手のbit値で modifier の組み合わせを指定：
  - 右SW1（bit3） = Shiftフラグ
  - 右SW2（bit2） = Ctrlフラグ
  - 右SW3（bit1） = Altフラグ
- 上記の OR で複合 modifier を表現

**元の0x01〜0x08は予約**（将来のメディアキー、マウス操作等のために確保）。

---

## 4. ローマ字表記スタイル

Python版（custom0405_code.py）に準拠。**訓令式ベース、最短入力数優先**。

| かな | ローマ字 | 備考 |
|---|---|---|
| し / じ | si / zi | 訓令式 |
| ち / ぢ | ti / di | 訓令式 |
| つ / づ / っ | tu / du / xtu | 訓令式 |
| ふ / ぶ / ぷ | hu / bu / pu | 訓令式 |
| ん | nn | 後続文字混同回避のため2文字 |
| を | wo | |
| ゃゅょゎ | xya / xyu / xyo / xwa | x接頭辞 |
| ぁぃぅぇぉ | xa / xi / xu / xe / xo | x接頭辞 |

**前提:** Windows MS-IME のローマ字入力モード（または同等の動作をするGoogle日本語入力等）。

---

## 5. キーマップ表（256パターン）

凡例:
- `write:xxx` = 文字列xxxをローマ字シーケンスとして送信
- `key:XXX` = HIDキーコードXXXを単発送信
- `keys:K1+K2` = 複数キー同時押下
- `mod:Shift` = Shift armedレイヤーへ遷移
- `ime` = IME On/Off切替
- `(None)` = 未割り当て

### 0x00 - 0x0F（システム・制御）

| Hex | bit | layer1 | withShift | withCtrl | 備考 |
|---|---|---|---|---|---|
| 0x00 | `0000 0000` | (None) | (None) | (None) | 何も押されていない |
| 0x01-0x08 | - | (reserved) | (reserved) | (reserved) | v0.3で予約 |
| 0x09 | `0000 1001` | key:TAB | | | |
| 0x0A | `0000 1010` | key:LGUI | | | superkey/Windowsキー |
| 0x0B | `0000 1011` | key:BSPC | | | BackSpace |
| 0x0C | `0000 1100` | key:SPACE | | | |
| 0x0D | `0000 1101` | key:RET | | | Enter |
| 0x0E | `0000 1110` | key:ESC | | | armed状態ならキャンセル |
| 0x0F | `0000 1111` | key:DEL | | | Delete |

### 0x10 - 0x1F（数字1・あ行・記号）

| Hex | bit | layer1 | withShift | withCtrl |
|---|---|---|---|---|
| 0x10 | `0001 0000` | write:1 | key:F1 | |
| 0x11 | `0001 0001` | write:a | | write:xa |
| 0x12 | `0001 0010` | write:i | | write:xi |
| 0x13 | `0001 0011` | write:u | | write:xu |
| 0x14 | `0001 0100` | write:e | | write:xe |
| 0x15 | `0001 0101` | write:o | | write:xo |
| 0x16 | `0001 0110` | write:! | write:! | |
| 0x17 | `0001 0111` | write:, | write:, | |
| 0x18 | `0001 1000` | write:. | write:. | |
| 0x19 | `0001 1001` | write:? | write:? | |
| 0x1A | `0001 1010` | write:~ | write:~ | |
| 0x1B | `0001 1011` | write:@ | write:@ | |
| 0x1C | `0001 1100` | write:_ | write:_ | |
| 0x1D | `0001 1101` | write:" | write:" | |
| 0x1E | `0001 1110` | write:& | write:& | |
| 0x1F | `0001 1111` | ime | ime | |

### 0x20 - 0x2F（数字2・か行・記号）

| Hex | bit | layer1 | withShift | withCtrl |
|---|---|---|---|---|
| 0x20 | `0010 0000` | write:2 | key:F2 | |
| 0x21 | `0010 0001` | write:ka | write:ga | |
| 0x22 | `0010 0010` | write:ki | write:gi | |
| 0x23 | `0010 0011` | write:ku | write:gu | |
| 0x24 | `0010 0100` | write:ke | write:ge | |
| 0x25 | `0010 0101` | write:ko | write:go | |
| 0x26 | `0010 0110` | write:# | write:# | |
| 0x27 | `0010 0111` | write:$ | write:$ | |
| 0x28 | `0010 1000` | write:% | write:% | |
| 0x29 | `0010 1001` | (None) | | |
| 0x2A | `0010 1010` | write:' | write:' | |
| 0x2B | `0010 1011` | (None) | | |
| 0x2C | `0010 1100` | write:^ | write:^ | |
| 0x2D | `0010 1101` | write:` | write:` | |
| 0x2E | `0010 1110` | write:\\ | write:\\ | |
| 0x2F | `0010 1111` | (None) | | |

### 0x30 - 0x3F（数字3・さ行・記号）

| Hex | bit | layer1 | withShift | withCtrl |
|---|---|---|---|---|
| 0x30 | `0011 0000` | write:3 | key:F3 | |
| 0x31 | `0011 0001` | write:sa | write:za | |
| 0x32 | `0011 0010` | write:si | write:zi | |
| 0x33 | `0011 0011` | write:su | write:zu | |
| 0x34 | `0011 0100` | write:se | write:ze | |
| 0x35 | `0011 0101` | write:so | write:zo | |
| 0x36 | `0011 0110` | write:/ | write:/ | |
| 0x37 | `0011 0111` | write:* | write:* | |
| 0x38 | `0011 1000` | write:= | write:= | |
| 0x39 | `0011 1001` | write:+ | write:+ | |
| 0x3A | `0011 1010` | write:- | write:- | |
| 0x3B-0x3D | - | (None) | | |
| 0x3E | `0011 1110` | keys:LSHIFT+TAB | | | not modifier（その場でShift+Tab送信） |
| 0x3F | `0011 1111` | keys:LCTRL+TAB | | | not modifier |

### 0x40 - 0x4F（数字4・た行・記号）

| Hex | bit | layer1 | withShift | withCtrl |
|---|---|---|---|---|
| 0x40 | `0100 0000` | write:4 | key:F4 | |
| 0x41 | `0100 0001` | write:ta | write:da | |
| 0x42 | `0100 0010` | write:ti | write:di | |
| 0x43 | `0100 0011` | write:tu | write:du | write:xtu |
| 0x44 | `0100 0100` | write:te | write:de | |
| 0x45 | `0100 0101` | write:to | write:do | |
| 0x46 | `0100 0110` | write:( | write:( | |
| 0x47 | `0100 0111` | write:) | write:) | |
| 0x48 | `0100 1000` | write:[ | write:[ | |
| 0x49 | `0100 1001` | write:{ | write:{ | |
| 0x4A | `0100 1010` | write:] | write:] | |
| 0x4B | `0100 1011` | write:} | write:} | |
| 0x4C | `0100 1100` | write:< | write:< | |
| 0x4D | `0100 1101` | write:> | write:> | |
| 0x4E | `0100 1110` | write:; | write:; | |
| 0x4F | `0100 1111` | write:: | write:: | |

### 0x50 - 0x5F（数字5・な行）

| Hex | bit | layer1 | withShift | withCtrl |
|---|---|---|---|---|
| 0x50 | `0101 0000` | write:5 | key:F5 | |
| 0x51 | `0101 0001` | write:na | | |
| 0x52 | `0101 0010` | write:ni | | |
| 0x53 | `0101 0011` | write:nu | | |
| 0x54 | `0101 0100` | write:ne | | |
| 0x55 | `0101 0101` | write:no | | |
| 0x56-0x5F | - | (None) | | |

### 0x60 - 0x6F（数字6・は行）

| Hex | bit | layer1 | withShift | withCtrl |
|---|---|---|---|---|
| 0x60 | `0110 0000` | write:6 | key:F6 | |
| 0x61 | `0110 0001` | write:ha | write:ba | write:pa |
| 0x62 | `0110 0010` | write:hi | write:bi | write:pi |
| 0x63 | `0110 0011` | write:hu | write:bu | write:pu |
| 0x64 | `0110 0100` | write:he | write:be | write:pe |
| 0x65 | `0110 0101` | write:ho | write:bo | write:po |
| 0x66-0x6F | - | (None) | | |

### 0x70 - 0x7F（数字7・ま行）

| Hex | bit | layer1 | withShift | withCtrl |
|---|---|---|---|---|
| 0x70 | `0111 0000` | write:7 | key:F7 | |
| 0x71 | `0111 0001` | write:ma | | |
| 0x72 | `0111 0010` | write:mi | | |
| 0x73 | `0111 0011` | write:mu | | |
| 0x74 | `0111 0100` | write:me | | |
| 0x75 | `0111 0101` | write:mo | | |
| 0x76-0x7F | - | (None) | | |

### 0x80 - 0x8F（数字8・や行・modifier）

| Hex | bit | layer1 | withShift | withCtrl |
|---|---|---|---|---|
| 0x80 | `1000 0000` | write:8 | key:F8 | |
| 0x81 | `1000 0001` | write:ya | | write:xya |
| **0x82** | `1000 0010` | **mod:Alt** | | | **新規（v0.3）** |
| 0x83 | `1000 0011` | write:yu | | write:xyu |
| **0x84** | `1000 0100` | **mod:Ctrl** | | | **新規（v0.3）** |
| 0x85 | `1000 0101` | write:yo | | write:xyo |
| **0x86** | `1000 0110` | **mod:Ctrl+Alt** | | | **新規（v0.3）** |
| 0x87 | `1000 0111` | (None) | | |
| **0x88** | `1000 1000` | **mod:Shift** | | | **新規（v0.3）** |
| 0x89 | `1000 1001` | (None) | | |
| **0x8A** | `1000 1010` | **mod:Shift+Alt** | | | **新規（v0.3）** |
| 0x8B | `1000 1011` | (None) | | |
| **0x8C** | `1000 1100` | **mod:Shift+Ctrl** | | | **新規（v0.3）** |
| 0x8D | `1000 1101` | (None) | | |
| **0x8E** | `1000 1110` | **mod:Shift+Ctrl+Alt** | | | **新規（v0.3）** |
| 0x8F | `1000 1111` | (None) | | |

### 0x90 - 0x9F（数字9・ら行）

| Hex | bit | layer1 | withShift | withCtrl |
|---|---|---|---|---|
| 0x90 | `1001 0000` | write:9 | key:F9 | |
| 0x91 | `1001 0001` | write:ra | | |
| 0x92 | `1001 0010` | write:ri | | |
| 0x93 | `1001 0011` | write:ru | | |
| 0x94 | `1001 0100` | write:re | | |
| 0x95 | `1001 0101` | write:ro | | |
| 0x96-0x9F | - | (None) | | |

### 0xA0 - 0xAF（数字0・わ行・ん）

| Hex | bit | layer1 | withShift | withCtrl |
|---|---|---|---|---|
| 0xA0 | `1010 0000` | write:0 | key:F10 | |
| 0xA1 | `1010 0001` | write:wa | | write:xwa |
| 0xA2 | `1010 0010` | (None) | | |
| 0xA3 | `1010 0011` | write:wo | | |
| 0xA4 | `1010 0100` | (None) | | |
| 0xA5 | `1010 0101` | write:nn | | |
| 0xA6-0xAF | - | (None) | | |

### 0xB0 - 0xBF（矢印↑・拡張領域）

| Hex | bit | layer1 | withShift | withCtrl |
|---|---|---|---|---|
| 0xB0 | `1011 0000` | key:UP | key:F11 | |
| 0xB1-0xBF | - | (None) | | |

### 0xC0 - 0xCF（矢印↓・拡張領域）

| Hex | bit | layer1 | withShift | withCtrl |
|---|---|---|---|---|
| 0xC0 | `1100 0000` | key:DOWN | key:F12 | |
| 0xC1-0xCF | - | (None) | | |

### 0xD0 - 0xDF（矢印←・拡張領域）

| Hex | bit | layer1 | withShift | withCtrl |
|---|---|---|---|---|
| 0xD0 | `1101 0000` | key:LEFT | | |
| 0xD1-0xDF | - | (None) | | |

### 0xE0 - 0xEF（矢印→・アルファベットa-o）

| Hex | bit | layer1 | withShift | withCtrl |
|---|---|---|---|---|
| 0xE0 | `1110 0000` | key:RIGHT | | |
| 0xE1 | `1110 0001` | write:a | write:A | |
| 0xE2 | `1110 0010` | write:b | write:B | |
| 0xE3 | `1110 0011` | write:c | write:C | |
| 0xE4 | `1110 0100` | write:d | write:D | |
| 0xE5 | `1110 0101` | write:e | write:E | |
| 0xE6 | `1110 0110` | write:f | write:F | |
| 0xE7 | `1110 0111` | write:g | write:G | |
| 0xE8 | `1110 1000` | write:h | write:H | |
| 0xE9 | `1110 1001` | write:i | write:I | |
| 0xEA | `1110 1010` | write:j | write:J | |
| 0xEB | `1110 1011` | write:k | write:K | |
| 0xEC | `1110 1100` | write:l | write:L | |
| 0xED | `1110 1101` | write:m | write:M | |
| 0xEE | `1110 1110` | write:n | write:N | |
| 0xEF | `1110 1111` | write:o | write:O | |

### 0xF0 - 0xFF（Enter・アルファベットp-z）

| Hex | bit | layer1 | withShift | withCtrl |
|---|---|---|---|---|
| 0xF0 | `1111 0000` | key:RET | | |
| 0xF1 | `1111 0001` | write:p | write:P | |
| 0xF2 | `1111 0010` | write:q | write:Q | |
| 0xF3 | `1111 0011` | write:r | write:R | |
| 0xF4 | `1111 0100` | write:s | write:S | |
| 0xF5 | `1111 0101` | write:t | write:T | |
| 0xF6 | `1111 0110` | write:u | write:U | |
| 0xF7 | `1111 0111` | write:v | write:V | |
| 0xF8 | `1111 1000` | write:w | write:W | |
| 0xF9 | `1111 1001` | write:x | write:X | |
| 0xFA | `1111 1010` | write:y | write:Y | |
| 0xFB | `1111 1011` | write:z | write:Z | |
| 0xFC-0xFF | - | (None) | | |

---

## 6. 集計

| 種別 | パターン数 |
|---|---|
| かな清音（あ行〜わ行+ん） | 46 |
| かな濁音（withShift） | 25 |
| かな半濁音・小書き（withCtrl） | 15 |
| 数字（0〜9） | 10 |
| F1〜F10（withShift） | 10 |
| アルファベット小文字（a〜z） | 26 |
| アルファベット大文字（withShift） | 26 |
| 記号（layer1） | 25 |
| 記号（withShift、ほぼ同記号） | 25 |
| 矢印 | 4 |
| 制御キー（Tab/BS/Space/Enter/Esc/Delete/superkey/Shift+Tab/Ctrl+Tab） | 9 |
| modifier arm（mod:* 系） | 7 |
| IME | 1 |
| **総アクション数** | **約229** |
| **総combo数（レイヤー別重複考慮後）** | 約350-400 |

---

## 7. ZMK実装方針

### 7.1 macro 命名規則

- `m_h_<hex>`: layer1 の動作（例: `m_h_21` = 「か」を送信するmacro）
- `m_s_<hex>`: withShift の動作
- `m_c_<hex>`: withCtrl の動作
- `m_arm_shift`, `m_arm_ctrl` 等: modifier arm

### 7.2 macro の末尾処理

armedレイヤー（L1〜L6）で発火するmacroは、末尾で必ず `<&to 0>` を追加する（L0復帰）。
modifier付きHID送信もmacro内で完結させる（Shift押下→キー送信→Shift解放→L0復帰）。

### 7.3 Esc（キャンセル）の扱い

0x0Eを全armedレイヤー（L1〜L6）で受けて、L0に戻すcomboを追加する。
L0で0x0Eを押した場合は通常のEscキー送信。

### 7.4 IME（0x1F）の扱い

Windows MS-IMEを前提に、`key:LANG1`（Henkan）または `kp INT5`（半角/全角）を送信。
要検証：実機でどのHIDコードがIME On/Offに対応するか確認。

### 7.5 CONFIG値

```
CONFIG_ZMK_COMBO_MAX_KEYS_PER_COMBO=8
CONFIG_ZMK_COMBO_MAX_COMBOS_PER_KEY=128  # 要検証、足りなければ256に
CONFIG_ZMK_COMBO_MAX_PRESSED_COMBOS=8
CONFIG_ZMK_KEYMAP_LAYERS_STATE_CHANGED=y  # debug用
```

---

## 8. 既知の制約

- **同じkey-positionsを共有するcomboの最大数:** ZMK CONFIG_ZMK_COMBO_MAX_COMBOS_PER_KEY で制限される。各キーから見て関与するcombo数を計算し、適切に設定する必要あり。
- **chord判定タイミング:** ZMKのcomboは「最初のキー押下から timeout-ms 以内に key-positions が揃う」と発火。Python版の「リリース時にスナップショット」とは厳密には異なる。実機で違和感がないか要確認。
- **layer-aware combos:** ZMKは `layers = <N>` でレイヤー指定combo可能（v3.5以降）。本実装はv0.3 manifest を使用。

---

## 9. v0.2 → v0.3 移行ガイド

| 項目 | v0.2 | v0.3 |
|---|---|---|
| Shift+ | 0x01（右SW4） | 0x88（左SW1+右SW1） |
| Ctrl+ | 0x05（右SW2+SW4） | 0x84（左SW1+右SW2） |
| Alt+ | 0x08（右SW1） | 0x82（左SW1+右SW3） |
| Shift+Ctrl+ | 0x02 | 0x8C |
| Shift+Alt+ | 0x03 | 0x8A |
| Ctrl+Alt+ | 0x06 | 0x86 |
| ローマ字 | 多様 | 訓令式に統一（si/ti/tu/hu/nn） |

**有線版（Python）との関係:**
v0.3 仕様は無線版（ZMK）の制約に合わせた更新であり、有線版（custom0405_code.py）は v0.2 のままで動作する。有線版を v0.3 に追従するかは別途判断。

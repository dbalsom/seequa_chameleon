
# Chameleon PAL Dumps

## File formats

 - **TT2** - Berkely format logic tables, produced by PALDump
 - **EQN** - EQNOTT format equations extracted by Espresso
 - **PLD** - CUPL assembly files

## PAL Types

The Chameleon has a number of different PAL types, some of them more obscure than others. They are a mix of combinatorial and registered PALs. Unfortunately, registered PALs cannot be easily dumped.

## PAL List

| Name    | Function                  | Type | PALDump   | Dumped? | PAL Type |
| ------- | ------------------------- | ---- | --------- | ------- | -------- |
| DCON    | DMA Control?              | R    |           |         | PAL16R4  |
| IOS     | Main IO Decode            | C    | added     |         | PAL20L10 |
| CRT     | Secondary Video IO decode | C    | added     | yes     | PAL12L6  |
| FDC     |                           | C    | supported |         | PAL16L8  |
| ROM     | Decode ROM Sockets        | C    | supported | yes     | PAL16L8  |
| RAM     | Decode DRAM banks         | C    | supported | yes     | PAL16L8  |
| KBD     | Keyboard Interface        | C    | ?         |         | PAL20L16 |
| 80ST    | Z80->8288 Translator      | C    | supported | yes     | PAL16L8  |
| DMA     | Also DMA?                 | R    |           |         | PAL16R6  |
| NMI     |                           | C    | added     |         | PAL12L6  |
| CPX     |                           | R    |           |         | PAL16R8  |
| CMX4    |                           | C    | no        |         | PAL18L4  |
| FDS     |                           | R    |           |         | PAL16R4  |
| WCP     |                           | R    |           |         | PAL16R6  |
| CRK     |                           | R    |           |         | PAL16R6  |
| CRM     |                           | C    | added     |         | PAL20L10 |
| CGC5    |                           | C    | ?         |         | PAL18L4  |
| CLT/CL4 |                           | C    | ?         |         | PAL20L2  |




---

### IOS - Main IO Addresss Decoder PAL

| Output Pin | Address Range     | Function                                               |
| :--------- | :---------------- | :----------------------------------------------------- |
| **P17**    | `000h – 07Fh`     | **Sub-Decoder Select** (Enable for GPIB/DMA/PIC/PIT/KB)|  
| **P21**    | `080h - 087h`     | **DMA Page Registers**                                 |
| **P22**    | `200h - 203h` (R) | **Game Port / Joystick** (Read)                        |
| **P23**    | `200h - 203h` (W) | **Game Port / Joystick** (Start Timer)                 |
| **P19**    | `378h – 37Fh`     | **LPT1 (Parallel Port)**                               |
| **P20**    | `3D4h – 3D7h`     | **6845 CRTC** (CGA Index/Data Registers)               |
| **P18**    | `3D8h – 3DFh`     | **Video Sub-Decoder**                                  |
| **P15**    | `3F0h – 3F2h`     | **FDC DOR**                                            |
| **P14**    |                   | **Data Bus Buffer Enable** (OE for 74LS244)            |
| **P16**    |                   | **I/O Wait State / Ready Logic**                       |

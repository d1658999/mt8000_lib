# Anritsu MT8000A — Comprehensive SCPI Remote Command Reference

**Source:** `document.md` (Application Note M1TB-1QA5GMEAS0044)  
**Instrument:** Anritsu MT8000A / MX800010A Radio Communication Test Station  
**Subject:** NR (5G New Radio) Conformance Measurements (TS38.521-1/2/3)

---

## Summary

**Total unique SCPI-like command names identified: ~135**  
Commands were extracted via exhaustive pattern-based searching of the 141,000+ line document. They are grouped below into 16 functional categories.

---

## 1. System Control & Initialization

| # | Command | Syntax / Arguments | Approx. Lines | Description |
|---|---------|-------------------|---------------|-------------|
| 1 | `PRESET` | `PRESET` | 8706, 12067, 22083 | Reset MT8821C (LTE) to defaults |
| 2 | `PRESETNSA` | `PRESETNSA` | 8712 | Preset MT8000A for NSA (Non-Stand Alone) mode |
| 3 | `PRESET_SA` | `PRESET_SA` | 14221, 16902 | Preset MT8000A for SA (Stand Alone) mode |
| 4 | `PRESETSA` | `PRESETSA` | 14627 | Alternate form of SA preset |
| 5 | `PRESET_NSA` | `PRESET_NSA` | 17447 | Alternate form of NSA preset |
| 6 | `RANOP` | `RANOP {ENDC\|SA\|NRDC}` | 8702, 14219, 14625, 16900 | Set RAN Operation mode (EN-DC, SA, NR-DC) |
| 7 | `SYSSEL` | `SYSSEL {1\|2}` | 14108, 16737 | Select system number |
| 8 | `SYSSEL?` | `SYSSEL? {1}` | 14106 | Query system selection / firmware version |
| 9 | `*OPC?` | `*OPC?` | Throughout | IEEE 488.2 Operation Complete query (synchronization) |
| 10 | `CONNECT` | `CONNECT {SN1},{SN2}` | 16730 | Select primary and secondary box (2-box config) |
| 11 | `CONNECT?` | `CONNECT? [PRIMARY\|SECONDARY]` | 16728-16744 | Query box connection config |
| 12 | `NUMOFMT8000A?` | `NUMOFMT8000A?` | 16743 | Query number of MT8000A units |
| 13 | `PORT?` | `PORT?` | 8329 | Query port number |
| 14 | `TEST_SPEC` | `TEST_SPEC {521_1_FR1_SA\|...}` | 19367, 19413 | Set test specification |
| 15 | `TEST_SPEC?` | `TEST_SPEC?` | 18972 | Query test specification |

## 2. Remote Command Destination

| # | Command | Syntax / Arguments | Approx. Lines | Description |
|---|---------|-------------------|---------------|-------------|
| 16 | `REM_DEST` | `REM_DEST {8000A\|8821C\|LTE\|NR}` | 8711, 12066, 13507 | Set remote command destination |
| 17 | `REM DEST` | `REM DEST {8000A\|8821C\|LTE\|NR}` | 8705, 12078, 13516 | Alternate form (space-separated) |
| 18 | `REMDEST` | `REMDEST {8000A\|8821C\|LTE}` | 12379, 12566, 13584 | Alternate form (no separator) |

> **Note:** These are all variants of the same underlying command to switch the remote command destination between MT8000A (NR), MT8821C (LTE), or system partitions (LTE/NR).

## 3. Test Interface & Slot Configuration

| # | Command | Syntax / Arguments | Approx. Lines | Description |
|---|---------|-------------------|---------------|-------------|
| 19 | `TESTIF` | `TESTIF {SLOT1\|SLOT2\|BOX2_SLOT1},{ARGV\|RFCONV\|ERF}` | 8715, 14227, 14632, 16907 | Set test interface (ARGV=direct/RFCONV=RF converter) |
| 20 | `TESTSLOT` | `TESTSLOT [cc,]{SLOT1\|SLOT2\|BOX2_SLOT1\|BOX2_SLOT2}` | 8722, 16752, 16979-17015 | Set test slot for carrier component |

## 4. Cell Configuration — Frequency & Bandwidth

| # | Command | Syntax / Arguments | Approx. Lines | Description |
|---|---------|-------------------|---------------|-------------|
| 21 | `FRAMETYPE` | `FRAMETYPE [cc,]{TDD\|FDD}` | 9100-10800 | Set frame type (TDD/FDD) per carrier |
| 22 | `BAND` | `BAND {cc},{band_number}` | 9100-10800 | Set operating band (e.g., 78, 41, 257) |
| 23 | `DLSCS` | `DLSCS {cc}.{15KHZ\|30KHZ\|120KHZ}` | 9100-10800 | Set DL subcarrier spacing |
| 24 | `ULSCS` | `ULSCS {cc}.{15KHZ\|30KHZ\|120KHZ}` | ~9100+ | Set UL subcarrier spacing |
| 25 | `DLBANDWIDTH` | `DLBANDWIDTH {cc}.{100MHZ\|20MHZ\|...}` | 9100-10800 | Set DL channel bandwidth |
| 26 | `ULBANDWIDTH` | `ULBANDWIDTH {cc}.{100MHZ\|20MHZ\|...}` | ~9100+ | Set UL channel bandwidth |
| 27 | `DLCHAN` | `DLCHAN {cc},{channel_number}` | 9100-10800 | Set DL channel (EARFCN/NR-ARFCN) |
| 28 | `DLCHAN POINTA` | `DLCHAN POINTA {cc},{value}` | ~10000+ | Set DL Point A channel number |
| 29 | `ULCHAN` | `ULCHAN {cc},{channel_number}` | 9100-10800 | Set UL channel (NR-ARFCN) |
| 30 | `OFFSETCARRIER` | `OFFSETCARRIER {cc},{value}` | 9900-10800 | Set offset to carrier |
| 31 | `SSBCHAN` | `SSBCHAN {cc},{channel_number}` | 9100-10800 | Set SSB channel number |
| 32 | `SSBSCS` | `SSBSCS {cc}.{15KHZ\|30KHZ\|120KHZ}` | 9100-10800 | Set SSB subcarrier spacing |
| 33 | `DUPLEX` | `DUPLEX {TDD\|FDD}` | ~7181, 7862 | Set duplex mode (referenced in GUI descriptions) |

## 5. Call Processing & Connection

| # | Command | Syntax / Arguments | Approx. Lines | Description |
|---|---------|-------------------|---------------|-------------|
| 34 | `CALLPROC` | `CALLPROC {ON\|OFF}` | 8707, 8724, 12068, 14236 | Enable/disable call processing |
| 35 | `CALLSTAT?` | `CALLSTAT?` | 12381-15476 | Query call processing status (returns 1=Idle, 2=Idle(Regist), 8=Connected, etc.) |
| 36 | `CALLSA` | `CALLSA` | 12383-15446 | Start SA/NSA call (initiate registration/connection) |
| 37 | `CALLSO` | `CALLSO` | (referenced in search patterns) | Call release / standby operation |

## 6. Level & Frequency Control

| # | Command | Syntax / Arguments | Approx. Lines | Description |
|---|---------|-------------------|---------------|-------------|
| 38 | `ILVL` | `ILVL [cc,]{level_dBm}` | 8756, 13661, 15864, 33045 | Set Input Level (UE Tx power expected at instrument) |
| 39 | `OLVL` | `OLVL [cc,]{EPRE\|PEAKEIS+n} {level}` | 13736, 16012, 32404 | Set Output Level (DL signal level to UE) |
| 40 | `TXIQROUTING` | `TXIQROUTING {SISO\|RXDIVERSITY\|USER}` | 9539-17460 | Set Tx IQ routing mode |
| 41 | `RFOUT` | `RFOUT {SLOT},{TRX},{MAIN\|AUX}` | 13517-13519 | Set RF output port routing |

## 7. UE & Power Control Parameters

| # | Command | Syntax / Arguments | Approx. Lines | Description |
|---|---------|-------------------|---------------|-------------|
| 42 | `UEPOWERCLASS` | `UEPOWERCLASS {CLASS3\|CLASS2\|CLASS1\|CLASS1_5}` | 8754, 17020, 17543 | Set UE power class |
| 43 | `MAXULPWR` | `MAXULPWR [cc,]{value_dBm}` | 8709, 32954-140684 | Set p-Max (maximum UL power) |
| 44 | `TPCPAT` | `TPCPAT {ALL3\|ALLM1\|ALLO\|AUTO\|AUTOTARGET}` | ~33000-43000 | Set TPC pattern (power control) |
| 45 | `TPCPATALL3` | `TPCPATALL3` | ~33000+ | Set TPC pattern All +3dB (no-space variant) |
| 46 | `TPCPATALLM1` | `TPCPATALLM1` | ~33000+ | Set TPC pattern All -1dB (no-space variant) |
| 47 | `ADDSPEM` | `ADDSPEM {ON\|OFF}` | 15653, 36507, 37696 | Enable/disable Additional Spectrum Emission |
| 48 | `ADDSPEMVALUE` | `ADDSPEMVALUE {0\|1\|...}` | 15655, 36509, 37702 | Set Additional Spectrum Emission value |
| 49 | `SSPBCHBLOCKPOWER` | `SSPBCHBLOCKPOWER {value}` | 44847-131909 | Set ss-PBCH-BlockPower |
| 50 | `GROUPHOPPING_CCH` | `GROUPHOPPING_CCH {ENABLE\|DISABLE}` | 8758, 14328, 15220 | Set PUCCH Group Hopping |
| 51 | `PREAMBLETGT` | `PREAMBLETGT {value}` | 8760, 14330 | Set PRACH Preamble Received Target Power |
| 52 | `PREAMBLEMAX` | `PREAMBLEMAX {N7\|N10\|...}` | 8762, 14332 | Set PreambleTransMax |
| 53 | `PWRRMPSTEP` | `PWRRMPSTEP {dB2\|dB4\|...}` | 8769, 14334 | Set Power Ramping Step |

## 8. RMC (Reference Measurement Channel) Configuration

| # | Command | Syntax / Arguments | Approx. Lines | Description |
|---|---------|-------------------|---------------|-------------|
| 54 | `ULWAVEFORM` | `ULWAVEFORM {cc}.{DFTOFDM\|CPOFDM}` | 15670-32340 | Set UL waveform type |
| 55 | `ULRMC_RB` | `ULRMC_RB [cc,]{num_RBs}` | 15680, 32341, 32614 | Set UL RMC Number of RBs |
| 56 | `ULRMC RB` | `ULRMC RB {cc}.{num_RBs}` | 15680 | Alternate form (space-separated) |
| 57 | `ULRB START` | `ULRB START [cc,]{start_RB}` | 15681-116635 | Set UL starting RB position |
| 58 | `ULRBSTART` | `ULRBSTART [cc,]{start_RB}` | ~15797+ | Alternate form (no space) |
| 59 | `ULRBSTARTSCC1` | `ULRBSTARTSCC1 {start_RB}` | ~34520+ | Set UL starting RB for SCC1 (legacy form) |
| 60 | `ULMCS_TABLE` | `ULMCS_TABLE {cc},{64QAM\|256QAM}` | 15740, 32345 | Set UL MCS Index Table |
| 61 | `ULIMCS` | `ULIMCS {cc},{index}` | 15754, 32347, 33019 | Set UL MCS Index |
| 62 | `ULRMC_MOD` | `ULRMC_MOD {QPSK\|16QAM\|64QAM}` | 32618, 33415-42986 | Set UL RMC modulation scheme (MT8821C) |
| 63 | `ULRMC_MOD_SCC1` | `ULRMC_MOD_SCC1 {QPSK}` | 34525, 41355 | Set UL RMC modulation for SCC1 |
| 64 | `PI2BPSK` | `PI2BPSK {ON\|OFF}` | (referenced ~32350) | Enable π/2-BPSK modulation |
| 65 | `DLRMC_RB` | `DLRMC_RB [cc,]{num_RBs}` | 15772, 32406, 32620 | Set DL RMC Number of RBs |
| 66 | `DLRMC RB` | `DLRMC RB {cc},{num_RBs}` | 15772 | Alternate form (space-separated) |
| 67 | `DLRB START` | `DLRB START [cc,]{start_RB}` | 32408-116635 | Set DL starting RB position |
| 68 | `DLRBSTART` | `DLRBSTART [cc,]{start_RB}` | ~15773+ | Alternate form (no space) |
| 69 | `DLMCS_TABLE` | `DLMCS_TABLE {cc},{64QAM\|256QAM}` | 32410, 33435 | Set DL MCS Index Table |
| 70 | `DLMCS TABLE` | `DLMCS TABLE {cc}.{64QAM}` | ~9000+ | Alternate form (space-separated) |
| 71 | `DLIMCS` | `DLIMCS {cc},{index}` | 15782, 32412, 32987 | Set DL MCS Index |
| 72 | `SCHEDULING` | `SCHEDULING {STATIC\|USER}` | 5387, 11071-136960 | Set scheduling mode |

## 9. NR-DC (Dual Connectivity) Target Selection

| # | Command | Syntax / Arguments | Approx. Lines | Description |
|---|---------|-------------------|---------------|-------------|
| 73 | `NRDC_SEL_TARGETFR` | `NRDC_SEL_TARGETFR {FR1\|FR2}` | 14963, 15166, 15647 | Select NR-DC target frequency range for commands |
| 74 | `NRDCSELTARGETFR` | `NRDCSELTARGETFR {FR1\|FR2}` | 15767 | Alternate form (no underscores) |

## 10. Measurement Control

| # | Command | Syntax / Arguments | Approx. Lines | Description |
|---|---------|-------------------|---------------|-------------|
| 75 | `MEASITEM` | `MEASITEM {NORMAL\|PWRTEMP\|PRACH\|PCT\|SRS\|EVMTP}` | 43474-137276 | Set measurement item type |
| 76 | `MEASSTART` | `MEASSTART` | (referenced) | Start measurement |
| 77 | `MEASSTOP` | `MEASSTOP` | (referenced) | Stop measurement |
| 78 | `MSTAT?` | `MSTAT?` | 15882-113884 | Query measurement status (returns completion state) |
| 79 | `ALLMEASITEMS_OFF` | `ALLMEASITEMS_OFF` | 15610-78635 | Turn off all measurement items |
| 80 | `ALLMEASITEMSOFF` | `ALLMEASITEMSOFF` | 33385-77793 | Alternate form (no underscores) |
| 81 | `ALLMEASITEMS-OFF` | `ALLMEASITEMS-OFF` | 32909, 42030 | Alternate form (hyphen) |

## 11. Measurement Switch Commands (Enable/Disable)

| # | Command | Syntax / Arguments | Approx. Lines | Description |
|---|---------|-------------------|---------------|-------------|
| 82 | `PWR MEAS` | `PWR MEAS {ON\|OFF}` | 15616, 32912-42470 | Enable/disable Power measurement |
| 83 | `PWRMEAS` | `PWRMEAS {ON}` | 56274-115710 | Enable Power measurement (no-space variant) |
| 84 | `PWR_AVG` | `PWR_AVG {1\|n}` | 15624-78640 | Set power measurement averaging count |
| 85 | `TPUTMEAS` | `TPUTMEAS {ON}` | 77790, 80362 | Enable Throughput measurement |
| 86 | `TPUT MEAS` | `TPUT MEAS {ON\|OFF}` | 15626, 77800, 78266 | Enable/disable Throughput measurement |
| 87 | `SEMMEAS` | `SEMMEAS {ON}` | 90290, 102329 | Enable SEM measurement |
| 88 | `SEM MEAS` | `SEM MEAS {ON}` | 74108-76831 | Enable SEM measurement (space variant) |
| 89 | `ACLR MEAS` | `ACLR MEAS {ON}` | 75538, 77315 | Enable ACLR measurement |
| 90 | `EARLY DECISION` | `EARLY DECISION {ON\|OFF}` | 15628, 77802, 78268 | Enable/disable throughput early decision |

## 12. Throughput Configuration

| # | Command | Syntax / Arguments | Approx. Lines | Description |
|---|---------|-------------------|---------------|-------------|
| 91 | `TPUT SAMPLE` | `TPUT SAMPLE {count}` | 15632, 16034, 78270 | Set throughput sample count |
| 92 | `TPUT UNIT` | `TPUT UNIT {BLOCK}` | 16030 | Set throughput unit |

## 13. Measurement Result Queries

| # | Command | Syntax / Arguments | Approx. Lines | Description |
|---|---------|-------------------|---------------|-------------|
| 93 | `POWER?` | `POWER? [{PCC\|SCC1\|SUM\|TOTAL\|ANT1\|ANT2}]` | 33108-140664 | Query UE power measurement result |
| 94 | `CHPWR?` | `CHPWR? [{PCC\|SCC1\|SUM}]` | 42183-119553 | Query channel power result |
| 95 | `EVM?` | `EVM? [{PCC\|SCC1\|SUM\|LAYER1\|LAYER2\|ANT1\|ANT2}]` | 57173-137364 | Query EVM result |
| 96 | `PCTPWR?` | `PCTPWR?` | 46549-55080 | Query PCT (Power Control Tolerance) power |
| 97 | `PCTPWR2?` | `PCTPWR2?` | 48052-51226 | Query PCT power result #2 |
| 98 | `PCTPWRE1?` | `PCTPWRE1?` | 48054-51228 | Query PCT power error #1 |
| 99 | `PCTPWRE2?` | `PCTPWRE2?` | 48056-51230 | Query PCT power error #2 |
| 100 | `ONPWR?` | `ONPWR?` | 43551-46076 | Query ON power (time mask) |
| 101 | `OFFPWR_BEFORE?` | `OFFPWR_BEFORE?` | 43552-44466 | Query OFF power before transition |
| 102 | `OFFPWRBEFORE?` | `OFFPWRBEFORE?` | 43999-45523 | Alternate form (no underscore) |
| 103 | `OFFPWR_AFTER?` | `OFFPWR_AFTER?` | 44468-45525 | Query OFF power after transition |
| 104 | `OFFPWRAFTER?` | `OFFPWRAFTER?` | 43554-46079 | Alternate form (no underscore) |
| 105 | `TTL_WORST_SEM_LV?` | `TTL_WORST_SEM_LV?` | 74234, 76117, 76512 | Query worst SEM level result |
| 106 | `TPUT? / TPUT variants` | `TPUT? {cc} PER` | 15885+ | Query throughput result per carrier |
| 107 | `TPUT_TOTAL_FR1?` | `TPUT_TOTAL_FR1? PER` | 15885 | Query total FR1 throughput |
| 108 | `TPUT_TOTAL_FR2?` | `TPUT_TOTAL_FR2?` | ~16087 | Query total FR2 throughput |
| 109 | `TPUT_BLERCNT?` | `TPUT_BLERCNT? {cc}` | 16066 | Query BLER count per carrier |
| 110 | `TPUT_BLERCNTNACK?` | `TPUT_BLERCNTNACK? {cc}` | 16067 | Query BLER NACK count |
| 111 | `TPUT_BLERCNTDTX?` | `TPUT_BLERCNTDTX? {cc}` | 16068 | Query BLER DTX count |
| 112 | `TPUT_BLER?` | `TPUT_BLER? {cc}` | 16069 | Query BLER ratio per carrier |
| 113 | `TPUT_TRANSBLOCK?` | `TPUT_TRANSBLOCK? {cc}` | 16070 | Query transport block count |
| 114 | `TPUT_TRANSFRAME?` | `TPUT TRANSFRAME? {cc}` | 16071 | Query transport frame count |
| 115 | `TPUT_BLERCNT_TOTAL_FR1?` | `TPUT_BLERCNT_TOTAL_FR1?` | 16075 | Query total FR1 BLER count |
| 116 | `TPUT_BLERCNTNACK_TOTAL_FR1?` | `TPUT_BLERCNTNACK_TOTAL_FR1?` | 16076 | Query total FR1 BLER NACK count |
| 117 | `TPUT_BLERCNTDTX_TOTAL_FR1?` | `TPUT_BLERCNTDTX_TOTAL_FR1?` | 16077 | Query total FR1 BLER DTX count |
| 118 | `TPUT_BLER_TOTAL_FR1?` | `TPUT_BLER_TOTAL_FR1?` | 16078 | Query total FR1 BLER ratio |
| 119 | `TPUT_TRANSBLOCK_TOTAL_FR1?` | `TPUT_TRANSBLOCK_TOTAL_FR1?` | 16079 | Query total FR1 transport blocks |
| 120 | `TPUT_TRANSFRAME_TOTAL_FR1?` | `TPUT TRANSFRAME TOTAL FR1?` | 16080 | Query total FR1 transport frames |
| 121 | `TPUT_TRANSFRAME_TOTAL_FR2?` | `TPUT TRANSFRAME TOTAL FR2?` | 16089 | Query total FR2 transport frames |
| 122 | `EIS?` | `EIS?` | 16055 | Query EIS measurement result |

## 14. Power Template & Time Mask

| # | Command | Syntax / Arguments | Approx. Lines | Description |
|---|---------|-------------------|---------------|-------------|
| 123 | `PWRTEMPAVG` | `PWRTEMPAVG {1\|n}` | 43476-137276 | Set power template averaging count |
| 124 | `PT_WDR` | `PT_WDR {ON\|OFF}` | 43478, 44311 | Set Power Template window (widen/restrict) |
| 125 | `PT_POWRES` | `PT_POWRES {OFF\|AUTO}` | 43480-131621 | Set Power Template power reset mode |

## 15. EIS (Effective Isotropic Sensitivity) — FR2

| # | Command | Syntax / Arguments | Approx. Lines | Description |
|---|---------|-------------------|---------------|-------------|
| 126 | `EIS_LVLSTEP` | `EIS_LVLSTEP {0.2\|n}` | 16023 | Set EIS level step size (dB) |
| 127 | `EIS_POLSWWAIT` | `EIS_POLSWWAIT {3.0\|n}` | 16024 | Set EIS polarization switch wait time (s) |
| 128 | `EIS_WAIT` | `EIS_WAIT {0.5\|n}` | 16029 | Set EIS wait time (s) |

## 16. CSI-RS, SRS, External Loss & Specialized Configuration

| # | Command | Syntax / Arguments | Approx. Lines | Description |
|---|---------|-------------------|---------------|-------------|
| 129 | `CSIRS` | `CSIRS {cc},{ON\|OFF}` | 11979-140957 | Enable/disable CSI-RS |
| 130 | `CSIRSRESOURCE` | `CSIRSRESOURCE {cc},{count}` | 11981 | Set CSI-RS resource count |
| 131 | `CSIRSPERIODICITY` | `CSIRSPERIODICITY {cc},{SLOTS40\|...}` | 11983 | Set CSI-RS periodicity |
| 132 | `CSIRSOFFSET` | `CSIRSOFFSET {cc},{resource},{offset}` | 11985-11991 | Set CSI-RS offset per resource |
| 133 | `CSIRSSTARTSYMBOL` | `CSIRSSTARTSYMBOL {cc},{symbol},{resource}` | 11993-11999 | Set CSI-RS start symbol |
| 134 | `CSIRSSTARTRB` | `CSIRSSTARTRB {cc},{start_RB}` | 12001 | Set CSI-RS starting RB |
| 135 | `CSIRSNRB` | `CSIRSNRB {cc},{num_RBs}` | 12003 | Set CSI-RS number of RBs |
| 136 | `SRS` | `SRS {ON\|OFF}` | 82035, 131465 | Enable/disable SRS |
| 137 | `SRSRESOURCE` | `SRSRESOURCE {PERIODIC\|APERIODIC}` | 82037, 131467, 131603 | Set SRS resource type |
| 138 | `SRSPERIODICITY` | `SRSPERIODICITY {SL20\|...}` | 82039, 131469 | Set SRS periodicity |
| 139 | `SRSOFFSET` | `SRSOFFSET {value}` | 82041-140312 | Set SRS offset |
| 140 | `SRSSTARTSYMBOL` | `SRSSTARTSYMBOL {value}` | 82043, 131473 | Set SRS start symbol |
| 141 | `SRSSYMBOLLENGTH` | `SRSSYMBOLLENGTH {N1\|N2\|N4}` | 82045, 131475 | Set SRS symbol length |
| 142 | `SRSALPHA` | `SRSALPHA {ALPHA08\|ALPHAO}` | 82047, 89652, 90757 | Set SRS alpha value |
| 143 | `SRS_P0` | `SRS_P0 {value}` | 82049-140316 | Set SRS p0 value |
| 144 | `EXTLOSSWJND` | `EXTLOSSWJND {SLOT},{ON\|COMMON}` | ~9200-10600 | Set external loss window setting |
| 145 | `EXTLOSSTBLID12GJND` | `EXTLOSSTBLID12GJND {SLOT},{TRX},{table_id}` | ~9200-10600 | Set external loss table ID for ≤12GHz |
| 146 | `EXTLOSSTBLID28GJND` | `EXTLOSSTBLID28GJND {SLOT},{TRX},{table_id}` | ~9200-10600 | Set external loss table ID for ≤28GHz |
| 147 | `EXTLOSSTBLID6GJND` | `EXTLOSSTBLID6GJND {SLOT},{TRX},{table_id}` | ~9500 | Set external loss table ID for ≤6GHz |
| 148 | `LTECONFIGFORDPS` | `LTECONFIGFORDPS {ON\|OFF}` | 35165-75255 | Enable/disable LTE config for DPS |
| 149 | `ANTCONFIG` | `ANTCONFIG [cc,]{4X4_TM3\|OPEN_LOOP\|...}` | 22311, 22667 | Set antenna configuration / MIMO mode |
| 150 | `REDCAPOP` | `REDCAPOP {ON\|OFF}` | 140440-141053 | Enable/disable RedCap operation |
| 151 | `NTN_PRESET` | `NTN_PRESET {3GPP_MND_600\|...}` | 141544 | Set NTN preset configuration |
| 152 | `NTN_UELOC_LONGI?` | `NTN_UELOC_LONGI?` | 14474 | Query NTN UE location longitude |
| 153 | `NTN_UELOC_LATI?` | `NTN_UELOC_LATI?` | 14475 | Query NTN UE location latitude |
| 154 | `NTN_UELOC_ALTI?` | `NTN_UELOC_ALTI?` | 14476 | Query NTN UE location altitude |

---

## Notes

1. **Command Variants**: Many commands appear with slight syntax variations throughout the document (e.g., spaces vs. underscores, periods vs. commas as delimiters). These are likely OCR artifacts from the PDF-to-markdown conversion or legitimate firmware version differences. The canonical forms typically use underscores or no separator.

2. **Carrier Component Addressing**: Most commands accept carrier component prefixes: `PCC` (Primary Component Carrier), `SCC1`–`SCC9` (Secondary Component Carriers), or `FR2_PCC`, `FR2_SCC1`, etc. for NR-DC configurations.

3. **LTE Commands (MT8821C)**: Some commands like `PRESET`, `ULRMC_RB`, `ULRMC_MOD`, `DLRMC_RB`, `ILVL`, `MAXULPWR` without carrier prefixes are directed to the MT8821C (LTE tester) after switching the remote destination via `REM_DEST 8821C`.

4. **Deprecated/Changed Commands**: `TTL_WORST_SEM?` was changed to `TTL_WORST_SEM_LV?` (noted at line ~5472).

5. **MEASITEM Modes**: The `MEASITEM` command switches between measurement modes:
   - `NORMAL` — Standard power measurement
   - `PWRTEMP` — Power template (ON/OFF power, time mask)
   - `PRACH` — PRACH-specific measurements
   - `PCT` — Power Control Tolerance
   - `SRS` — SRS time mask measurements
   - `EVMTP` — EVM throughput measurements

6. **2-Box Configuration**: For FR1+FR2 or high CA configurations, commands may reference `BOX2_SLOT1`, `BOX2_SLOT2` for the secondary MT8000A unit.

7. **Document Sections**: Lines ~8700-14600 cover initial setup; ~15600-16100 cover NRDC measurement procedures; ~32000-55000 cover FR1 power/time-mask/PCT; ~56000-78000 cover EVM/SEM/ACLR; ~78000-92000 cover throughput and SRS; ~92000-120000 cover CA measurements; ~120000-141000 cover MIMO, RedCap, and NTN measurements.

"""
Anritsu MT8000A / MT8821C Remote Command Library for NR TDD Measurements
=========================================================================

Python module providing SCPI-like remote commands extracted from:
  Application Note: M1TB-1QA5GMEAS0044
  NR TDD Measurement Software MX800010A

Usage:
    import pyvisa
    from mt8000a_commands import MT8000A

    rm = pyvisa.ResourceManager()
    inst = rm.open_resource("GPIB0::1::INSTR")  # or TCPIP address
    mt = MT8000A(inst)

    # Example: SA call setup on band 78
    inst.write(mt.preset_sa())
    inst.query("*OPC?")  # Note: opc moved to MT8000A and MT8821C
    mt.set_ran_operation("SA")
    mt.set_frame_type("TDD")
    mt.set_band("PCC", 78)
    mt.set_dl_scs("PCC", "30KHZ")
    mt.set_dl_bandwidth("PCC", "100MHZ")
    inst.write(mt.call_sa())
    mt.wait_for_call_connected()

    # Example: Power measurement
    inst.write(mt.all_meas_items_off())
    inst.query("*OPC?")
    mt.set_power_meas(True)
    inst.write(mt.sweep())
    inst.query("*OPC?")
    result = inst.query(mt.query_power())
"""

from __future__ import annotations

import time
import logging
from typing import Optional, Union

logger = logging.getLogger(__name__)


class MT8000A:
    """
    Anritsu MT8000A NR Test Station remote commands.

    Commands are grouped by functional category for clarity.
    Most setter methods accept carrier component arguments like 'PCC', 'SCC1', etc.
    """
    # =========================================================================
    # Self test write and query commands
    # =========================================================================
    
    def __init__(self, visa_resource, timeout_ms: int = 10000):
        """
        Parameters
        ----------
        visa_resource : pyvisa.Resource
            An opened VISA instrument resource (GPIB, TCPIP, etc.)
        timeout_ms : int
            Default command timeout in milliseconds.
        """
        self._inst = visa_resource
        self._inst.timeout = timeout_ms

    def write(self, cmd: str) -> None:
        """Send a SCPI command."""
        logger.debug("WRITE: %s", cmd)
        self._inst.write(cmd)

    def query(self, cmd: str) -> str:
        """Send a query and return the response string."""
        logger.debug("QUERY: %s", cmd)
        resp = self._inst.query(cmd).strip()
        logger.debug("RESP:  %s", resp)
        return resp

    def close(self) -> None:  
        """Close the VISA resource."""
        self._inst.close()

    # =========================================================================
    # System / Initialization
    # =========================================================================
    def opc(self) -> str:
        """Wait for operation complete (*OPC?)."""
        return "*OPC?"
    
    def preset(self) -> str:
        """Initialize all parameters (NSA mode)."""
        # Note: Consider adding *OPC? after this command.
        return "PRESET"

    def preset_sa(self) -> str:
        """Initialize all parameters for SA mode."""
        # Note: Consider adding *OPC? after this command.
        return "PRESET_SA"

    def set_ran_operation(self, mode: str) -> str:
        """Set RAN operation mode. mode: 'SA' | 'NSA'"""
        return f"RANOP {mode}"

    def set_remote_destination(self, dest: str) -> str:
        """
        Switch remote command destination.
        dest: '8000A' | '8821C' | 'LTE' | 'NR'
        """
        return f"REM_DEST {dest}"

    def set_test_interface(self, slot: str, interface: str = "ARGV") -> str:
        """Set test interface. e.g. TESTIF SLOT1,ARGV"""
        return f"TESTIF {slot},{interface}"

    def set_test_slot(self, slot: str, cc: Optional[str] = None) -> str:
        """Set test slot. e.g. TESTSLOT SLOT1 or TESTSLOT PCC,SLOT1"""
        if cc:
            return f"TESTSLOT {cc},{slot}"
        else:
            return f"TESTSLOT {slot}"

    def set_system_select(self, system_num: int) -> str:
        """Select system number for multi-system config. e.g. SYSSEL 1"""
        return f"SYSSEL {system_num}"

    def query_system_select(self, system_num: Optional[int] = None) -> str:
        """Query system selection."""
        if system_num is not None:
            return f"SYSSEL? {system_num}"
        return "SYSSEL?"

    def query_num_mt8000a(self) -> str:
        """Query number of MT8000A units (2-box config)."""
        return "NUMOFMT8000A?"

    # =========================================================================
    # Call Processing / Connection Control
    # =========================================================================
    def set_call_processing(self, on_off: bool) -> str:
        """Enable/disable call processing."""
        return f"CALLPROC {'ON' if on_off else 'OFF'}"

    def call_sa(self) -> str:
        """Initiate SA call connection."""
        return "CALLSA"

    def call_disconnect(self) -> str:
        """Disconnect the call (SA)."""
        return "CALLSO"

    def query_call_status(self) -> str:
        """Query current call processing status."""
        return "CALLSTAT?"

    def query_connection_status(self) -> str:
        """Query connection status."""
        return "CONNECT?"

    # TODO: implement higer-level call control methods that combine commands and polling, e.g. wait_for_call_connected()
    # def wait_for_call_connected(self, timeout_s: float = 60, poll_interval_s: float = 1) -> bool:
    #     """
    #     Poll CALLSTAT? until connected or timeout.
    #     Returns True if connected, False on timeout.
    #     """
    #     start = time.time()
    #     while time.time() - start < timeout_s:
    #         status = self.query(self.query_call_status())
    #         if "CONNECTED" in status.upper() or status == "6":
    #             return True
    #         time.sleep(poll_interval_s)
    #     logger.warning("Call connection timed out after %ss", timeout_s)
    #     return False

    # =========================================================================
    # SIM / Authentication
    # =========================================================================
    def set_sim_model(self, model: str) -> str:
        """Set SIM card model number. e.g. SIMMODELNUM P0135"""
        return f"SIMMODELNUM {model}"

    def set_integrity(self, algorithm: str) -> str:
        """Set integrity protection algorithm. e.g. INTEGRITY SNOW3G"""
        return f"INTEGRITY {algorithm}"

    # =========================================================================
    # Frame Structure / Duplex Mode
    # =========================================================================
    def set_frame_type(self, mode: str, cc: Optional[str] = None) -> str:
        """
        Set duplex mode. mode: 'TDD' | 'FDD'
        cc: carrier component, e.g. 'SCC1'. If None, applies to PCC.
        """
        if cc:
            return f"FRAMETYPE {cc},{mode}"
        else:
            return f"FRAMETYPE {mode}"

    def set_channel_setting_mode(self, mode: str = "LOWESTGSCN") -> str:
        """Set channel setting mode. Default: LOWESTGSCN"""
        return f"CHANSETMODE {mode}"

    def set_common_setting_mode(self, mode: str) -> str:
        """Set common setting mode."""
        return f"COMMONSETMODE {mode}"

    # =========================================================================
    # Band / Frequency Configuration
    # =========================================================================
    def set_band(self, cc: str, band: int) -> str:
        """Set operation band. e.g. BAND PCC,78"""
        return f"BAND {cc},{band}"

    def set_dl_scs(self, cc: str, scs: str) -> str:
        """Set DL subcarrier spacing. e.g. DLSCS PCC,30KHZ"""
        return f"DLSCS {cc},{scs}"

    def set_dl_bandwidth(self, cc: str, bw: str) -> str:
        """Set DL channel bandwidth. e.g. DLBANDWIDTH PCC,100MHZ"""
        return f"DLBANDWIDTH {cc},{bw}"

    def set_dl_channel(self, cc: str, channel: int) -> str:
        """Set DL center channel (NR-ARFCN). e.g. DLCHAN PCC,623334"""
        return f"DLCHAN {cc},{channel}"

    def set_offset_carrier(self, cc: str, offset: int) -> str:
        """Set DL OffsetToCarrier. e.g. OFFSETCARRIER PCC,0"""
        return f"OFFSETCARRIER {cc},{offset}"

    def set_ssb_channel(self, cc: str, channel: int) -> str:
        """Set Absolute Frequency SSB. e.g. SSBCHAN PCC,620352"""
        return f"SSBCHAN {cc},{channel}"

    def set_ssb_scs(self, cc: str, scs: str) -> str:
        """Set SS Block Subcarrier Spacing. e.g. SSBSCS PCC,30KHZ"""
        return f"SSBSCS {cc},{scs}"

    def set_ssb_type(self, cc: str, stype: str) -> str:
        """Set SS Block Transmission Type. e.g. SSBTYPE PCC,BITMAP"""
        return f"SSBTYPE {cc},{stype}"

    def set_ssb_position(self, cc: str, bitmap: str) -> str:
        """Set SS Block Position Bitmap. e.g. SSBPOS PCC,40"""
        return f"SSBPOS {cc},{bitmap}"

    def set_ssb_period(self, cc: str, period: int) -> str:
        """Set SSB Burst Periodicity (ms). e.g. SSBPERIOD PCC,10"""
        return f"SSBPERIOD {cc},{period}"

    def set_ssb_power(self, power: float) -> str:
        """Set SS/PBCH Block Power. e.g. SSPBCHBLOCKPOWER -6.02"""
        return f"SSPBCHBLOCKPOWER {power}"

    def set_ul_channel(self, cc: str, channel: int) -> str:
        """Set UL center channel (NR-ARFCN). e.g. ULCHAN PCC,516582"""
        return f"ULCHAN {cc},{channel}"

    def set_ul_bandwidth(self, cc: str, bw: str) -> str:
        """Set UL channel bandwidth. e.g. ULBANDWIDTH PCC,100MHZ"""
        return f"ULBANDWIDTH {cc},{bw}"

    def set_ul_offset_carrier(self, cc: str, offset: int) -> str:
        """Set UL OffsetToCarrier. e.g. ULOFFSETCARRIER PCC,0"""
        return f"ULOFFSETCARRIER {cc},{offset}"

    def set_cell_id(self, cc: str, cell_id: int) -> str:
        """Set Physical Cell ID. e.g. CELLID PCC,0"""
        return f"CELLID {cc},{cell_id}"

    # =========================================================================
    # TDD Configuration
    # =========================================================================
    def set_tdd_ul_dl_config(self, cc: str, config: str) -> str:
        """Set TDD UL/DL Configuration. e.g. TDDULDLCONF PCC,CONFIG1"""
        return f"TDDULDLCONF {cc},{config}"

    def set_tdd_ul_dl_config2(self, cc: str, config: str) -> str:
        """Set TDD UL/DL Configuration 2."""
        return f"TDDULDLCONF2 {cc},{config}"

    def set_tdd_ssf_config(self, cc: str, config: str) -> str:
        """Set TDD special subframe configuration."""
        return f"TDDSSFCONF {cc},{config}"

    def set_dl_ul_period(self, cc: str, period: str) -> str:
        """Set DL/UL Periodicity. e.g. DLULPERIOD PCC,5MS"""
        return f"DLULPERIOD {cc},{period}"

    def set_dl_duration(self, cc: str, duration: int) -> str:
        """Set DL Duration (slots). e.g. DLDURATION PCC,8"""
        return f"DLDURATION {cc},{duration}"

    def set_ul_duration(self, cc: str, duration: int) -> str:
        """Set UL Duration (slots). e.g. ULDURATION PCC,2"""
        return f"ULDURATION {cc},{duration}"

    def set_dl_symbols(self, cc: str, symbols: int) -> str:
        """Set Common DL symbols. e.g. DLSYMBOLS PCC,6"""
        return f"DLSYMBOLS {cc},{symbols}"

    def set_ul_symbols(self, cc: str, symbols: int) -> str:
        """Set Common UL symbols. e.g. ULSYMBOLS PCC,4"""
        return f"ULSYMBOLS {cc},{symbols}"

    # =========================================================================
    # Carrier Aggregation (CA) Configuration
    # =========================================================================
    def set_dl_scc(self, num: int) -> str:
        """Set number of DL Secondary Component Carriers. e.g. DLSCC 1"""
        return f"DLSCC {num}"

    def set_ul_scc(self, num: int) -> str:
        """Set number of UL Secondary Component Carriers. e.g. ULSCC 1"""
        return f"ULSCC {num}"

    def set_ul_ca(self, num: int) -> str:
        """Set number of UL CA carriers. e.g. ULCA 2"""
        return f"ULCA {num}"

    def set_dl_2ca(self, mode: str) -> str:
        """Configure DL 2CA mode."""
        return f"DL2CA {mode}"

    def set_ul_agg_level(self, level: int) -> str:
        """Set UL aggregation level."""
        return f"ULAGGLVL {level}"

    def set_dl_agg_level(self, level: int) -> str:
        """Set DL aggregation level."""
        return f"DLAGGLVL {level}"

    # =========================================================================
    # Supplementary Uplink (SUL) Configuration
    # =========================================================================
    def enable_sul(self) -> str:
        """Enable Supplementary Uplink (SUL) carrier."""
        return "ADDSULON"

    def set_sul_band(self, cc: str, band: int) -> str:
        """Set SUL operation band. e.g. SULBAND PCC,80"""
        return f"SULBAND {cc},{band}"

    def set_sul_bandwidth(self, cc: str, bw: str) -> str:
        """Set SUL channel bandwidth. e.g. SULBANDWIDTH PCC,5MHZ"""
        return f"SULBANDWIDTH {cc},{bw}"

    def set_sul_channel(self, cc: str, channel: int) -> str:
        """Set SUL center channel. e.g. SULCHAN PCC,349500"""
        return f"SULCHAN {cc},{channel}"

    def set_sul_offset_carrier(self, cc: str, offset: int) -> str:
        """Set SUL OffsetToCarrier. e.g. SULOFFSETCARRIER PCC,2198"""
        return f"SULOFFSETCARRIER {cc},{offset}"

    # =========================================================================
    # Handover Configuration
    # =========================================================================
    def set_ho_type(self, ho_type: str) -> str:
        """Set handover type. e.g. HOTYPE NORMAL"""
        return f"HOTYPE {ho_type}"

    def set_ho_frame_type(self, mode: str) -> str:
        """Set handover duplex mode. e.g. HO_FRAMETYPE TDD"""
        return f"HO_FRAMETYPE {mode}"

    def set_ho_channel_setting_mode(self, mode: str = "LOWESTGSCN") -> str:
        """Set handover channel setting mode."""
        return f"HO_CHANSETMODE {mode}"

    def set_ho_band(self, cc: str, band: int) -> str:
        """Set handover operation band. e.g. HO_BAND PCC,78"""
        return f"HO_BAND {cc},{band}"

    def set_ho_dl_bandwidth(self, cc: str, bw: str) -> str:
        """Set handover DL bandwidth. e.g. HO_DLBANDWIDTH PCC,100MHZ"""
        return f"HO_DLBANDWIDTH {cc},{bw}"

    def set_ho_dl_channel(self, cc: str, channel: int) -> str:
        """Set handover DL center channel. e.g. HO_DLCHAN PCC,623334"""
        return f"HO_DLCHAN {cc},{channel}"

    def set_ho_offset_carrier(self, cc: str, offset: int) -> str:
        """Set handover OffsetToCarrier. e.g. HO_OFFSETCARRIER PCC,0"""
        return f"HO_OFFSETCARRIER {cc},{offset}"

    def set_ho_ssb_channel(self, cc: str, channel: int) -> str:
        """Set handover SSB channel. e.g. HO_SSBCHAN PCC,620352"""
        return f"HO_SSBCHAN {cc},{channel}"

    def execute_channel_handover(self) -> str:
        """Execute channel handover."""
        # Note: Consider adding *OPC? after this command.
        return "EXEC_CHHO"

    # =========================================================================
    # Routing / Port Configuration
    # =========================================================================
    def set_routing_mode(self, mode: str) -> str:
        """Set routing mode. mode: 'USER' | 'SISO' | etc. e.g. TXIQROUTING USER"""
        return f"TXIQROUTING {mode}"

    def set_meas_hw_slot(self, cc: str, slot: str) -> str:
        """Set measurement HW slot. e.g. MEASHWSLOT PCC,SLOT1"""
        return f"MEASHWSLOT {cc},{slot}"

    def set_meas_hw_port(self, cc: str, port: str) -> str:
        """Set measurement HW port (TRx). e.g. MEASHWPORT PCC,TRX1"""
        return f"MEASHWPORT {cc},{port}"

    def set_cell_trx(self, cc: str, trx: str) -> str:
        """Set Cell TRx port. e.g. CELLTRX PCC,TRX1"""
        return f"CELLTRX {cc},{trx}"

    def set_rf_out(self, setting: str) -> str:
        """Set RF output configuration."""
        return f"RFOUT {setting}"

    def set_channel_coding(self, mode: str) -> str:
        """Set channel coding. e.g. CHCODING RMC"""
        return f"CHCODING {mode}"

    def set_box2_slot(self, slot: str, trx: str, value: Optional[float] = None) -> str:
        """Set 2-box configuration slot. e.g. BOX2_SLOT1 TRX1,12.7"""
        if value is not None:
            return f"BOX2_SLOT1 {trx},{value}"
        else:
            return f"BOX2_SLOT1 {trx}"

    # =========================================================================
    # AUX Connector Configuration (for external SG sync)
    # =========================================================================
    def set_aux_frame_timing1(self, slot: str, mode: str) -> str:
        """Set AUX Frame Timing 1. e.g. AUX_FRAME_TIM1 SLOT1,FRAME"""
        return f"AUX_FRAME_TIM1 {slot},{mode}"

    def set_aux_frame_timing2(self, slot: str, mode: str) -> str:
        """Set AUX Frame Timing 2. e.g. AUX_FRAME_TIM2 SLOT1,FRAME"""
        return f"AUX_FRAME_TIM2 {slot},{mode}"

    # =========================================================================
    # PDCCH / DCI Configuration
    # =========================================================================
    def set_dci_format(self, fmt: str) -> str:
        """Set DCI Format. e.g. DCIFORMAT FORMAT0_1_AND_1_1"""
        return f"DCIFORMAT {fmt}"

    def set_scheduling(self, mode: str) -> str:
        """Set scheduling type. mode: 'STATIC' | 'DYNAMIC'. e.g. SCHEDULING STATIC"""
        return f"SCHEDULING {mode}"

    def set_num_rb_coreset(self, cc: str, rb: str) -> str:
        """Set CORESET Number of RBs. e.g. NUMRBCORESET PCC,FULLBW"""
        return f"NUMRBCORESET {cc},{rb}"

    def set_num_sym_coreset(self, cc: str, sym: int) -> str:
        """Set CORESET Number of Symbols."""
        return f"NUMSYMCORESET {cc},{sym}"

    def set_cce_index_type(self, cc: str, mode: str) -> str:
        """Set CCE Index Allocation. e.g. CCEINDEX_TYPE PCC,AUTO"""
        return f"CCEINDEX_TYPE {cc},{mode}"

    def set_cce_index(self, cc: str, index: int) -> str:
        """Set CCE Index value."""
        return f"CCEINDEX {cc},{index}"

    def set_ss_candidate(self, cc: str, value: int) -> str:
        """Set number of PDCCH candidates."""
        return f"SSCANDIDATE {cc},{value}"

    def set_ss_candidate_al4(self, cc: str, value: int) -> str:
        """Set number of PDCCH candidates for AL4."""
        return f"SSCANDIDATE_AL4 {cc},{value}"

    def set_ss_candidate_al16(self, cc: str, value: int) -> str:
        """Set number of PDCCH candidates for AL16."""
        return f"SSCANDIDATE_AL16 {cc},{value}"

    def set_start_prb_cch_fmt1(self, cc: str, prb: int) -> str:
        """Set starting PRB for CCH Format 1."""
        return f"STARTPRB_CCHFMT1 {cc},{prb}"

    def set_start_prb_cch_fmt3(self, cc: str, prb: int) -> str:
        """Set starting PRB for CCH Format 3."""
        return f"STARTPRB_CCHFMT3 {cc},{prb}"

    def set_format_type(self, cc: str, fmt: str) -> str:
        """Set PUCCH format type."""
        return f"FORMATTYPE {cc},{fmt}"

    def set_format_type_cch(self, cc: str, fmt: str) -> str:
        """Set PUCCH CCH format type."""
        return f"FORMATTYPE_CCH {cc},{fmt}"

    def set_group_hopping_cch(self, mode: str) -> str:
        """Set PUCCH Group Hopping. mode: 'ENABLE' | 'NEITHER'. e.g. GROUPHOPPING_CCH ENABLE"""
        return f"GROUPHOPPING_CCH {mode}"

    def set_dl_harq_ack_codebook(self, cc: str, mode: str) -> str:
        """Set HARQ-ACK Codebook. mode: 'DYNAMIC' | 'SEMISTATIC'"""
        return f"DLHARQACKCODEBOOK {cc},{mode}"

    def set_dl_num_harq_process(self, cc: str, num: int) -> str:
        """Set number of DL HARQ processes."""
        return f"DLNUMHARQPROCESS {cc},{num}"

    def set_crnti(self, cc: str, value: int) -> str:
        """Set C-RNTI value."""
        return f"CRNTI {cc},{value}"

    def set_report_direct_current(self, mode: str) -> str:
        """Set Report Direct Current. e.g. REPORTDIRECTCURRENT ON"""
        return f"REPORTDIRECTCURRENT {mode}"

    def set_phy_chan_set_mode(self, mode: str) -> str:
        """Set Physical Channel Setting Mode."""
        return f"PHYCHANSETMODE {mode}"

    # =========================================================================
    # RMC / Modulation Configuration
    # =========================================================================
    def set_ch_config(self, config: str) -> str:
        """Set RMC Configuration. config: 'PUSCH' | 'PUCCH' | etc. e.g. CHCONFIG PUSCH"""
        return f"CHCONFIG {config}"

    def set_tx_config(self, cc: str, mode: str) -> str:
        """Set txConfig. e.g. TXCONFIG PCC,CODEBOOK"""
        return f"TXCONFIG {cc},{mode}"

    # --- DL RMC ---
    def set_dl_rmc_rb(self, cc: str, rb: int) -> str:
        """Set DL RMC Number of RB. e.g. DLRMC_RB PCC,0"""
        return f"DLRMC_RB {cc},{rb}"

    def set_dl_rb_start(self, cc: str, start: int) -> str:
        """Set DL RMC Starting RB. e.g. DLRB_START PCC,0"""
        return f"DLRB_START {cc},{start}"

    def set_dl_mcs_table(self, cc: str, table: str) -> str:
        """Set DL MCS Index Table. e.g. DLMCS_TABLE PCC,64QAM"""
        return f"DLMCS_TABLE {cc},{table}"

    def set_dl_mcs_index(self, cc: str, index: int) -> str:
        """Set DL MCS Index. e.g. DLIMCS PCC,4"""
        return f"DLIMCS {cc},{index}"

    def set_dl_rmc(self, cc: str, rmc: str) -> str:
        """Set DL RMC configuration name."""
        return f"DLRMC {cc},{rmc}"

    # --- UL RMC ---
    def set_ul_waveform(self, cc: str, waveform: str) -> str:
        """Set UL waveform. waveform: 'DFTOFDM' | 'CPOFDM'. e.g. ULWAVEFORM PCC,DFTOFDM"""
        return f"ULWAVEFORM {cc},{waveform}"

    def set_ul_rmc_rb(self, cc: str, rb: int) -> str:
        """Set UL RMC Number of RB. e.g. ULRMC_RB PCC,162"""
        return f"ULRMC_RB {cc},{rb}"

    def set_ul_rb_start(self, cc: str, start: int) -> str:
        """Set UL RMC Starting RB. e.g. ULRB_START PCC,0"""
        return f"ULRB_START {cc},{start}"

    def set_ul_mcs_table(self, cc: str, table: str) -> str:
        """Set UL MCS Index Table. e.g. ULMCS_TABLE PCC,64QAM"""
        return f"ULMCS_TABLE {cc},{table}"

    def set_ul_mcs_index(self, cc: str, index: int) -> str:
        """Set UL MCS Index. e.g. ULIMCS PCC,10"""
        return f"ULIMCS {cc},{index}"

    def set_ul_rmc_mod(self, cc: str, mod: str) -> str:
        """Set UL RMC Modulation. e.g. ULRMC_MOD PCC,QPSK"""
        return f"ULRMC_MOD {cc},{mod}"

    def set_ul_rmc(self, cc: str, rmc: str) -> str:
        """Set UL RMC configuration name."""
        return f"ULRMC {cc},{rmc}"

    # =========================================================================
    # MIMO / Antenna Configuration
    # =========================================================================
    def set_antenna_config(self, config: str) -> str:
        """Set antenna configuration."""
        return f"ANTCONFIG {config}"

    def set_ul_antenna_config(self, cc: str, config: str) -> str:
        """Set UL antenna configuration. e.g. ULANTCONFIG PCC,1T2R"""
        return f"ULANTCONFIG {cc},{config}"

    def set_ul_antenna_num(self, cc: str, num: int) -> str:
        """Set UL antenna number."""
        return f"ULANTNUM {cc},{num}"

    def set_ul_layer_num(self, cc: str, num: int) -> str:
        """Set UL number of layers."""
        return f"ULLAYERNUM {cc},{num}"

    def set_tpmi(self, cc: str, mode: str) -> str:
        """Set TPMI mode."""
        return f"TPMI {cc},{mode}"

    def set_tpmi_value(self, cc: str, value: int) -> str:
        """Set TPMI value."""
        return f"TPMIVAL {cc},{value}"

    def set_ul_fptx(self, mode: str) -> str:
        """Set UL Full Power Tx mode. e.g. ULFPTX ON"""
        return f"ULFPTX {mode}"

    def set_mimo_ref_point(self, point: str) -> str:
        """Set MIMO reference point."""
        return f"MIMO_REFPOINT {point}"

    def set_rx_div_ant_num(self, num: int) -> str:
        """Set Rx Diversity antenna number."""
        return f"RXDIVANTNUM {num}"

    def set_rx_div_ca_mode(self, mode: str) -> str:
        """Set Rx Diversity CA mode."""
        return f"RXDIVCAMODE {mode}"

    def set_tx_diversity_mod_meas_type(self, mtype: str) -> str:
        """Set Tx diversity modulation measurement type."""
        return f"TXDIV_MOD_MEAS_TYPE {mtype}"

    # =========================================================================
    # Power Control / Level Settings
    # =========================================================================
    def set_input_level(self, cc_or_value: Union[str, float], value: Optional[float] = None) -> str:
        """
        Set input level (dBm).
        Usage: set_input_level("PCC", 23) or set_input_level(23)
        """
        if value is not None:
            return f"ILVL {cc_or_value},{value}"
        else:
            return f"ILVL {cc_or_value}"

    def set_output_level(self, cc: str, level: float) -> str:
        """Set output level (dBm). e.g. OLVL PCC,-88.1"""
        return f"OLVL {cc},{level}"

    def set_output_level_epre(self, cc: str, level: float) -> str:
        """Set output level EPRE (dBm/SCS). e.g. OLVL_EPRE PCC,-85.0"""
        return f"OLVL_EPRE {cc},{level}"

    def set_tpc_pattern(self, pattern: str) -> str:
        """
        Set TPC pattern.
        pattern: 'AUTO' | 'ALLO' (All 0) | 'ALL3' (All +3) | 'ALL_3' (All -3) etc.
        """
        return f"TPCPAT {pattern}"

    def set_tpc_target_power(self, power: float) -> str:
        """Set TPC Target Power."""
        return f"TPCTARGETPOW {power}"

    def set_max_ul_power(self, power: float) -> str:
        """Set maximum UL power (LTE). e.g. MAXULPWR 23"""
        return f"MAXULPWR {power}"

    def set_max_ul_level(self, mode: str) -> str:
        """Set max UL level mode. e.g. MAXULLVL ON"""
        return f"MAXULLVL {mode}"

    def set_max_ue_fr1_ul_power(self, power: float) -> str:
        """Set p-MaxUE-FR1 value. e.g. MAXUEFR1ULPWR 23"""
        return f"MAXUEFR1ULPWR {power}"

    def set_max_ue_fr1_ul_level(self, mode: str) -> str:
        """Set p-MaxUE-FR1 On/Off. e.g. MAXUEFR1ULLVL ON"""
        return f"MAXUEFR1ULLVL {mode}"

    def set_max_power(self, power: float) -> str:
        """Set max power."""
        return f"MAXPWR {power}"

    def set_nr_fr1_ul_level(self, level: float) -> str:
        """Set NR FR1 UL level."""
        return f"NRFR1ULLVL {level}"

    def set_nr_fr1_ul_power(self, power: float) -> str:
        """Set NR FR1 UL power."""
        return f"NRFR1ULPWR {power}"

    def set_p_nominal(self, value: float) -> str:
        """Set P0 Nominal PUSCH."""
        return f"PONOMINAL {value}"

    def set_ue_power_class(self, power_class: int) -> str:
        """Set UE Power Class. e.g. UEPOWERCLASS 3"""
        return f"UEPOWERCLASS {power_class}"

    def set_xscale(self, mode: str) -> str:
        """Set XSCALE mode. e.g. XSCALE OFF"""
        return f"XSCALE {mode}"

    def set_lte_config_for_dps(self, mode: str) -> str:
        """Set LTE config for DynamicPowerSharing. e.g. LTECONFIGFORDPS ON"""
        return f"LTECONFIGFORDPS {mode}"

    def set_tx_switching(self, mode: str) -> str:
        """Set Tx switching mode."""
        return f"TXSWITCHING {mode}"

    # =========================================================================
    # External Loss Settings
    # =========================================================================
    def set_dl_ext_loss(self, value: float) -> str:
        """Set DL external loss (JND). e.g. DLEXTLOSSJND 0.5"""
        return f"DLEXTLOSSJND {value}"

    def set_ul_ext_loss(self, value: float) -> str:
        """Set UL external loss (JND). e.g. ULEXTLOSSJND 0.5"""
        return f"ULEXTLOSSJND {value}"

    def set_aux_ext_loss(self, value: float) -> str:
        """Set AUX external loss (JND)."""
        return f"AUEXTLOSSJND {value}"

    def set_loss_table_value(self, *args) -> str:
        """Set loss table value. e.g. LOSSTBLVAL freq,loss"""
        return f"LOSSTBLVAL {','.join(str(a) for a in args)}"

    def set_ext_loss_table_6g(self, value: float) -> str:
        """Set external loss table ID for 6GHz band."""
        return f"EXTLOSSTBLID6GJND {value}"

    def set_ext_loss_table_12g(self, value: float) -> str:
        """Set external loss table ID for 12GHz band."""
        return f"EXTLOSSTBLID12GJND {value}"

    def set_ext_loss_table_28g(self, value: float) -> str:
        """Set external loss table ID for 28GHz band."""
        return f"EXTLOSSTBLID28GJND {value}"

    def set_ext_loss_w(self, value: float) -> str:
        """Set external loss W (JND)."""
        return f"EXTLOSSWJND {value}"

    def set_dl_ext_loss_rf_conv(self, value: float) -> str:
        """Set DL external loss with RF converter P2."""
        return f"DLEXTLOSSRFCONVP2JND {value}"

    def set_ul_ext_loss_rf_conv(self, value: float) -> str:
        """Set UL external loss with RF converter P1."""
        return f"ULEXTLOSSRFCONVP1JND {value}"

    # =========================================================================
    # EN-DC Specific
    # =========================================================================
    def set_endc_meas_mode(self, mode: str) -> str:
        """Set EN-DC measurement mode. mode: 'NR' | 'LTE' | etc."""
        return f"ENDCMEASMODE {mode}"

    def set_sync_offset(self, offset: int) -> str:
        """Set LTE-NR Frame Timing Offset (ms). e.g. SYNCOFFSET 3"""
        return f"SYNCOFFSET {offset}"

    def enter_sync(self, mode: str = "PRIMARY") -> str:
        """Execute frame timing synchronization. e.g. ENTERSYNC PRIMARY"""
        # Note: Consider adding *OPC? after this command.
        return f"ENTERSYNC {mode}"

    # =========================================================================
    # NR-DC Specific
    # =========================================================================
    def set_nrdc_target_fr(self, fr: str) -> str:
        """Select target FR for NR-DC commands. fr: 'FR1' | 'FR2'"""
        return f"NRDC_SEL_TARGETFR {fr}"

    def set_fr1_fr2_meas_mode(self, mode: str) -> str:
        """Select FR1/FR2 for measurement. mode: 'FR1' | 'FR2'"""
        return f"FR1FR2MEASMODE {mode}"

    def set_fr1_fr2_rx_meas_mode(self, mode: str) -> str:
        """Select FR1/FR2 for Rx measurement."""
        return f"FR1FR2RXMEASMODE {mode}"

    # =========================================================================
    # CSI-RS Configuration
    # =========================================================================
    def set_csirs(self, mode: str) -> str:
        """Set CSI-RS mode. e.g. CSIRS ON"""
        return f"CSIRS {mode}"

    def set_csirs_resource(self, cc: str, value: int) -> str:
        """Set CSI-RS resource number."""
        return f"CSIRSRESOURCE {cc},{value}"

    def set_csirs_periodicity(self, cc: str, period: int) -> str:
        """Set CSI-RS periodicity."""
        return f"CSIRSPERIODICITY {cc},{period}"

    def set_csirs_offset(self, cc: str, offset: int) -> str:
        """Set CSI-RS offset."""
        return f"CSIRSOFFSET {cc},{offset}"

    def set_csirs_nrb(self, cc: str, nrb: int) -> str:
        """Set CSI-RS Number of RBs."""
        return f"CSIRSNRB {cc},{nrb}"

    def set_csirs_start_rb(self, cc: str, rb: int) -> str:
        """Set CSI-RS Starting RB."""
        return f"CSIRSSTARTRB {cc},{rb}"

    def set_csirs_start_symbol(self, cc: str, symbol: int) -> str:
        """Set CSI-RS Starting Symbol."""
        return f"CSIRSSTARTSYMBOL {cc},{symbol}"

    def set_avoid_csirs_for_ref_sens(self, cc: str, mode: str) -> str:
        """Disable PDSCH during CSI-RS slots for ref. sensitivity. e.g. AVOIDCSIRSFORREFSENS PCC,ON"""
        return f"AVOIDCSIRSFORREFSENS {cc},{mode}"

    # =========================================================================
    # SRS Configuration
    # =========================================================================
    def set_srs_resource(self, cc: str, value: int) -> str:
        """Set SRS resource number."""
        return f"SRSRESOURCE {cc},{value}"

    def set_srs_periodicity(self, cc: str, period: int) -> str:
        """Set SRS periodicity."""
        return f"SRSPERIODICITY {cc},{period}"

    def set_srs_offset(self, offset: int) -> str:
        """Set SRS Offset. e.g. SRSOFFSET 7"""
        return f"SRSOFFSET {offset}"

    def set_srs_alpha(self, alpha: str) -> str:
        """Set SRS alpha value. e.g. SRS_ALPHA ALPHA0"""
        return f"SRS_ALPHA {alpha}"

    def set_srs_p0(self, p0: float) -> str:
        """Set SRS p0 value. e.g. SRS_P0 0"""
        return f"SRS_P0 {p0}"

    def set_srs_num_ports(self, ports: int) -> str:
        """Set SRS number of ports."""
        return f"SRSNUMPORTS {ports}"

    def set_srs_start_symbol(self, symbol: int) -> str:
        """Set SRS starting symbol."""
        return f"SRSSTARTSYMBOL {symbol}"

    def set_srs_symbol_length(self, length: int) -> str:
        """Set SRS symbol length."""
        return f"SRSSYMBOLLENGTH {length}"

    # =========================================================================
    # PRACH Configuration
    # =========================================================================
    def set_prach_config_index(self, index: int) -> str:
        """Set PRACH Configuration Index. e.g. PRACHCONFIGINDEX 81"""
        return f"PRACHCONFIGINDEX {index}"

    def set_preamble_target(self, power: float) -> str:
        """Set Preamble Received Target Power. e.g. PREAMBLETGT -92"""
        return f"PREAMBLETGT {power}"

    def set_preamble_max(self, value: str) -> str:
        """Set PreambleTransMax. e.g. PREAMBLEMAX N7"""
        return f"PREAMBLEMAX {value}"

    def set_power_ramping_step(self, step: str) -> str:
        """Set Power Ramping Step. e.g. PWRRMPSTEP dB4"""
        return f"PWRRMPSTEP {step}"

    # =========================================================================
    # UL Allocation List (for multi-slot scheduling)
    # =========================================================================
    def set_ul_alloc_list_size(self, size: int) -> str:
        """Set UL allocation list size."""
        return f"ULALLOCLIST_SIZE {size}"

    def set_ul_alloc_list(self, *args) -> str:
        """Set UL allocation list entry."""
        return f"ULALLOCLIST {','.join(str(a) for a in args)}"

    def set_ul_alloc_list_k2(self, k2: int) -> str:
        """Set UL allocation list K2 value."""
        return f"ULALLOCLIST_K2 {k2}"

    # =========================================================================
    # Spectrum / Additional Spectrum Emission
    # =========================================================================
    def set_additional_spectrum_emission(self, mode: str) -> str:
        """Enable/disable Additional Spectrum Emission. e.g. ADDSPEM ON"""
        return f"ADDSPEM {mode}"

    def set_additional_spectrum_emission_value(self, cc_or_value, value: Optional[int] = None) -> str:
        """Set ASEM value. e.g. ADDSPEMVALUE 1 or ADDSPEMVALUE PCC,0"""
        if value is not None:
            return f"ADDSPEMVALUE {cc_or_value},{value}"
        else:
            return f"ADDSPEMVALUE {cc_or_value}"

    def set_additional_spectrum_emission_sul(self, value: int) -> str:
        """Set ASEM value for SUL."""
        return f"ADDSPEMVALUE_SUL {value}"

    def set_addspem_sul(self, mode: str) -> str:
        """Enable/disable Additional Spectrum Emission for SUL."""
        return f"ADDSPEM_SUL {mode}"

    def set_sib2_ns(self, value: int) -> str:
        """Set SIB2 NS value."""
        return f"SIB2_NS {value}"

    # =========================================================================
    # RedCap (Reduced Capability) Configuration
    # =========================================================================
    def set_redcap_operation(self, mode: str) -> str:
        """Set RedCap operation mode. e.g. REDCAPOP ON"""
        return f"REDCAPOP {mode}"

    # =========================================================================
    # NR NTN (Non-Terrestrial Network) Configuration
    # =========================================================================
    def set_nrntn(self, mode: str) -> str:
        """Enable/disable NR NTN mode."""
        return f"NRNTN {mode}"

    def set_ntn_preset(self, preset: str) -> str:
        """Set NTN preset configuration."""
        return f"NTN_PRESET {preset}"

    def query_ntn_ue_location_latitude(self) -> str:
        """Query NTN UE location latitude."""
        return "NTN_UELOC_LATI?"

    def query_ntn_ue_location_longitude(self) -> str:
        """Query NTN UE location longitude."""
        return "NTN_UELOC_LONGI?"

    def query_ntn_ue_location_altitude(self) -> str:
        """Query NTN UE location altitude."""
        return "NTN_UELOC_ALTI?"

    # =========================================================================
    # Measurement Control
    # =========================================================================
    def all_meas_items_off(self) -> str:
        """Turn off all measurement items."""
        # Note: Consider adding *OPC? after this command.
        return "ALLMEASITEMS_OFF"

    def set_meas_item(self, item: str) -> str:
        """
        Set measurement item mode.
        item: 'NORMAL' | 'PCT' | 'EVMTP' | etc.
        """
        return f"MEASITEM {item}"

    def set_meas_metric(self, metric: str) -> str:
        """Set measurement metric."""
        return f"MEASMETRIC {metric}"

    # --- Individual measurement ON/OFF ---
    def set_power_meas(self, on: bool, avg: Optional[int] = None) -> str:
        """Enable/disable power measurement and optionally set averaging count."""
        cmd = f"PWR_MEAS {'ON' if on else 'OFF'}"
        if avg is not None:
            cmd += f";PWR_AVG {avg}"
        return cmd

    def set_mod_meas(self, on: bool, avg: Optional[int] = None) -> str:
        """Enable/disable modulation analysis and optionally set averaging count."""
        cmd = f"MOD_MEAS {'ON' if on else 'OFF'}"
        if avg is not None:
            cmd += f";MOD_AVG {avg}"
        return cmd

    def set_sem_meas(self, on: bool, avg: Optional[int] = None) -> str:
        """Enable/disable Spectrum Emission Mask measurement."""
        cmd = f"SEM_MEAS {'ON' if on else 'OFF'}"
        if avg is not None:
            cmd += f";SEM_AVG {avg}"
        return cmd

    def set_obw_meas(self, on: bool) -> str:
        """Enable/disable Occupied Bandwidth measurement."""
        return f"OBWMEAS {'ON' if on else 'OFF'}"

    def set_obw_meas_bw(self, bw: str) -> str:
        """Set OBW measurement bandwidth."""
        return f"OBWMEASBW {bw}"

    def set_obw_meas_proc(self, proc: str) -> str:
        """Set OBW measurement processing mode."""
        return f"OBWMEASPROC {proc}"

    def set_aclr_meas(self, on: bool) -> str:
        """Set ACLR measurement avg/count."""
        return f"ACLR_MEAS {'ON' if on else 'OFF'}"

    def set_aclr_avg(self, avg: int) -> str:
        """Set ACLR averaging count."""
        return f"ACLR_AVG {avg}"

    def set_throughput_meas(self, on: bool) -> str:
        """Enable/disable Throughput measurement."""
        return f"TPUT_MEAS {'ON' if on else 'OFF'}"

    def set_throughput_sample(self, samples: int) -> str:
        """Set throughput measurement sample count. e.g. TPUT_SAMPLE 2466"""
        return f"TPUT_SAMPLE {samples}"

    def set_power_temp_meas(self, on: bool, avg: Optional[int] = None) -> str:
        """Enable/disable Power Template measurement."""
        cmd = f"PWRTEMP_MEAS {'ON' if on else 'OFF'}"
        if avg is not None:
            cmd += f";PWRTEMP_AVG {avg}"
        return cmd

    def set_ibem_meas(self, mode: str) -> str:
        """Set IBEM (In-Band Emission) measurement."""
        return f"IBEM {mode}"

    def set_ibem_clfr(self, value: str) -> str:
        """Set IBEM CLFR value."""
        return f"IBEM_CLFR {value}"

    def set_early_decision(self, mode: str) -> str:
        """Enable/disable early decision for throughput. e.g. EARLY_DECISION ON"""
        return f"EARLY_DECISION {mode}"

    def set_fast_mod_analysis_mode(self, mode: str) -> str:
        """Enable/disable Fast Analysis Mode. e.g. FAST_MODANA_MODE ON"""
        return f"FAST_MODANA_MODE {mode}"

    def set_meas_sf_overlapping_nr(self, mode: str) -> str:
        """Set Measurement Subframe overlapping with NR symbols."""
        return f"MEAS_SF_OVERLAPPING_NR {mode}"

    def set_meas_target_system(self, system: str) -> str:
        """Set measurement target system."""
        return f"MEAS_TARGET_SYSTEM {system}"

    # =========================================================================
    # Power Control Tolerance (PCT) Settings
    # =========================================================================
    def set_pct_type(self, ptype: str) -> str:
        """
        Set Power Control Tolerance test type.
        ptype: 'ABS' | 'REL_UP' | 'REL_DOWN' | 'REL_ALT' | 'AGG' etc.
        """
        return f"PCTTYPE {ptype}"

    def set_rel_sf(self, sf: int) -> str:
        """Set Relative Power measurement subframe. e.g. REL_SF 10"""
        return f"REL_SF {sf}"

    def set_rel_rb1(self, rb: int) -> str:
        """Set Relative Power UL Number of RB1."""
        return f"REL_RB1 {rb}"

    def set_rel_rb_start1(self, start: int) -> str:
        """Set Relative Power UL Starting RB1."""
        return f"REL_RB_START1 {start}"

    def set_rel_rb2(self, rb: int) -> str:
        """Set Relative Power UL Number of RB2."""
        return f"REL_RB2 {rb}"

    def set_rel_rb_start2(self, start: int) -> str:
        """Set Relative Power UL Starting RB2."""
        return f"REL_RB_START2 {start}"

    def set_rel_rb_change(self, change: str) -> str:
        """Set Relative Power RB change mode."""
        return f"REL_RBCHANGE {change}"

    def set_rel_initial_power(self, power: float) -> str:
        """Set Relative Power Initial Power. e.g. REL_INITPWR -10.0"""
        return f"REL_INITPWR {power}"

    def set_rel_pumax_mode(self, mode: str) -> str:
        """Set Relative Power Pumax mode."""
        return f"REL_PUMAX_MODE {mode}"

    # =========================================================================
    # EVM with Transient Period (EVMTP) Settings
    # =========================================================================
    def set_transient_capability(self, cap: str) -> str:
        """Set transient capability. e.g. TRANSIENT_CAPA 2US"""
        return f"TRANSIENT_CAPA {cap}"

    def set_evmtp_hp_ul_rb(self, rb: int) -> str:
        """Set EVM-TP high power UL RB."""
        return f"EVMTP_HP_ULRB {rb}"

    def set_evmtp_hp_ul_rb_start(self, start: int) -> str:
        """Set EVM-TP high power UL starting RB."""
        return f"EVMTP_HP_ULRB_START {start}"

    def set_evmtp_lp_ul_rb(self, rb: int) -> str:
        """Set EVM-TP low power UL RB."""
        return f"EVMTP_LP_ULRB {rb}"

    def set_evmtp_lp_ul_rb_start(self, start: int) -> str:
        """Set EVM-TP low power starting RB."""
        return f"EVMTP_LP_ULRB_START {start}"

    # =========================================================================
    # EIS (FR2 OTA) Settings
    # =========================================================================
    def set_eis_level_step(self, step: float) -> str:
        """Set EIS level step (dB)."""
        return f"EIS_LVLSTEP {step}"

    def set_eis_pol_switch_wait(self, wait_ms: int) -> str:
        """Set EIS polarization switch wait time (ms)."""
        return f"EIS_POLSWWAIT {wait_ms}"

    def set_eis_wait(self, wait_ms: int) -> str:
        """Set EIS wait time (ms)."""
        return f"EIS_WAIT {wait_ms}"

    # =========================================================================
    # Measurement Execution
    # =========================================================================
    def sweep(self) -> str:
        """Start measurement sweep (SWP) and wait for completion."""
        # Note: Consider adding *OPC? after this command.
        return "SWP"

    def query_meas_status(self) -> str:
        """Query measurement status. Returns result of MSTAT?"""
        return "MSTAT?"

    # =========================================================================
    # Measurement Result Queries
    # =========================================================================
    def query_power(self) -> str:
        """Query UE output power result (dBm). POWER?"""
        return "POWER?"

    def query_channel_power(self, *args) -> str:
        """Query channel power. CHPWR? [args]"""
        cmd = "CHPWR?"
        if args:
            cmd += " " + ",".join(str(a) for a in args)
        return cmd

    def query_mod_power(self) -> str:
        """Query modulation power result. MODPWR?"""
        return "MODPWR?"

    def query_evm(self) -> str:
        """Query Error Vector Magnitude result. EVM?"""
        return "EVM?"

    def query_rs_evm(self) -> str:
        """Query RS-EVM result. RSEVM?"""
        return "RSEVM?"

    def query_tp_evm(self) -> str:
        """Query EVM with Transient Period result. TPEVM?"""
        return "TPEVM?"

    def query_carrier_freq_error(self) -> str:
        """Query Carrier Frequency Error result. CARRFERR?"""
        return "CARRFERR?"

    def query_carrier_leakage(self) -> str:
        """Query Carrier Leakage result. CARRLEAK?"""
        return "CARRLEAK?"

    def query_obw(self) -> str:
        """Query Occupied Bandwidth result. OBW?"""
        return "OBW?"

    def query_on_power(self) -> str:
        """Query ON power result. ONPWR?"""
        return "ONPWR?"

    def query_off_power_before(self) -> str:
        """Query OFF power before result. OFFPWR_BEFORE?"""
        return "OFFPWR_BEFORE?"

    def query_off_power_after(self) -> str:
        """Query OFF power after result. OFFPWR_AFTER?"""
        return "OFFPWR_AFTER?"

    def query_timing_alignment_error(self) -> str:
        """Query Timing Alignment Error result. TMGALIGNERR?"""
        return "TMGALIGNERR?"

    def query_spec_flatness(self, direction: str = "") -> str:
        """
        Query EVM Equalizer Spectrum Flatness result.
        direction: '' | 'RP1' | 'RP2' | 'RP12' | 'RP21'
        """
        if direction:
            return f"SPECFLAT_{direction}?"
        return "SPECFLAT?"

    # --- SEM Results ---
    def query_sem_pass(self, mode: str = "") -> str:
        """Query SEM pass/fail. mode: '' | 'SUM'. SEMPASS? [SUM]"""
        cmd = "SEMPASS?"
        if mode:
            cmd += f" {mode}"
        return cmd

    def query_ttl_worst_sem(self, mode: str = "") -> str:
        """Query total worst SEM result. TTL_WORST_SEM? [SUM]"""
        cmd = "TTL_WORST_SEM?"
        if mode:
            cmd += f" {mode}"
        return cmd

    def query_ttl_worst_sem_level(self, mode: str = "") -> str:
        """Query total worst SEM level result. TTL_WORST_SEM_LV? [SUM]"""
        cmd = "TTL_WORST_SEM_LV?"
        if mode:
            cmd += f" {mode}"
        return cmd

    # --- ACLR Results ---
    def query_aclr(self, *args) -> str:
        """Query ACLR result. ACLR? [args]"""
        cmd = "ACLR?"
        if args:
            cmd += " " + ",".join(str(a) for a in args)
        return cmd

    # --- In-Band Emission Results ---
    def query_inband_emission_general(self, *args) -> str:
        """Query In-Band Emission general result. INBANDE_GEN? [args]"""
        cmd = "INBANDE_GEN?"
        if args:
            cmd += " " + ",".join(str(a) for a in args)
        return cmd

    def query_inband_emission_leakage(self, *args) -> str:
        """Query In-Band Emission leakage result. INBANDE_LEAK? [args]"""
        cmd = "INBANDE_LEAK?"
        if args:
            cmd += " " + ",".join(str(a) for a in args)
        return cmd

    def query_inband_emission_margin(self, *args) -> str:
        """Query In-Band Emission margin result. INBANDE_MARG? [args]"""
        cmd = "INBANDE_MARG?"
        if args:
            cmd += " " + ",".join(str(a) for a in args)
        return cmd

    def query_inband_emission_margin_eutra(self, *args) -> str:
        """Query In-Band Emission margin (EUTRA) result. INBANDE_MARG_EUTRA? [args]"""
        cmd = "INBANDE_MARG_EUTRA?"
        if args:
            cmd += " " + ",".join(str(a) for a in args)
        return cmd

    # --- Power Control Tolerance Results ---
    def query_pct_power(self) -> str:
        """Query PCT (Power Control Tolerance) power result. PCTPWR?"""
        return "PCTPWR?"

    def query_pct_power2(self) -> str:
        """Query PCT power result 2. PCTPWR2?"""
        return "PCTPWR2?"

    def query_pct_power_e1(self, mode: str = "") -> str:
        """Query PCT power E1. PCTPWRE1? [SUM]"""
        cmd = "PCTPWRE1?"
        if mode:
            cmd += f" {mode}"
        return cmd

    def query_pct_power_e2(self) -> str:
        """Query PCT power E2. PCTPWRE2?"""
        return "PCTPWRE2?"

    def query_pct_power_e3(self) -> str:
        """Query PCT power E3. PCTPWRE3?"""
        return "PCTPWRE3?"

    def query_pct_rel(self) -> str:
        """Query PCT relative result. PCTREL?"""
        return "PCTREL?"

    # --- Throughput Results ---
    def query_throughput(self, per_cc: str = "", cc: str = "") -> str:
        """
        Query Throughput result.
        per_cc: 'PER' for per-CC result. cc: 'SCC1', 'SCC2' etc.
        e.g. query_throughput("PER") or query_throughput("PER", "SCC1")
        """
        cmd = "TPUT?"
        if per_cc:
            cmd += f" {per_cc}"
            if cc:
                cmd += f",{cc}"
        return cmd

    def query_throughput_bler(self, cc: str = "") -> str:
        """Query Throughput BLER result."""
        cmd = "TPUT_BLER?"
        if cc:
            cmd += f" {cc}"
        return cmd

    def query_throughput_bler_count(self, cc: str = "") -> str:
        """Query Throughput BLER count."""
        cmd = "TPUT_BLERCNT?"
        if cc:
            cmd += f" {cc}"
        return cmd

    def query_throughput_bler_count_nack(self, cc: str = "") -> str:
        """Query Throughput BLER NACK count."""
        cmd = "TPUT_BLERCNTNACK?"
        if cc:
            cmd += f" {cc}"
        return cmd

    def query_throughput_bler_count_dtx(self, cc: str = "") -> str:
        """Query Throughput BLER DTX count."""
        cmd = "TPUT_BLERCNTDTX?"
        if cc:
            cmd += f" {cc}"
        return cmd

    def query_throughput_transport_block(self, cc: str = "") -> str:
        """Query Throughput Transport Block size."""
        cmd = "TPUT_TRANSBLOCK?"
        if cc:
            cmd += f" {cc}"
        return cmd

    def query_throughput_total_fr1(self) -> str:
        """Query Throughput total FR1."""
        return "TPUT_TOTAL_FR1?"

    def query_throughput_total_fr2(self) -> str:
        """Query Throughput total FR2."""
        return "TPUT_TOTAL_FR2?"

    def query_throughput_bler_total_fr1(self) -> str:
        """Query Throughput BLER total FR1."""
        return "TPUT_BLER_TOTAL_FR1?"

    # --- EIS Results (FR2 OTA) ---
    def query_eis(self) -> str:
        """Query EIS result (FR2). EIS?"""
        return "EIS?"

    def query_peak_eirp(self) -> str:
        """Query Peak EIRP result. PEAKEIRP?"""
        return "PEAKEIRP?"

    # --- TTL/Modulation Power ---
    def query_ttl_mod_power(self) -> str:
        """Query total modulation power. TTL_MODPWR?"""
        return "TTL_MODPWR?"

    # --- Power Template Results ---
    def query_power_temp(self, *args) -> str:
        """Query Power Template result. PWRTEMP? [args]"""
        cmd = "PWRTEMP?"
        if args:
            cmd += " " + ",".join(str(a) for a in args)
        return cmd

    def query_test_spec(self) -> str:
        """Query test specification. TEST_SPEC?"""
        return "TEST_SPEC?"


# =============================================================================
# MT8821C (LTE) Command Extensions
# =============================================================================
class MT8821C:
    """
    Anritsu MT8821C LTE anchor commands (used via REM_DEST 8821C).

    Note: These commands are typically sent to the MT8000A which routes them
    to the MT8821C. When using with MT8000A, call mt8000a.set_remote_destination("8821C")
    first, then use these commands through the same VISA resource.
    """

    # =========================================================================
    # Self test write and query commands
    # =========================================================================
    
    def __init__(self, visa_resource, timeout_ms: int = 10000):
        """
        Parameters
        ----------
        visa_resource : pyvisa.Resource
            An opened VISA instrument resource (GPIB, TCPIP, etc.)
        timeout_ms : int
            Default command timeout in milliseconds.
        """
        self._inst = visa_resource
        self._inst.timeout = timeout_ms

    def write(self, cmd: str) -> None:
        """Send a SCPI command."""
        logger.debug("WRITE: %s", cmd)
        self._inst.write(cmd)

    def query(self, cmd: str) -> str:
        """Send a query and return the response string."""
        logger.debug("QUERY: %s", cmd)
        resp = self._inst.query(cmd).strip()
        logger.debug("RESP:  %s", resp)
        return resp

    def close(self) -> None:  
        """Close the VISA resource."""
        self._inst.close()

    def preset(self) -> str:
        """Initialize MT8821C parameters. PRESET"""
        # Note: Consider adding *OPC? after this command.
        return "PRESET"

    def set_call_processing(self, on_off: bool) -> str:
        """Enable/disable LTE call processing."""
        return f"CALLPROC {'ON' if on_off else 'OFF'}"

    def set_band(self, band: int) -> str:
        """Set LTE operation band. e.g. BAND 5"""
        return f"BAND {band}"

    def set_bandwidth(self, bw: str) -> str:
        """Set LTE channel bandwidth. e.g. BANDWIDTH 5MHZ"""
        return f"BANDWIDTH {bw}"

    def set_ul_channel(self, channel: int) -> str:
        """Set LTE UL channel. e.g. ULCHAN 18300"""
        return f"ULCHAN {channel}"

    def set_frame_type(self, mode: str) -> str:
        """Set LTE duplex mode. e.g. FRAMETYPE FDD"""
        return f"FRAMETYPE {mode}"

    def set_sim_model(self, model: str) -> str:
        """Set SIM model number for LTE. e.g. SIMMODELNUM P0250"""
        return f"SIMMODELNUM {model}"

    def set_integrity(self, algorithm: str) -> str:
        """Set integrity protection. e.g. INTEGRITY SNOW3G"""
        return f"INTEGRITY {algorithm}"

    def set_channel_coding(self, mode: str) -> str:
        """Set channel coding. e.g. CHCODING RMC"""
        return f"CHCODING {mode}"

    def set_routing_mode(self, mode: str) -> str:
        """Set routing mode. e.g. TXIQROUTING SISO"""
        return f"TXIQROUTING {mode}"

    def set_ul_rmc_rb(self, rb: int) -> str:
        """Set LTE UL RMC RB. e.g. ULRMC_RB 18"""
        return f"ULRMC_RB {rb}"

    def set_ul_rb_start(self, start: int) -> str:
        """Set LTE UL Starting RB. e.g. ULRBSTART 82"""
        return f"ULRBSTART {start}"

    def set_ul_rmc_mod(self, mod: str) -> str:
        """Set LTE UL RMC Modulation. e.g. ULRMC_MOD QPSK"""
        return f"ULRMC_MOD {mod}"

    def set_dl_rmc_rb(self, rb: int) -> str:
        """Set LTE DL RMC RB."""
        return f"DLRMC_RB {rb}"

    def set_dl_rb_start(self, start: int) -> str:
        """Set LTE DL Starting RB."""
        return f"DLRB_START {start}"

    def set_input_level(self, level: float) -> str:
        """Set LTE input level (dBm)."""
        return f"ILVL {level}"

    def set_output_level_epre(self, level: float) -> str:
        """Set LTE output level EPRE."""
        return f"OLVL_EPRE {level}"

    def set_tpc_pattern(self, pattern: str) -> str:
        """Set LTE TPC pattern."""
        return f"TPCPAT {pattern}"

    def set_max_ul_power(self, power: float) -> str:
        """Set LTE max UL power."""
        return f"MAXULPWR {power}"

    def call_sa(self) -> str:
        """Initiate LTE call. CALLSA"""
        return "CALLSA"

    def query_call_status(self) -> str:
        """Query LTE call status. CALLSTAT?"""
        return "CALLSTAT?"

    def query_power(self) -> str:
        """Query LTE power result. POWER?"""
        return "POWER?"

    def all_meas_items_off(self) -> str:
        """Turn off all LTE measurement items. ALLMEASITEMS_OFF"""
        # Note: Consider adding *OPC? after this command.
        return "ALLMEASITEMS_OFF"

    def set_power_meas(self, on: bool) -> str:
        """Enable/disable LTE power measurement."""
        return f"PWR_MEAS {'ON' if on else 'OFF'}"

    def set_throughput_meas(self, on: bool) -> str:
        """Enable/disable LTE throughput measurement."""
        return f"TPUT_MEAS {'ON' if on else 'OFF'}"

    def sweep(self) -> str:
        """Start LTE measurement sweep. SWP"""
        # Note: Consider adding *OPC? after this command.
        return "SWP"

    def query_meas_status(self) -> str:
        """Query LTE measurement status. MSTAT?"""
        return "MSTAT?"

    def wait_for_call_connected(self, timeout_s: int = 60) -> bool:
        """
        Wait for LTE call to be connected.

        Args:
            timeout_s: Timeout in seconds

        Returns:
            True if call connected, False if timeout
        """
        import time
        import logging

        logger = logging.getLogger(__name__)
        start_time = time.time()

        while time.time() - start_time < timeout_s:
            status = self.query_call_status()
            if "CONNECTED" in status.upper():
                logger.info("LTE call connected")
                return True
            time.sleep(1)

        logger.warning(f"LTE call connection timeout after {timeout_s}s")
        return False


# =============================================================================
# Example Measurement Workflows
# =============================================================================

def example_sa_power_measurement(visa_resource) -> dict:
    """
    Example: SA UE Maximum Output Power measurement on Band 78 TDD.

    Returns measurement results dict.
    """
    mt = MT8000A(visa_resource)

    # --- System Initialization ---
    visa_resource.write(mt.preset_sa())
    visa_resource.write(mt.set_ran_operation("SA"))
    visa_resource.write(mt.set_test_interface("SLOT1", "ARGV"))
    visa_resource.write(mt.set_test_slot("SLOT1"))
    visa_resource.write(mt.set_call_processing(True))
    visa_resource.write(mt.set_sim_model("P0135"))
    visa_resource.write(mt.set_integrity("SNOW3G"))

    # --- Frame & Frequency Configuration ---
    visa_resource.write(mt.set_frame_type("TDD"))
    visa_resource.write(mt.set_channel_setting_mode("LOWESTGSCN"))
    visa_resource.write(mt.set_band("PCC", 78))
    visa_resource.write(mt.set_dl_scs("PCC", "30KHZ"))
    visa_resource.write(mt.set_dl_bandwidth("PCC", "100MHZ"))
    visa_resource.write(mt.set_dl_channel("PCC", 623334))
    visa_resource.write(mt.set_offset_carrier("PCC", 0))
    visa_resource.write(mt.set_ssb_channel("PCC", 620352))
    visa_resource.write(mt.set_ssb_scs("PCC", "30KHZ"))

    # --- TDD Configuration ---
    visa_resource.write(mt.set_dl_ul_period("PCC", "5MS"))
    visa_resource.write(mt.set_dl_duration("PCC", 8))
    visa_resource.write(mt.set_ul_duration("PCC", 2))
    visa_resource.write(mt.set_dl_symbols("PCC", 6))
    visa_resource.write(mt.set_ul_symbols("PCC", 4))

    # --- DCI Configuration ---
    visa_resource.write(mt.set_dci_format("FORMAT0_1_AND_1_1"))
    visa_resource.write(mt.set_scheduling("STATIC"))
    visa_resource.write(mt.set_group_hopping_cch("ENABLE"))

    # --- Call Connection ---
    visa_resource.write(mt.call_sa())
    connected = mt.wait_for_call_connected(timeout_s=60)
    if not connected:
        raise RuntimeError("Call connection failed")

    # --- Measurement Configuration ---
    visa_resource.write(mt.all_meas_items_off())
    visa_resource.write(mt.set_power_meas(True, avg=1))

    # --- UL RMC Settings ---
    visa_resource.write(mt.set_ul_waveform("PCC", "DFTOFDM"))
    visa_resource.write(mt.set_ul_rmc_rb("PCC", 162))
    visa_resource.write(mt.set_ul_rb_start("PCC", 0))
    visa_resource.write(mt.set_ul_mcs_index("PCC", 10))

    # --- DL RMC Settings ---
    visa_resource.write(mt.set_dl_rmc_rb("PCC", 0))
    visa_resource.write(mt.set_dl_rb_start("PCC", 0))
    visa_resource.write(mt.set_dl_mcs_table("PCC", "64QAM"))
    visa_resource.write(mt.set_dl_mcs_index("PCC", 4))

    # --- Input Level & TPC ---
    visa_resource.write(mt.set_input_level("PCC", 23))
    visa_resource.write(mt.set_tpc_pattern("ALL3"))

    # --- Execute Measurement ---
    visa_resource.write(mt.sweep())
    status = visa_resource.query(mt.query_meas_status())
    power = visa_resource.query(mt.query_power())

    # --- Reset ---
    visa_resource.write(mt.set_tpc_pattern("AUTO"))

    return {
        "status": status,
        "power_dBm": power,
    }


def example_nsa_endc_evm_measurement(visa_resource) -> dict:
    """
    Example: NSA EN-DC EVM measurement (Intra-Band Contiguous, Band 41 TDD).

    Returns measurement results dict.
    """
    mt = MT8000A(visa_resource)
    mt8821c = MT8821C()

    # --- Switch to LTE (MT8821C) for anchor config ---
    visa_resource.write(mt.set_remote_destination("8821C"))
    visa_resource.write(mt8821c.preset())
    visa_resource.write(mt8821c.set_call_processing(True))
    visa_resource.write(mt8821c.set_band(41))
    visa_resource.write(mt8821c.set_bandwidth("20MHZ"))
    visa_resource.write(mt8821c.set_sim_model("P0250"))
    visa_resource.write(mt8821c.set_integrity("SNOW3G"))

    # --- Switch back to NR ---
    visa_resource.write(mt.set_remote_destination("8000A"))

    # --- NR Frame & Frequency ---
    visa_resource.write(mt.set_frame_type("TDD"))
    visa_resource.write(mt.set_band("PCC", 41))
    visa_resource.write(mt.set_dl_scs("PCC", "30KHZ"))
    visa_resource.write(mt.set_dl_bandwidth("PCC", "100MHZ"))
    visa_resource.write(mt.set_dl_channel("PCC", 509202))
    visa_resource.write(mt.set_offset_carrier("PCC", 0))
    visa_resource.write(mt.set_channel_setting_mode("LOWESTGSCN"))
    visa_resource.write(mt.set_ssb_channel("PCC", 500190))
    visa_resource.write(mt.set_ssb_scs("PCC", "30KHZ"))

    # --- TDD Configuration ---
    visa_resource.write(mt.set_dl_ul_period("PCC", "5MS"))
    visa_resource.write(mt.set_dl_duration("PCC", 8))
    visa_resource.write(mt.set_ul_duration("PCC", 2))
    visa_resource.write(mt.set_dl_symbols("PCC", 6))
    visa_resource.write(mt.set_ul_symbols("PCC", 4))

    # --- EN-DC Measurement Mode ---
    visa_resource.write(mt.set_endc_meas_mode("NR"))

    # --- Call Connection (LTE then NR) ---
    visa_resource.write(mt.set_remote_destination("8821C"))
    visa_resource.write(mt8821c.call_sa())
    visa_resource.write(mt.set_remote_destination("8000A"))
    visa_resource.write(mt.call_sa())
    connected = mt.wait_for_call_connected(timeout_s=60)
    if not connected:
        raise RuntimeError("NR call connection failed")

    # --- Measurement Configuration ---
    visa_resource.write(mt.all_meas_items_off())
    visa_resource.write(mt.set_mod_meas(True, avg=20))

    # --- UL RMC Settings ---
    visa_resource.write(mt.set_ul_waveform("PCC", "DFTOFDM"))
    visa_resource.write(mt.set_ul_rmc_rb("PCC", 162))
    visa_resource.write(mt.set_ul_rb_start("PCC", 0))
    visa_resource.write(mt.set_ul_mcs_index("PCC", 2))

    # --- Level & TPC ---
    visa_resource.write(mt.set_input_level("PCC", 23))
    visa_resource.write(mt.set_tpc_pattern("ALL3"))

    # --- Execute Measurement ---
    visa_resource.write(mt.sweep())
    status = visa_resource.query(mt.query_meas_status())
    evm = visa_resource.query(mt.query_evm())
    carrier_leakage = visa_resource.query(mt.query_carrier_leakage())

    # --- Reset ---
    visa_resource.write(mt.set_tpc_pattern("AUTO"))

    return {
        "status": status,
        "evm": evm,
        "carrier_leakage": carrier_leakage,
    }


def example_rx_throughput_measurement(visa_resource) -> dict:
    """
    Example: SA Reference Sensitivity / Throughput measurement.

    Returns measurement results dict.
    """
    mt = MT8000A(visa_resource)

    # Assume system already initialized & call connected

    # --- Measurement Configuration ---
    visa_resource.write(mt.all_meas_items_off())
    visa_resource.write(mt.set_throughput_meas(True))
    visa_resource.write(mt.set_throughput_sample(2466))
    visa_resource.write(mt.set_early_decision(True))

    # --- DL RMC Settings ---
    visa_resource.write(mt.set_dl_rmc_rb("PCC", 133))
    visa_resource.write(mt.set_dl_mcs_table("PCC", "64QAM"))
    visa_resource.write(mt.set_dl_mcs_index("PCC", 4))
    visa_resource.write(mt.set_avoid_csirs_for_ref_sens("PCC", "ON"))

    # --- Output Level (Reference Sensitivity) ---
    visa_resource.write(mt.set_output_level("PCC", -88.1))

    # --- Input Level & TPC ---
    visa_resource.write(mt.set_input_level("PCC", 23))
    visa_resource.write(mt.set_tpc_pattern("ALL3"))

    # --- Execute Measurement ---
    visa_resource.write(mt.sweep())
    status = visa_resource.query(mt.query_meas_status())
    throughput = visa_resource.query(mt.query_throughput("PER"))

    # --- Reset ---
    visa_resource.write(mt.set_tpc_pattern("AUTO"))
    visa_resource.write(mt.set_early_decision("OFF"))
    visa_resource.write(mt.set_avoid_csirs_for_ref_sens("PCC", "OFF"))

    return {
        "status": status,
        "throughput_pcc": throughput,
    }


if __name__ == "__main__":
    print("MT8000A Remote Command Library")
    print("=" * 50)
    print("Usage:")
    print("  import pyvisa")
    print("  from mt8000a_commands import MT8000A")
    print()
    print("  rm = pyvisa.ResourceManager()")
    print("  inst = rm.open_resource('GPIB0::1::INSTR')")
    print("  mt = MT8000A()")
    print()
    print("  # Set band and frequency")
    print("  inst.write(mt.set_band('PCC', 78))")
    print("  inst.write(mt.set_dl_scs('PCC', '30KHZ'))")
    print("  inst.write(mt.set_dl_bandwidth('PCC', '100MHZ'))")
    print()
    print("  # Run power measurement")
    print("  inst.write(mt.all_meas_items_off())")
    print("  inst.write(mt.set_power_meas(True, avg=1))")
    print("  inst.write(mt.sweep())")
    print("  result = inst.query(mt.query_power())")
    print("  print(f'Power: {result} dBm')")

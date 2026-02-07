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
    mt.preset_sa()
    mt.set_ran_operation("SA")
    mt.set_frame_type("TDD")
    mt.set_band("PCC", 78)
    mt.set_dl_scs("PCC", "30KHZ")
    mt.set_dl_bandwidth("PCC", "100MHZ")
    mt.call_sa()
    mt.wait_for_call_connected()

    # Example: Power measurement
    mt.all_meas_items_off()
    mt.set_power_meas(True)
    mt.sweep()
    result = mt.query_power()
"""

from __future__ import annotations

import time
import logging
from typing import Optional, Union

logger = logging.getLogger(__name__)


class InstrumentBase:
    """Thin wrapper around a VISA instrument resource for SCPI communication."""

    def __init__(self, visa_resource, timeout_ms: int = 30000):
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

    def opc(self) -> str:
        """Wait for operation complete (*OPC?)."""
        return self.query("*OPC?")

    def close(self) -> None:
        """Close the VISA resource."""
        self._inst.close()


class MT8000A(InstrumentBase):
    """
    Anritsu MT8000A NR Test Station remote commands.

    Commands are grouped by functional category for clarity.
    Most setter methods accept carrier component arguments like 'PCC', 'SCC1', etc.
    """

    # =========================================================================
    # System / Initialization
    # =========================================================================
    def preset(self) -> None:
        """Initialize all parameters (NSA mode)."""
        self.write("PRESET")
        self.opc()

    def preset_sa(self) -> None:
        """Initialize all parameters for SA mode."""
        self.write("PRESET_SA")
        self.opc()

    def set_ran_operation(self, mode: str) -> None:
        """Set RAN operation mode. mode: 'SA' | 'NSA'"""
        self.write(f"RANOP {mode}")

    def set_remote_destination(self, dest: str) -> None:
        """
        Switch remote command destination.
        dest: '8000A' | '8821C' | 'LTE' | 'NR'
        """
        self.write(f"REM_DEST {dest}")

    def set_test_interface(self, slot: str, interface: str = "ARGV") -> None:
        """Set test interface. e.g. TESTIF SLOT1,ARGV"""
        self.write(f"TESTIF {slot},{interface}")

    def set_test_slot(self, slot: str, cc: Optional[str] = None) -> None:
        """Set test slot. e.g. TESTSLOT SLOT1 or TESTSLOT PCC,SLOT1"""
        if cc:
            self.write(f"TESTSLOT {cc},{slot}")
        else:
            self.write(f"TESTSLOT {slot}")

    def set_system_select(self, system_num: int) -> None:
        """Select system number for multi-system config. e.g. SYSSEL 1"""
        self.write(f"SYSSEL {system_num}")

    def query_system_select(self, system_num: Optional[int] = None) -> str:
        """Query system selection."""
        if system_num is not None:
            return self.query(f"SYSSEL? {system_num}")
        return self.query("SYSSEL?")

    def query_num_mt8000a(self) -> str:
        """Query number of MT8000A units (2-box config)."""
        return self.query("NUMOFMT8000A?")

    # =========================================================================
    # Call Processing / Connection Control
    # =========================================================================
    def set_call_processing(self, on_off: bool) -> None:
        """Enable/disable call processing."""
        self.write(f"CALLPROC {'ON' if on_off else 'OFF'}")

    def call_sa(self) -> None:
        """Initiate SA call connection."""
        self.write("CALLSA")

    def call_disconnect(self) -> None:
        """Disconnect the call (SA)."""
        self.write("CALLSO")

    def query_call_status(self) -> str:
        """Query current call processing status."""
        return self.query("CALLSTAT?")

    def query_connection_status(self) -> str:
        """Query connection status."""
        return self.query("CONNECT?")

    def wait_for_call_connected(self, timeout_s: float = 60, poll_interval_s: float = 1) -> bool:
        """
        Poll CALLSTAT? until connected or timeout.
        Returns True if connected, False on timeout.
        """
        start = time.time()
        while time.time() - start < timeout_s:
            status = self.query_call_status()
            if "CONNECTED" in status.upper() or status == "6":
                return True
            time.sleep(poll_interval_s)
        logger.warning("Call connection timed out after %ss", timeout_s)
        return False

    # =========================================================================
    # SIM / Authentication
    # =========================================================================
    def set_sim_model(self, model: str) -> None:
        """Set SIM card model number. e.g. SIMMODELNUM P0135"""
        self.write(f"SIMMODELNUM {model}")

    def set_integrity(self, algorithm: str) -> None:
        """Set integrity protection algorithm. e.g. INTEGRITY SNOW3G"""
        self.write(f"INTEGRITY {algorithm}")

    # =========================================================================
    # Frame Structure / Duplex Mode
    # =========================================================================
    def set_frame_type(self, mode: str, cc: Optional[str] = None) -> None:
        """
        Set duplex mode. mode: 'TDD' | 'FDD'
        cc: carrier component, e.g. 'SCC1'. If None, applies to PCC.
        """
        if cc:
            self.write(f"FRAMETYPE {cc},{mode}")
        else:
            self.write(f"FRAMETYPE {mode}")

    def set_channel_setting_mode(self, mode: str = "LOWESTGSCN") -> None:
        """Set channel setting mode. Default: LOWESTGSCN"""
        self.write(f"CHANSETMODE {mode}")

    def set_common_setting_mode(self, mode: str) -> None:
        """Set common setting mode."""
        self.write(f"COMMONSETMODE {mode}")

    # =========================================================================
    # Band / Frequency Configuration
    # =========================================================================
    def set_band(self, cc: str, band: int) -> None:
        """Set operation band. e.g. BAND PCC,78"""
        self.write(f"BAND {cc},{band}")

    def set_dl_scs(self, cc: str, scs: str) -> None:
        """Set DL subcarrier spacing. e.g. DLSCS PCC,30KHZ"""
        self.write(f"DLSCS {cc},{scs}")

    def set_dl_bandwidth(self, cc: str, bw: str) -> None:
        """Set DL channel bandwidth. e.g. DLBANDWIDTH PCC,100MHZ"""
        self.write(f"DLBANDWIDTH {cc},{bw}")

    def set_dl_channel(self, cc: str, channel: int) -> None:
        """Set DL center channel (NR-ARFCN). e.g. DLCHAN PCC,623334"""
        self.write(f"DLCHAN {cc},{channel}")

    def set_offset_carrier(self, cc: str, offset: int) -> None:
        """Set DL OffsetToCarrier. e.g. OFFSETCARRIER PCC,0"""
        self.write(f"OFFSETCARRIER {cc},{offset}")

    def set_ssb_channel(self, cc: str, channel: int) -> None:
        """Set Absolute Frequency SSB. e.g. SSBCHAN PCC,620352"""
        self.write(f"SSBCHAN {cc},{channel}")

    def set_ssb_scs(self, cc: str, scs: str) -> None:
        """Set SS Block Subcarrier Spacing. e.g. SSBSCS PCC,30KHZ"""
        self.write(f"SSBSCS {cc},{scs}")

    def set_ssb_type(self, cc: str, stype: str) -> None:
        """Set SS Block Transmission Type. e.g. SSBTYPE PCC,BITMAP"""
        self.write(f"SSBTYPE {cc},{stype}")

    def set_ssb_position(self, cc: str, bitmap: str) -> None:
        """Set SS Block Position Bitmap. e.g. SSBPOS PCC,40"""
        self.write(f"SSBPOS {cc},{bitmap}")

    def set_ssb_period(self, cc: str, period: int) -> None:
        """Set SSB Burst Periodicity (ms). e.g. SSBPERIOD PCC,10"""
        self.write(f"SSBPERIOD {cc},{period}")

    def set_ssb_power(self, power: float) -> None:
        """Set SS/PBCH Block Power. e.g. SSPBCHBLOCKPOWER -6.02"""
        self.write(f"SSPBCHBLOCKPOWER {power}")

    def set_ul_channel(self, cc: str, channel: int) -> None:
        """Set UL center channel (NR-ARFCN). e.g. ULCHAN PCC,516582"""
        self.write(f"ULCHAN {cc},{channel}")

    def set_ul_bandwidth(self, cc: str, bw: str) -> None:
        """Set UL channel bandwidth. e.g. ULBANDWIDTH PCC,100MHZ"""
        self.write(f"ULBANDWIDTH {cc},{bw}")

    def set_ul_offset_carrier(self, cc: str, offset: int) -> None:
        """Set UL OffsetToCarrier. e.g. ULOFFSETCARRIER PCC,0"""
        self.write(f"ULOFFSETCARRIER {cc},{offset}")

    def set_cell_id(self, cc: str, cell_id: int) -> None:
        """Set Physical Cell ID. e.g. CELLID PCC,0"""
        self.write(f"CELLID {cc},{cell_id}")

    # =========================================================================
    # TDD Configuration
    # =========================================================================
    def set_tdd_ul_dl_config(self, cc: str, config: str) -> None:
        """Set TDD UL/DL Configuration. e.g. TDDULDLCONF PCC,CONFIG1"""
        self.write(f"TDDULDLCONF {cc},{config}")

    def set_tdd_ul_dl_config2(self, cc: str, config: str) -> None:
        """Set TDD UL/DL Configuration 2."""
        self.write(f"TDDULDLCONF2 {cc},{config}")

    def set_tdd_ssf_config(self, cc: str, config: str) -> None:
        """Set TDD special subframe configuration."""
        self.write(f"TDDSSFCONF {cc},{config}")

    def set_dl_ul_period(self, cc: str, period: str) -> None:
        """Set DL/UL Periodicity. e.g. DLULPERIOD PCC,5MS"""
        self.write(f"DLULPERIOD {cc},{period}")

    def set_dl_duration(self, cc: str, duration: int) -> None:
        """Set DL Duration (slots). e.g. DLDURATION PCC,8"""
        self.write(f"DLDURATION {cc},{duration}")

    def set_ul_duration(self, cc: str, duration: int) -> None:
        """Set UL Duration (slots). e.g. ULDURATION PCC,2"""
        self.write(f"ULDURATION {cc},{duration}")

    def set_dl_symbols(self, cc: str, symbols: int) -> None:
        """Set Common DL symbols. e.g. DLSYMBOLS PCC,6"""
        self.write(f"DLSYMBOLS {cc},{symbols}")

    def set_ul_symbols(self, cc: str, symbols: int) -> None:
        """Set Common UL symbols. e.g. ULSYMBOLS PCC,4"""
        self.write(f"ULSYMBOLS {cc},{symbols}")

    # =========================================================================
    # Carrier Aggregation (CA) Configuration
    # =========================================================================
    def set_dl_scc(self, num: int) -> None:
        """Set number of DL Secondary Component Carriers. e.g. DLSCC 1"""
        self.write(f"DLSCC {num}")

    def set_ul_scc(self, num: int) -> None:
        """Set number of UL Secondary Component Carriers. e.g. ULSCC 1"""
        self.write(f"ULSCC {num}")

    def set_ul_ca(self, num: int) -> None:
        """Set number of UL CA carriers. e.g. ULCA 2"""
        self.write(f"ULCA {num}")

    def set_dl_2ca(self, mode: str) -> None:
        """Configure DL 2CA mode."""
        self.write(f"DL2CA {mode}")

    def set_ul_agg_level(self, level: int) -> None:
        """Set UL aggregation level."""
        self.write(f"ULAGGLVL {level}")

    def set_dl_agg_level(self, level: int) -> None:
        """Set DL aggregation level."""
        self.write(f"DLAGGLVL {level}")

    # =========================================================================
    # Supplementary Uplink (SUL) Configuration
    # =========================================================================
    def enable_sul(self) -> None:
        """Enable Supplementary Uplink (SUL) carrier."""
        self.write("ADDSULON")

    def set_sul_band(self, cc: str, band: int) -> None:
        """Set SUL operation band. e.g. SULBAND PCC,80"""
        self.write(f"SULBAND {cc},{band}")

    def set_sul_bandwidth(self, cc: str, bw: str) -> None:
        """Set SUL channel bandwidth. e.g. SULBANDWIDTH PCC,5MHZ"""
        self.write(f"SULBANDWIDTH {cc},{bw}")

    def set_sul_channel(self, cc: str, channel: int) -> None:
        """Set SUL center channel. e.g. SULCHAN PCC,349500"""
        self.write(f"SULCHAN {cc},{channel}")

    def set_sul_offset_carrier(self, cc: str, offset: int) -> None:
        """Set SUL OffsetToCarrier. e.g. SULOFFSETCARRIER PCC,2198"""
        self.write(f"SULOFFSETCARRIER {cc},{offset}")

    # =========================================================================
    # Handover Configuration
    # =========================================================================
    def set_ho_type(self, ho_type: str) -> None:
        """Set handover type. e.g. HOTYPE NORMAL"""
        self.write(f"HOTYPE {ho_type}")

    def set_ho_frame_type(self, mode: str) -> None:
        """Set handover duplex mode. e.g. HO_FRAMETYPE TDD"""
        self.write(f"HO_FRAMETYPE {mode}")

    def set_ho_channel_setting_mode(self, mode: str = "LOWESTGSCN") -> None:
        """Set handover channel setting mode."""
        self.write(f"HO_CHANSETMODE {mode}")

    def set_ho_band(self, cc: str, band: int) -> None:
        """Set handover operation band. e.g. HO_BAND PCC,78"""
        self.write(f"HO_BAND {cc},{band}")

    def set_ho_dl_bandwidth(self, cc: str, bw: str) -> None:
        """Set handover DL bandwidth. e.g. HO_DLBANDWIDTH PCC,100MHZ"""
        self.write(f"HO_DLBANDWIDTH {cc},{bw}")

    def set_ho_dl_channel(self, cc: str, channel: int) -> None:
        """Set handover DL center channel. e.g. HO_DLCHAN PCC,623334"""
        self.write(f"HO_DLCHAN {cc},{channel}")

    def set_ho_offset_carrier(self, cc: str, offset: int) -> None:
        """Set handover OffsetToCarrier. e.g. HO_OFFSETCARRIER PCC,0"""
        self.write(f"HO_OFFSETCARRIER {cc},{offset}")

    def set_ho_ssb_channel(self, cc: str, channel: int) -> None:
        """Set handover SSB channel. e.g. HO_SSBCHAN PCC,620352"""
        self.write(f"HO_SSBCHAN {cc},{channel}")

    def execute_channel_handover(self) -> None:
        """Execute channel handover."""
        self.write("EXEC_CHHO")
        self.opc()

    # =========================================================================
    # Routing / Port Configuration
    # =========================================================================
    def set_routing_mode(self, mode: str) -> None:
        """Set routing mode. mode: 'USER' | 'SISO' | etc. e.g. TXIQROUTING USER"""
        self.write(f"TXIQROUTING {mode}")

    def set_meas_hw_slot(self, cc: str, slot: str) -> None:
        """Set measurement HW slot. e.g. MEASHWSLOT PCC,SLOT1"""
        self.write(f"MEASHWSLOT {cc},{slot}")

    def set_meas_hw_port(self, cc: str, port: str) -> None:
        """Set measurement HW port (TRx). e.g. MEASHWPORT PCC,TRX1"""
        self.write(f"MEASHWPORT {cc},{port}")

    def set_cell_trx(self, cc: str, trx: str) -> None:
        """Set Cell TRx port. e.g. CELLTRX PCC,TRX1"""
        self.write(f"CELLTRX {cc},{trx}")

    def set_rf_out(self, setting: str) -> None:
        """Set RF output configuration."""
        self.write(f"RFOUT {setting}")

    def set_channel_coding(self, mode: str) -> None:
        """Set channel coding. e.g. CHCODING RMC"""
        self.write(f"CHCODING {mode}")

    def set_box2_slot(self, slot: str, trx: str, value: Optional[float] = None) -> None:
        """Set 2-box configuration slot. e.g. BOX2_SLOT1 TRX1,12.7"""
        if value is not None:
            self.write(f"BOX2_SLOT1 {trx},{value}")
        else:
            self.write(f"BOX2_SLOT1 {trx}")

    # =========================================================================
    # AUX Connector Configuration (for external SG sync)
    # =========================================================================
    def set_aux_frame_timing1(self, slot: str, mode: str) -> None:
        """Set AUX Frame Timing 1. e.g. AUX_FRAME_TIM1 SLOT1,FRAME"""
        self.write(f"AUX_FRAME_TIM1 {slot},{mode}")

    def set_aux_frame_timing2(self, slot: str, mode: str) -> None:
        """Set AUX Frame Timing 2. e.g. AUX_FRAME_TIM2 SLOT1,FRAME"""
        self.write(f"AUX_FRAME_TIM2 {slot},{mode}")

    # =========================================================================
    # PDCCH / DCI Configuration
    # =========================================================================
    def set_dci_format(self, fmt: str) -> None:
        """Set DCI Format. e.g. DCIFORMAT FORMAT0_1_AND_1_1"""
        self.write(f"DCIFORMAT {fmt}")

    def set_scheduling(self, mode: str) -> None:
        """Set scheduling type. mode: 'STATIC' | 'DYNAMIC'. e.g. SCHEDULING STATIC"""
        self.write(f"SCHEDULING {mode}")

    def set_num_rb_coreset(self, cc: str, rb: str) -> None:
        """Set CORESET Number of RBs. e.g. NUMRBCORESET PCC,FULLBW"""
        self.write(f"NUMRBCORESET {cc},{rb}")

    def set_num_sym_coreset(self, cc: str, sym: int) -> None:
        """Set CORESET Number of Symbols."""
        self.write(f"NUMSYMCORESET {cc},{sym}")

    def set_cce_index_type(self, cc: str, mode: str) -> None:
        """Set CCE Index Allocation. e.g. CCEINDEX_TYPE PCC,AUTO"""
        self.write(f"CCEINDEX_TYPE {cc},{mode}")

    def set_cce_index(self, cc: str, index: int) -> None:
        """Set CCE Index value."""
        self.write(f"CCEINDEX {cc},{index}")

    def set_ss_candidate(self, cc: str, value: int) -> None:
        """Set number of PDCCH candidates."""
        self.write(f"SSCANDIDATE {cc},{value}")

    def set_ss_candidate_al4(self, cc: str, value: int) -> None:
        """Set number of PDCCH candidates for AL4."""
        self.write(f"SSCANDIDATE_AL4 {cc},{value}")

    def set_ss_candidate_al16(self, cc: str, value: int) -> None:
        """Set number of PDCCH candidates for AL16."""
        self.write(f"SSCANDIDATE_AL16 {cc},{value}")

    def set_start_prb_cch_fmt1(self, cc: str, prb: int) -> None:
        """Set starting PRB for CCH Format 1."""
        self.write(f"STARTPRB_CCHFMT1 {cc},{prb}")

    def set_start_prb_cch_fmt3(self, cc: str, prb: int) -> None:
        """Set starting PRB for CCH Format 3."""
        self.write(f"STARTPRB_CCHFMT3 {cc},{prb}")

    def set_format_type(self, cc: str, fmt: str) -> None:
        """Set PUCCH format type."""
        self.write(f"FORMATTYPE {cc},{fmt}")

    def set_format_type_cch(self, cc: str, fmt: str) -> None:
        """Set PUCCH CCH format type."""
        self.write(f"FORMATTYPE_CCH {cc},{fmt}")

    def set_group_hopping_cch(self, mode: str) -> None:
        """Set PUCCH Group Hopping. mode: 'ENABLE' | 'NEITHER'. e.g. GROUPHOPPING_CCH ENABLE"""
        self.write(f"GROUPHOPPING_CCH {mode}")

    def set_dl_harq_ack_codebook(self, cc: str, mode: str) -> None:
        """Set HARQ-ACK Codebook. mode: 'DYNAMIC' | 'SEMISTATIC'"""
        self.write(f"DLHARQACKCODEBOOK {cc},{mode}")

    def set_dl_num_harq_process(self, cc: str, num: int) -> None:
        """Set number of DL HARQ processes."""
        self.write(f"DLNUMHARQPROCESS {cc},{num}")

    def set_crnti(self, cc: str, value: int) -> None:
        """Set C-RNTI value."""
        self.write(f"CRNTI {cc},{value}")

    def set_report_direct_current(self, mode: str) -> None:
        """Set Report Direct Current. e.g. REPORTDIRECTCURRENT ON"""
        self.write(f"REPORTDIRECTCURRENT {mode}")

    def set_phy_chan_set_mode(self, mode: str) -> None:
        """Set Physical Channel Setting Mode."""
        self.write(f"PHYCHANSETMODE {mode}")

    # =========================================================================
    # RMC / Modulation Configuration
    # =========================================================================
    def set_ch_config(self, config: str) -> None:
        """Set RMC Configuration. config: 'PUSCH' | 'PUCCH' | etc. e.g. CHCONFIG PUSCH"""
        self.write(f"CHCONFIG {config}")

    def set_tx_config(self, cc: str, mode: str) -> None:
        """Set txConfig. e.g. TXCONFIG PCC,CODEBOOK"""
        self.write(f"TXCONFIG {cc},{mode}")

    # --- DL RMC ---
    def set_dl_rmc_rb(self, cc: str, rb: int) -> None:
        """Set DL RMC Number of RB. e.g. DLRMC_RB PCC,0"""
        self.write(f"DLRMC_RB {cc},{rb}")

    def set_dl_rb_start(self, cc: str, start: int) -> None:
        """Set DL RMC Starting RB. e.g. DLRB_START PCC,0"""
        self.write(f"DLRB_START {cc},{start}")

    def set_dl_mcs_table(self, cc: str, table: str) -> None:
        """Set DL MCS Index Table. e.g. DLMCS_TABLE PCC,64QAM"""
        self.write(f"DLMCS_TABLE {cc},{table}")

    def set_dl_mcs_index(self, cc: str, index: int) -> None:
        """Set DL MCS Index. e.g. DLIMCS PCC,4"""
        self.write(f"DLIMCS {cc},{index}")

    def set_dl_rmc(self, cc: str, rmc: str) -> None:
        """Set DL RMC configuration name."""
        self.write(f"DLRMC {cc},{rmc}")

    # --- UL RMC ---
    def set_ul_waveform(self, cc: str, waveform: str) -> None:
        """Set UL waveform. waveform: 'DFTOFDM' | 'CPOFDM'. e.g. ULWAVEFORM PCC,DFTOFDM"""
        self.write(f"ULWAVEFORM {cc},{waveform}")

    def set_ul_rmc_rb(self, cc: str, rb: int) -> None:
        """Set UL RMC Number of RB. e.g. ULRMC_RB PCC,162"""
        self.write(f"ULRMC_RB {cc},{rb}")

    def set_ul_rb_start(self, cc: str, start: int) -> None:
        """Set UL RMC Starting RB. e.g. ULRB_START PCC,0"""
        self.write(f"ULRB_START {cc},{start}")

    def set_ul_mcs_table(self, cc: str, table: str) -> None:
        """Set UL MCS Index Table. e.g. ULMCS_TABLE PCC,64QAM"""
        self.write(f"ULMCS_TABLE {cc},{table}")

    def set_ul_mcs_index(self, cc: str, index: int) -> None:
        """Set UL MCS Index. e.g. ULIMCS PCC,10"""
        self.write(f"ULIMCS {cc},{index}")

    def set_ul_rmc_mod(self, cc: str, mod: str) -> None:
        """Set UL RMC Modulation. e.g. ULRMC_MOD PCC,QPSK"""
        self.write(f"ULRMC_MOD {cc},{mod}")

    def set_ul_rmc(self, cc: str, rmc: str) -> None:
        """Set UL RMC configuration name."""
        self.write(f"ULRMC {cc},{rmc}")

    # =========================================================================
    # MIMO / Antenna Configuration
    # =========================================================================
    def set_antenna_config(self, config: str) -> None:
        """Set antenna configuration."""
        self.write(f"ANTCONFIG {config}")

    def set_ul_antenna_config(self, cc: str, config: str) -> None:
        """Set UL antenna configuration. e.g. ULANTCONFIG PCC,1T2R"""
        self.write(f"ULANTCONFIG {cc},{config}")

    def set_ul_antenna_num(self, cc: str, num: int) -> None:
        """Set UL antenna number."""
        self.write(f"ULANTNUM {cc},{num}")

    def set_ul_layer_num(self, cc: str, num: int) -> None:
        """Set UL number of layers."""
        self.write(f"ULLAYERNUM {cc},{num}")

    def set_tpmi(self, cc: str, mode: str) -> None:
        """Set TPMI mode."""
        self.write(f"TPMI {cc},{mode}")

    def set_tpmi_value(self, cc: str, value: int) -> None:
        """Set TPMI value."""
        self.write(f"TPMIVAL {cc},{value}")

    def set_ul_fptx(self, mode: str) -> None:
        """Set UL Full Power Tx mode. e.g. ULFPTX ON"""
        self.write(f"ULFPTX {mode}")

    def set_mimo_ref_point(self, point: str) -> None:
        """Set MIMO reference point."""
        self.write(f"MIMO_REFPOINT {point}")

    def set_rx_div_ant_num(self, num: int) -> None:
        """Set Rx Diversity antenna number."""
        self.write(f"RXDIVANTNUM {num}")

    def set_rx_div_ca_mode(self, mode: str) -> None:
        """Set Rx Diversity CA mode."""
        self.write(f"RXDIVCAMODE {mode}")

    def set_tx_diversity_mod_meas_type(self, mtype: str) -> None:
        """Set Tx diversity modulation measurement type."""
        self.write(f"TXDIV_MOD_MEAS_TYPE {mtype}")

    # =========================================================================
    # Power Control / Level Settings
    # =========================================================================
    def set_input_level(self, cc_or_value: Union[str, float], value: Optional[float] = None) -> None:
        """
        Set input level (dBm).
        Usage: set_input_level("PCC", 23) or set_input_level(23)
        """
        if value is not None:
            self.write(f"ILVL {cc_or_value},{value}")
        else:
            self.write(f"ILVL {cc_or_value}")

    def set_output_level(self, cc: str, level: float) -> None:
        """Set output level (dBm). e.g. OLVL PCC,-88.1"""
        self.write(f"OLVL {cc},{level}")

    def set_output_level_epre(self, cc: str, level: float) -> None:
        """Set output level EPRE (dBm/SCS). e.g. OLVL_EPRE PCC,-85.0"""
        self.write(f"OLVL_EPRE {cc},{level}")

    def set_tpc_pattern(self, pattern: str) -> None:
        """
        Set TPC pattern.
        pattern: 'AUTO' | 'ALLO' (All 0) | 'ALL3' (All +3) | 'ALL_3' (All -3) etc.
        """
        self.write(f"TPCPAT {pattern}")

    def set_tpc_target_power(self, power: float) -> None:
        """Set TPC Target Power."""
        self.write(f"TPCTARGETPOW {power}")

    def set_max_ul_power(self, power: float) -> None:
        """Set maximum UL power (LTE). e.g. MAXULPWR 23"""
        self.write(f"MAXULPWR {power}")

    def set_max_ul_level(self, mode: str) -> None:
        """Set max UL level mode. e.g. MAXULLVL ON"""
        self.write(f"MAXULLVL {mode}")

    def set_max_ue_fr1_ul_power(self, power: float) -> None:
        """Set p-MaxUE-FR1 value. e.g. MAXUEFR1ULPWR 23"""
        self.write(f"MAXUEFR1ULPWR {power}")

    def set_max_ue_fr1_ul_level(self, mode: str) -> None:
        """Set p-MaxUE-FR1 On/Off. e.g. MAXUEFR1ULLVL ON"""
        self.write(f"MAXUEFR1ULLVL {mode}")

    def set_max_power(self, power: float) -> None:
        """Set max power."""
        self.write(f"MAXPWR {power}")

    def set_nr_fr1_ul_level(self, level: float) -> None:
        """Set NR FR1 UL level."""
        self.write(f"NRFR1ULLVL {level}")

    def set_nr_fr1_ul_power(self, power: float) -> None:
        """Set NR FR1 UL power."""
        self.write(f"NRFR1ULPWR {power}")

    def set_p_nominal(self, value: float) -> None:
        """Set P0 Nominal PUSCH."""
        self.write(f"PONOMINAL {value}")

    def set_ue_power_class(self, power_class: int) -> None:
        """Set UE Power Class. e.g. UEPOWERCLASS 3"""
        self.write(f"UEPOWERCLASS {power_class}")

    def set_xscale(self, mode: str) -> None:
        """Set XSCALE mode. e.g. XSCALE OFF"""
        self.write(f"XSCALE {mode}")

    def set_lte_config_for_dps(self, mode: str) -> None:
        """Set LTE config for DynamicPowerSharing. e.g. LTECONFIGFORDPS ON"""
        self.write(f"LTECONFIGFORDPS {mode}")

    def set_tx_switching(self, mode: str) -> None:
        """Set Tx switching mode."""
        self.write(f"TXSWITCHING {mode}")

    # =========================================================================
    # External Loss Settings
    # =========================================================================
    def set_dl_ext_loss(self, value: float) -> None:
        """Set DL external loss (JND). e.g. DLEXTLOSSJND 0.5"""
        self.write(f"DLEXTLOSSJND {value}")

    def set_ul_ext_loss(self, value: float) -> None:
        """Set UL external loss (JND). e.g. ULEXTLOSSJND 0.5"""
        self.write(f"ULEXTLOSSJND {value}")

    def set_aux_ext_loss(self, value: float) -> None:
        """Set AUX external loss (JND)."""
        self.write(f"AUEXTLOSSJND {value}")

    def set_loss_table_value(self, *args) -> None:
        """Set loss table value. e.g. LOSSTBLVAL freq,loss"""
        self.write(f"LOSSTBLVAL {','.join(str(a) for a in args)}")

    def set_ext_loss_table_6g(self, value: float) -> None:
        """Set external loss table ID for 6GHz band."""
        self.write(f"EXTLOSSTBLID6GJND {value}")

    def set_ext_loss_table_12g(self, value: float) -> None:
        """Set external loss table ID for 12GHz band."""
        self.write(f"EXTLOSSTBLID12GJND {value}")

    def set_ext_loss_table_28g(self, value: float) -> None:
        """Set external loss table ID for 28GHz band."""
        self.write(f"EXTLOSSTBLID28GJND {value}")

    def set_ext_loss_w(self, value: float) -> None:
        """Set external loss W (JND)."""
        self.write(f"EXTLOSSWJND {value}")

    def set_dl_ext_loss_rf_conv(self, value: float) -> None:
        """Set DL external loss with RF converter P2."""
        self.write(f"DLEXTLOSSRFCONVP2JND {value}")

    def set_ul_ext_loss_rf_conv(self, value: float) -> None:
        """Set UL external loss with RF converter P1."""
        self.write(f"ULEXTLOSSRFCONVP1JND {value}")

    # =========================================================================
    # EN-DC Specific
    # =========================================================================
    def set_endc_meas_mode(self, mode: str) -> None:
        """Set EN-DC measurement mode. mode: 'NR' | 'LTE' | etc."""
        self.write(f"ENDCMEASMODE {mode}")

    def set_sync_offset(self, offset: int) -> None:
        """Set LTE-NR Frame Timing Offset (ms). e.g. SYNCOFFSET 3"""
        self.write(f"SYNCOFFSET {offset}")

    def enter_sync(self, mode: str = "PRIMARY") -> None:
        """Execute frame timing synchronization. e.g. ENTERSYNC PRIMARY"""
        self.write(f"ENTERSYNC {mode}")
        self.opc()

    # =========================================================================
    # NR-DC Specific
    # =========================================================================
    def set_nrdc_target_fr(self, fr: str) -> None:
        """Select target FR for NR-DC commands. fr: 'FR1' | 'FR2'"""
        self.write(f"NRDC_SEL_TARGETFR {fr}")

    def set_fr1_fr2_meas_mode(self, mode: str) -> None:
        """Select FR1/FR2 for measurement. mode: 'FR1' | 'FR2'"""
        self.write(f"FR1FR2MEASMODE {mode}")

    def set_fr1_fr2_rx_meas_mode(self, mode: str) -> None:
        """Select FR1/FR2 for Rx measurement."""
        self.write(f"FR1FR2RXMEASMODE {mode}")

    # =========================================================================
    # CSI-RS Configuration
    # =========================================================================
    def set_csirs(self, mode: str) -> None:
        """Set CSI-RS mode. e.g. CSIRS ON"""
        self.write(f"CSIRS {mode}")

    def set_csirs_resource(self, cc: str, value: int) -> None:
        """Set CSI-RS resource number."""
        self.write(f"CSIRSRESOURCE {cc},{value}")

    def set_csirs_periodicity(self, cc: str, period: int) -> None:
        """Set CSI-RS periodicity."""
        self.write(f"CSIRSPERIODICITY {cc},{period}")

    def set_csirs_offset(self, cc: str, offset: int) -> None:
        """Set CSI-RS offset."""
        self.write(f"CSIRSOFFSET {cc},{offset}")

    def set_csirs_nrb(self, cc: str, nrb: int) -> None:
        """Set CSI-RS Number of RBs."""
        self.write(f"CSIRSNRB {cc},{nrb}")

    def set_csirs_start_rb(self, cc: str, rb: int) -> None:
        """Set CSI-RS Starting RB."""
        self.write(f"CSIRSSTARTRB {cc},{rb}")

    def set_csirs_start_symbol(self, cc: str, symbol: int) -> None:
        """Set CSI-RS Starting Symbol."""
        self.write(f"CSIRSSTARTSYMBOL {cc},{symbol}")

    def set_avoid_csirs_for_ref_sens(self, cc: str, mode: str) -> None:
        """Disable PDSCH during CSI-RS slots for ref. sensitivity. e.g. AVOIDCSIRSFORREFSENS PCC,ON"""
        self.write(f"AVOIDCSIRSFORREFSENS {cc},{mode}")

    # =========================================================================
    # SRS Configuration
    # =========================================================================
    def set_srs_resource(self, cc: str, value: int) -> None:
        """Set SRS resource number."""
        self.write(f"SRSRESOURCE {cc},{value}")

    def set_srs_periodicity(self, cc: str, period: int) -> None:
        """Set SRS periodicity."""
        self.write(f"SRSPERIODICITY {cc},{period}")

    def set_srs_offset(self, offset: int) -> None:
        """Set SRS Offset. e.g. SRSOFFSET 7"""
        self.write(f"SRSOFFSET {offset}")

    def set_srs_alpha(self, alpha: str) -> None:
        """Set SRS alpha value. e.g. SRS_ALPHA ALPHA0"""
        self.write(f"SRS_ALPHA {alpha}")

    def set_srs_p0(self, p0: float) -> None:
        """Set SRS p0 value. e.g. SRS_P0 0"""
        self.write(f"SRS_P0 {p0}")

    def set_srs_num_ports(self, ports: int) -> None:
        """Set SRS number of ports."""
        self.write(f"SRSNUMPORTS {ports}")

    def set_srs_start_symbol(self, symbol: int) -> None:
        """Set SRS starting symbol."""
        self.write(f"SRSSTARTSYMBOL {symbol}")

    def set_srs_symbol_length(self, length: int) -> None:
        """Set SRS symbol length."""
        self.write(f"SRSSYMBOLLENGTH {length}")

    # =========================================================================
    # PRACH Configuration
    # =========================================================================
    def set_prach_config_index(self, index: int) -> None:
        """Set PRACH Configuration Index. e.g. PRACHCONFIGINDEX 81"""
        self.write(f"PRACHCONFIGINDEX {index}")

    def set_preamble_target(self, power: float) -> None:
        """Set Preamble Received Target Power. e.g. PREAMBLETGT -92"""
        self.write(f"PREAMBLETGT {power}")

    def set_preamble_max(self, value: str) -> None:
        """Set PreambleTransMax. e.g. PREAMBLEMAX N7"""
        self.write(f"PREAMBLEMAX {value}")

    def set_power_ramping_step(self, step: str) -> None:
        """Set Power Ramping Step. e.g. PWRRMPSTEP dB4"""
        self.write(f"PWRRMPSTEP {step}")

    # =========================================================================
    # UL Allocation List (for multi-slot scheduling)
    # =========================================================================
    def set_ul_alloc_list_size(self, size: int) -> None:
        """Set UL allocation list size."""
        self.write(f"ULALLOCLIST_SIZE {size}")

    def set_ul_alloc_list(self, *args) -> None:
        """Set UL allocation list entry."""
        self.write(f"ULALLOCLIST {','.join(str(a) for a in args)}")

    def set_ul_alloc_list_k2(self, k2: int) -> None:
        """Set UL allocation list K2 value."""
        self.write(f"ULALLOCLIST_K2 {k2}")

    # =========================================================================
    # Spectrum / Additional Spectrum Emission
    # =========================================================================
    def set_additional_spectrum_emission(self, mode: str) -> None:
        """Enable/disable Additional Spectrum Emission. e.g. ADDSPEM ON"""
        self.write(f"ADDSPEM {mode}")

    def set_additional_spectrum_emission_value(self, cc_or_value, value: Optional[int] = None) -> None:
        """Set ASEM value. e.g. ADDSPEMVALUE 1 or ADDSPEMVALUE PCC,0"""
        if value is not None:
            self.write(f"ADDSPEMVALUE {cc_or_value},{value}")
        else:
            self.write(f"ADDSPEMVALUE {cc_or_value}")

    def set_additional_spectrum_emission_sul(self, value: int) -> None:
        """Set ASEM value for SUL."""
        self.write(f"ADDSPEMVALUE_SUL {value}")

    def set_addspem_sul(self, mode: str) -> None:
        """Enable/disable Additional Spectrum Emission for SUL."""
        self.write(f"ADDSPEM_SUL {mode}")

    def set_sib2_ns(self, value: int) -> None:
        """Set SIB2 NS value."""
        self.write(f"SIB2_NS {value}")

    # =========================================================================
    # RedCap (Reduced Capability) Configuration
    # =========================================================================
    def set_redcap_operation(self, mode: str) -> None:
        """Set RedCap operation mode. e.g. REDCAPOP ON"""
        self.write(f"REDCAPOP {mode}")

    # =========================================================================
    # NR NTN (Non-Terrestrial Network) Configuration
    # =========================================================================
    def set_nrntn(self, mode: str) -> None:
        """Enable/disable NR NTN mode."""
        self.write(f"NRNTN {mode}")

    def set_ntn_preset(self, preset: str) -> None:
        """Set NTN preset configuration."""
        self.write(f"NTN_PRESET {preset}")

    def query_ntn_ue_location_latitude(self) -> str:
        """Query NTN UE location latitude."""
        return self.query("NTN_UELOC_LATI?")

    def query_ntn_ue_location_longitude(self) -> str:
        """Query NTN UE location longitude."""
        return self.query("NTN_UELOC_LONGI?")

    def query_ntn_ue_location_altitude(self) -> str:
        """Query NTN UE location altitude."""
        return self.query("NTN_UELOC_ALTI?")

    # =========================================================================
    # Measurement Control
    # =========================================================================
    def all_meas_items_off(self) -> None:
        """Turn off all measurement items."""
        self.write("ALLMEASITEMS_OFF")
        self.opc()

    def set_meas_item(self, item: str) -> None:
        """
        Set measurement item mode.
        item: 'NORMAL' | 'PCT' | 'EVMTP' | etc.
        """
        self.write(f"MEASITEM {item}")

    def set_meas_metric(self, metric: str) -> None:
        """Set measurement metric."""
        self.write(f"MEASMETRIC {metric}")

    # --- Individual measurement ON/OFF ---
    def set_power_meas(self, on: bool, avg: Optional[int] = None) -> None:
        """Enable/disable power measurement and optionally set averaging count."""
        self.write(f"PWR_MEAS {'ON' if on else 'OFF'}")
        if avg is not None:
            self.write(f"PWR_AVG {avg}")

    def set_mod_meas(self, on: bool, avg: Optional[int] = None) -> None:
        """Enable/disable modulation analysis and optionally set averaging count."""
        self.write(f"MOD_MEAS {'ON' if on else 'OFF'}")
        if avg is not None:
            self.write(f"MOD_AVG {avg}")

    def set_sem_meas(self, on: bool, avg: Optional[int] = None) -> None:
        """Enable/disable Spectrum Emission Mask measurement."""
        self.write(f"SEM_MEAS {'ON' if on else 'OFF'}")
        if avg is not None:
            self.write(f"SEM_AVG {avg}")

    def set_obw_meas(self, on: bool) -> None:
        """Enable/disable Occupied Bandwidth measurement."""
        self.write(f"OBWMEAS {'ON' if on else 'OFF'}")

    def set_obw_meas_bw(self, bw: str) -> None:
        """Set OBW measurement bandwidth."""
        self.write(f"OBWMEASBW {bw}")

    def set_obw_meas_proc(self, proc: str) -> None:
        """Set OBW measurement processing mode."""
        self.write(f"OBWMEASPROC {proc}")

    def set_aclr_meas(self, on: bool) -> None:
        """Set ACLR measurement avg/count."""
        self.write(f"ACLR {'ON' if on else 'OFF'}")

    def set_aclr_avg(self, avg: int) -> None:
        """Set ACLR averaging count."""
        self.write(f"ACLRAVG {avg}")

    def set_throughput_meas(self, on: bool) -> None:
        """Enable/disable Throughput measurement."""
        self.write(f"TPUT_MEAS {'ON' if on else 'OFF'}")

    def set_throughput_sample(self, samples: int) -> None:
        """Set throughput measurement sample count. e.g. TPUT_SAMPLE 2466"""
        self.write(f"TPUT_SAMPLE {samples}")

    def set_power_temp_meas(self, on: bool, avg: Optional[int] = None) -> None:
        """Enable/disable Power Template measurement."""
        self.write(f"PWRTEMP_MEAS {'ON' if on else 'OFF'}")
        if avg is not None:
            self.write(f"PWRTEMP_AVG {avg}")

    def set_ibem_meas(self, mode: str) -> None:
        """Set IBEM (In-Band Emission) measurement."""
        self.write(f"IBEM {mode}")

    def set_ibem_clfr(self, value: str) -> None:
        """Set IBEM CLFR value."""
        self.write(f"IBEM_CLFR {value}")

    def set_early_decision(self, mode: str) -> None:
        """Enable/disable early decision for throughput. e.g. EARLY_DECISION ON"""
        self.write(f"EARLY_DECISION {mode}")

    def set_fast_mod_analysis_mode(self, mode: str) -> None:
        """Enable/disable Fast Analysis Mode. e.g. FAST_MODANA_MODE ON"""
        self.write(f"FAST_MODANA_MODE {mode}")

    def set_meas_sf_overlapping_nr(self, mode: str) -> None:
        """Set Measurement Subframe overlapping with NR symbols."""
        self.write(f"MEAS_SF_OVERLAPPING_NR {mode}")

    def set_meas_target_system(self, system: str) -> None:
        """Set measurement target system."""
        self.write(f"MEAS_TARGET_SYSTEM {system}")

    # =========================================================================
    # Power Control Tolerance (PCT) Settings
    # =========================================================================
    def set_pct_type(self, ptype: str) -> None:
        """
        Set Power Control Tolerance test type.
        ptype: 'ABS' | 'REL_UP' | 'REL_DOWN' | 'REL_ALT' | 'AGG' etc.
        """
        self.write(f"PCTTYPE {ptype}")

    def set_rel_sf(self, sf: int) -> None:
        """Set Relative Power measurement subframe. e.g. REL_SF 10"""
        self.write(f"REL_SF {sf}")

    def set_rel_rb1(self, rb: int) -> None:
        """Set Relative Power UL Number of RB1."""
        self.write(f"REL_RB1 {rb}")

    def set_rel_rb_start1(self, start: int) -> None:
        """Set Relative Power UL Starting RB1."""
        self.write(f"REL_RB_START1 {start}")

    def set_rel_rb2(self, rb: int) -> None:
        """Set Relative Power UL Number of RB2."""
        self.write(f"REL_RB2 {rb}")

    def set_rel_rb_start2(self, start: int) -> None:
        """Set Relative Power UL Starting RB2."""
        self.write(f"REL_RB_START2 {start}")

    def set_rel_rb_change(self, change: str) -> None:
        """Set Relative Power RB change mode."""
        self.write(f"REL_RBCHANGE {change}")

    def set_rel_initial_power(self, power: float) -> None:
        """Set Relative Power Initial Power. e.g. REL_INITPWR -10.0"""
        self.write(f"REL_INITPWR {power}")

    def set_rel_pumax_mode(self, mode: str) -> None:
        """Set Relative Power Pumax mode."""
        self.write(f"REL_PUMAX_MODE {mode}")

    # =========================================================================
    # EVM with Transient Period (EVMTP) Settings
    # =========================================================================
    def set_transient_capability(self, cap: str) -> None:
        """Set transient capability. e.g. TRANSIENT_CAPA 2US"""
        self.write(f"TRANSIENT_CAPA {cap}")

    def set_evmtp_hp_ul_rb(self, rb: int) -> None:
        """Set EVM-TP high power UL RB."""
        self.write(f"EVMTP_HP_ULRB {rb}")

    def set_evmtp_hp_ul_rb_start(self, start: int) -> None:
        """Set EVM-TP high power UL starting RB."""
        self.write(f"EVMTP_HP_ULRB_START {start}")

    def set_evmtp_lp_ul_rb(self, rb: int) -> None:
        """Set EVM-TP low power UL RB."""
        self.write(f"EVMTP_LP_ULRB {rb}")

    def set_evmtp_lp_ul_rb_start(self, start: int) -> None:
        """Set EVM-TP low power starting RB."""
        self.write(f"EVMTP_LP_ULRB_START {start}")

    # =========================================================================
    # EIS (FR2 OTA) Settings
    # =========================================================================
    def set_eis_level_step(self, step: float) -> None:
        """Set EIS level step (dB)."""
        self.write(f"EIS_LVLSTEP {step}")

    def set_eis_pol_switch_wait(self, wait_ms: int) -> None:
        """Set EIS polarization switch wait time (ms)."""
        self.write(f"EIS_POLSWWAIT {wait_ms}")

    def set_eis_wait(self, wait_ms: int) -> None:
        """Set EIS wait time (ms)."""
        self.write(f"EIS_WAIT {wait_ms}")

    # =========================================================================
    # Measurement Execution
    # =========================================================================
    def sweep(self) -> None:
        """Start measurement sweep (SWP) and wait for completion."""
        self.write("SWP")
        self.opc()

    def query_meas_status(self) -> str:
        """Query measurement status. Returns result of MSTAT?"""
        return self.query("MSTAT?")

    # =========================================================================
    # Measurement Result Queries
    # =========================================================================
    def query_power(self) -> str:
        """Query UE output power result (dBm). POWER?"""
        return self.query("POWER?")

    def query_channel_power(self, *args) -> str:
        """Query channel power. CHPWR? [args]"""
        cmd = "CHPWR?"
        if args:
            cmd += " " + ",".join(str(a) for a in args)
        return self.query(cmd)

    def query_mod_power(self) -> str:
        """Query modulation power result. MODPWR?"""
        return self.query("MODPWR?")

    def query_evm(self) -> str:
        """Query Error Vector Magnitude result. EVM?"""
        return self.query("EVM?")

    def query_rs_evm(self) -> str:
        """Query RS-EVM result. RSEVM?"""
        return self.query("RSEVM?")

    def query_tp_evm(self) -> str:
        """Query EVM with Transient Period result. TPEVM?"""
        return self.query("TPEVM?")

    def query_carrier_freq_error(self) -> str:
        """Query Carrier Frequency Error result. CARRFERR?"""
        return self.query("CARRFERR?")

    def query_carrier_leakage(self) -> str:
        """Query Carrier Leakage result. CARRLEAK?"""
        return self.query("CARRLEAK?")

    def query_obw(self) -> str:
        """Query Occupied Bandwidth result. OBW?"""
        return self.query("OBW?")

    def query_on_power(self) -> str:
        """Query ON power result. ONPWR?"""
        return self.query("ONPWR?")

    def query_off_power_before(self) -> str:
        """Query OFF power before result. OFFPWR_BEFORE?"""
        return self.query("OFFPWR_BEFORE?")

    def query_off_power_after(self) -> str:
        """Query OFF power after result. OFFPWR_AFTER?"""
        return self.query("OFFPWR_AFTER?")

    def query_timing_alignment_error(self) -> str:
        """Query Timing Alignment Error result. TMGALIGNERR?"""
        return self.query("TMGALIGNERR?")

    def query_spec_flatness(self, direction: str = "") -> str:
        """
        Query EVM Equalizer Spectrum Flatness result.
        direction: '' | 'RP1' | 'RP2' | 'RP12' | 'RP21'
        """
        if direction:
            return self.query(f"SPECFLAT_{direction}?")
        return self.query("SPECFLAT?")

    # --- SEM Results ---
    def query_sem_pass(self, mode: str = "") -> str:
        """Query SEM pass/fail. mode: '' | 'SUM'. SEMPASS? [SUM]"""
        cmd = "SEMPASS?"
        if mode:
            cmd += f" {mode}"
        return self.query(cmd)

    def query_ttl_worst_sem(self, mode: str = "") -> str:
        """Query total worst SEM result. TTL_WORST_SEM? [SUM]"""
        cmd = "TTL_WORST_SEM?"
        if mode:
            cmd += f" {mode}"
        return self.query(cmd)

    def query_ttl_worst_sem_level(self, mode: str = "") -> str:
        """Query total worst SEM level result. TTL_WORST_SEM_LV? [SUM]"""
        cmd = "TTL_WORST_SEM_LV?"
        if mode:
            cmd += f" {mode}"
        return self.query(cmd)

    # --- ACLR Results ---
    def query_aclr(self, *args) -> str:
        """Query ACLR result. ACLR? [args]"""
        cmd = "ACLR?"
        if args:
            cmd += " " + ",".join(str(a) for a in args)
        return self.query(cmd)

    # --- In-Band Emission Results ---
    def query_inband_emission_general(self, *args) -> str:
        """Query In-Band Emission general result. INBANDE_GEN? [args]"""
        cmd = "INBANDE_GEN?"
        if args:
            cmd += " " + ",".join(str(a) for a in args)
        return self.query(cmd)

    def query_inband_emission_leakage(self, *args) -> str:
        """Query In-Band Emission leakage result. INBANDE_LEAK? [args]"""
        cmd = "INBANDE_LEAK?"
        if args:
            cmd += " " + ",".join(str(a) for a in args)
        return self.query(cmd)

    def query_inband_emission_margin(self, *args) -> str:
        """Query In-Band Emission margin result. INBANDE_MARG? [args]"""
        cmd = "INBANDE_MARG?"
        if args:
            cmd += " " + ",".join(str(a) for a in args)
        return self.query(cmd)

    def query_inband_emission_margin_eutra(self, *args) -> str:
        """Query In-Band Emission margin (EUTRA) result. INBANDE_MARG_EUTRA? [args]"""
        cmd = "INBANDE_MARG_EUTRA?"
        if args:
            cmd += " " + ",".join(str(a) for a in args)
        return self.query(cmd)

    # --- Power Control Tolerance Results ---
    def query_pct_power(self) -> str:
        """Query PCT (Power Control Tolerance) power result. PCTPWR?"""
        return self.query("PCTPWR?")

    def query_pct_power2(self) -> str:
        """Query PCT power result 2. PCTPWR2?"""
        return self.query("PCTPWR2?")

    def query_pct_power_e1(self, mode: str = "") -> str:
        """Query PCT power E1. PCTPWRE1? [SUM]"""
        cmd = "PCTPWRE1?"
        if mode:
            cmd += f" {mode}"
        return self.query(cmd)

    def query_pct_power_e2(self) -> str:
        """Query PCT power E2. PCTPWRE2?"""
        return self.query("PCTPWRE2?")

    def query_pct_power_e3(self) -> str:
        """Query PCT power E3. PCTPWRE3?"""
        return self.query("PCTPWRE3?")

    def query_pct_rel(self) -> str:
        """Query PCT relative result. PCTREL?"""
        return self.query("PCTREL?")

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
        return self.query(cmd)

    def query_throughput_bler(self, cc: str = "") -> str:
        """Query Throughput BLER result."""
        cmd = "TPUT_BLER?"
        if cc:
            cmd += f" {cc}"
        return self.query(cmd)

    def query_throughput_bler_count(self, cc: str = "") -> str:
        """Query Throughput BLER count."""
        cmd = "TPUT_BLERCNT?"
        if cc:
            cmd += f" {cc}"
        return self.query(cmd)

    def query_throughput_bler_count_nack(self, cc: str = "") -> str:
        """Query Throughput BLER NACK count."""
        cmd = "TPUT_BLERCNTNACK?"
        if cc:
            cmd += f" {cc}"
        return self.query(cmd)

    def query_throughput_bler_count_dtx(self, cc: str = "") -> str:
        """Query Throughput BLER DTX count."""
        cmd = "TPUT_BLERCNTDTX?"
        if cc:
            cmd += f" {cc}"
        return self.query(cmd)

    def query_throughput_transport_block(self, cc: str = "") -> str:
        """Query Throughput Transport Block size."""
        cmd = "TPUT_TRANSBLOCK?"
        if cc:
            cmd += f" {cc}"
        return self.query(cmd)

    def query_throughput_total_fr1(self) -> str:
        """Query Throughput total FR1."""
        return self.query("TPUT_TOTAL_FR1?")

    def query_throughput_total_fr2(self) -> str:
        """Query Throughput total FR2."""
        return self.query("TPUT_TOTAL_FR2?")

    def query_throughput_bler_total_fr1(self) -> str:
        """Query Throughput BLER total FR1."""
        return self.query("TPUT_BLER_TOTAL_FR1?")

    # --- EIS Results (FR2 OTA) ---
    def query_eis(self) -> str:
        """Query EIS result (FR2). EIS?"""
        return self.query("EIS?")

    def query_peak_eirp(self) -> str:
        """Query Peak EIRP result. PEAKEIRP?"""
        return self.query("PEAKEIRP?")

    # --- TTL/Modulation Power ---
    def query_ttl_mod_power(self) -> str:
        """Query total modulation power. TTL_MODPWR?"""
        return self.query("TTL_MODPWR?")

    # --- Power Template Results ---
    def query_power_temp(self, *args) -> str:
        """Query Power Template result. PWRTEMP? [args]"""
        cmd = "PWRTEMP?"
        if args:
            cmd += " " + ",".join(str(a) for a in args)
        return self.query(cmd)

    def query_test_spec(self) -> str:
        """Query test specification. TEST_SPEC?"""
        return self.query("TEST_SPEC?")


# =============================================================================
# MT8821C (LTE) Command Extensions
# =============================================================================
class MT8821C(InstrumentBase):
    """
    Anritsu MT8821C LTE anchor commands (used via REM_DEST 8821C).

    Note: These commands are typically sent to the MT8000A which routes them
    to the MT8821C. When using with MT8000A, call mt8000a.set_remote_destination("8821C")
    first, then use these commands through the same VISA resource.
    """

    def preset(self) -> None:
        """Initialize MT8821C parameters."""
        self.write("PRESET")
        self.opc()

    def set_call_processing(self, on_off: bool) -> None:
        """Enable/disable LTE call processing."""
        self.write(f"CALLPROC {'ON' if on_off else 'OFF'}")

    def set_band(self, band: int) -> None:
        """Set LTE operation band. e.g. BAND 5"""
        self.write(f"BAND {band}")

    def set_bandwidth(self, bw: str) -> None:
        """Set LTE channel bandwidth. e.g. BANDWIDTH 5MHZ"""
        self.write(f"BANDWIDTH {bw}")

    def set_ul_channel(self, channel: int) -> None:
        """Set LTE UL channel. e.g. ULCHAN 18300"""
        self.write(f"ULCHAN {channel}")

    def set_frame_type(self, mode: str) -> None:
        """Set LTE duplex mode. e.g. FRAMETYPE FDD"""
        self.write(f"FRAMETYPE {mode}")

    def set_sim_model(self, model: str) -> None:
        """Set SIM model number for LTE. e.g. SIMMODELNUM P0250"""
        self.write(f"SIMMODELNUM {model}")

    def set_integrity(self, algorithm: str) -> None:
        """Set integrity protection. e.g. INTEGRITY SNOW3G"""
        self.write(f"INTEGRITY {algorithm}")

    def set_channel_coding(self, mode: str) -> None:
        """Set channel coding. e.g. CHCODING RMC"""
        self.write(f"CHCODING {mode}")

    def set_routing_mode(self, mode: str) -> None:
        """Set routing mode. e.g. TXIQROUTING SISO"""
        self.write(f"TXIQROUTING {mode}")

    def set_ul_rmc_rb(self, rb: int) -> None:
        """Set LTE UL RMC RB. e.g. ULRMC_RB 18"""
        self.write(f"ULRMC_RB {rb}")

    def set_ul_rb_start(self, start: int) -> None:
        """Set LTE UL Starting RB. e.g. ULRBSTART 82"""
        self.write(f"ULRBSTART {start}")

    def set_ul_rmc_mod(self, mod: str) -> None:
        """Set LTE UL RMC Modulation. e.g. ULRMC_MOD QPSK"""
        self.write(f"ULRMC_MOD {mod}")

    def set_dl_rmc_rb(self, rb: int) -> None:
        """Set LTE DL RMC RB."""
        self.write(f"DLRMC_RB {rb}")

    def set_dl_rb_start(self, start: int) -> None:
        """Set LTE DL Starting RB."""
        self.write(f"DLRB_START {start}")

    def set_input_level(self, level: float) -> None:
        """Set LTE input level (dBm)."""
        self.write(f"ILVL {level}")

    def set_output_level_epre(self, level: float) -> None:
        """Set LTE output level EPRE."""
        self.write(f"OLVL_EPRE {level}")

    def set_tpc_pattern(self, pattern: str) -> None:
        """Set LTE TPC pattern."""
        self.write(f"TPCPAT {pattern}")

    def set_max_ul_power(self, power: float) -> None:
        """Set LTE max UL power."""
        self.write(f"MAXULPWR {power}")

    def call_sa(self) -> None:
        """Initiate LTE call."""
        self.write("CALLSA")

    def query_call_status(self) -> str:
        """Query LTE call status."""
        return self.query("CALLSTAT?")

    def query_power(self) -> str:
        """Query LTE power result."""
        return self.query("POWER?")

    def all_meas_items_off(self) -> None:
        """Turn off all LTE measurement items."""
        self.write("ALLMEASITEMS_OFF")
        self.opc()

    def set_power_meas(self, on: bool) -> None:
        """Enable/disable LTE power measurement."""
        self.write(f"PWR_MEAS {'ON' if on else 'OFF'}")

    def set_throughput_meas(self, on: bool) -> None:
        """Enable/disable LTE throughput measurement."""
        self.write(f"TPUT_MEAS {'ON' if on else 'OFF'}")

    def sweep(self) -> None:
        """Start LTE measurement sweep."""
        self.write("SWP")
        self.opc()

    def query_meas_status(self) -> str:
        """Query LTE measurement status."""
        return self.query("MSTAT?")


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
    mt.preset_sa()
    mt.set_ran_operation("SA")
    mt.set_test_interface("SLOT1", "ARGV")
    mt.set_test_slot("SLOT1")
    mt.set_call_processing(True)
    mt.set_sim_model("P0135")
    mt.set_integrity("SNOW3G")

    # --- Frame & Frequency Configuration ---
    mt.set_frame_type("TDD")
    mt.set_channel_setting_mode("LOWESTGSCN")
    mt.set_band("PCC", 78)
    mt.set_dl_scs("PCC", "30KHZ")
    mt.set_dl_bandwidth("PCC", "100MHZ")
    mt.set_dl_channel("PCC", 623334)
    mt.set_offset_carrier("PCC", 0)
    mt.set_ssb_channel("PCC", 620352)
    mt.set_ssb_scs("PCC", "30KHZ")

    # --- TDD Configuration ---
    mt.set_dl_ul_period("PCC", "5MS")
    mt.set_dl_duration("PCC", 8)
    mt.set_ul_duration("PCC", 2)
    mt.set_dl_symbols("PCC", 6)
    mt.set_ul_symbols("PCC", 4)

    # --- DCI Configuration ---
    mt.set_dci_format("FORMAT0_1_AND_1_1")
    mt.set_scheduling("STATIC")
    mt.set_group_hopping_cch("ENABLE")

    # --- Call Connection ---
    mt.call_sa()
    connected = mt.wait_for_call_connected(timeout_s=60)
    if not connected:
        raise RuntimeError("Call connection failed")

    # --- Measurement Configuration ---
    mt.all_meas_items_off()
    mt.set_power_meas(True, avg=1)

    # --- UL RMC Settings ---
    mt.set_ul_waveform("PCC", "DFTOFDM")
    mt.set_ul_rmc_rb("PCC", 162)
    mt.set_ul_rb_start("PCC", 0)
    mt.set_ul_mcs_index("PCC", 10)

    # --- DL RMC Settings ---
    mt.set_dl_rmc_rb("PCC", 0)
    mt.set_dl_rb_start("PCC", 0)
    mt.set_dl_mcs_table("PCC", "64QAM")
    mt.set_dl_mcs_index("PCC", 4)

    # --- Input Level & TPC ---
    mt.set_input_level("PCC", 23)
    mt.set_tpc_pattern("ALL3")

    # --- Execute Measurement ---
    mt.sweep()
    status = mt.query_meas_status()
    power = mt.query_power()

    # --- Reset ---
    mt.set_tpc_pattern("AUTO")

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

    # --- Switch to LTE (MT8821C) for anchor config ---
    mt.set_remote_destination("8821C")
    MT8821C(mt._inst).preset()
    MT8821C(mt._inst).set_call_processing(True)
    MT8821C(mt._inst).set_band(41)
    MT8821C(mt._inst).set_bandwidth("20MHZ")
    MT8821C(mt._inst).set_sim_model("P0250")
    MT8821C(mt._inst).set_integrity("SNOW3G")

    # --- Switch back to NR ---
    mt.set_remote_destination("8000A")

    # --- NR Frame & Frequency ---
    mt.set_frame_type("TDD")
    mt.set_band("PCC", 41)
    mt.set_dl_scs("PCC", "30KHZ")
    mt.set_dl_bandwidth("PCC", "100MHZ")
    mt.set_dl_channel("PCC", 509202)
    mt.set_offset_carrier("PCC", 0)
    mt.set_channel_setting_mode("LOWESTGSCN")
    mt.set_ssb_channel("PCC", 500190)
    mt.set_ssb_scs("PCC", "30KHZ")

    # --- TDD Configuration ---
    mt.set_dl_ul_period("PCC", "5MS")
    mt.set_dl_duration("PCC", 8)
    mt.set_ul_duration("PCC", 2)
    mt.set_dl_symbols("PCC", 6)
    mt.set_ul_symbols("PCC", 4)

    # --- EN-DC Measurement Mode ---
    mt.set_endc_meas_mode("NR")

    # --- Call Connection (LTE then NR) ---
    mt.set_remote_destination("8821C")
    MT8821C(mt._inst).call_sa()
    mt.set_remote_destination("8000A")
    mt.call_sa()
    connected = mt.wait_for_call_connected(timeout_s=60)
    if not connected:
        raise RuntimeError("NR call connection failed")

    # --- Measurement Configuration ---
    mt.all_meas_items_off()
    mt.set_mod_meas(True, avg=20)

    # --- UL RMC Settings ---
    mt.set_ul_waveform("PCC", "DFTOFDM")
    mt.set_ul_rmc_rb("PCC", 162)
    mt.set_ul_rb_start("PCC", 0)
    mt.set_ul_mcs_index("PCC", 2)

    # --- Level & TPC ---
    mt.set_input_level("PCC", 23)
    mt.set_tpc_pattern("ALL3")

    # --- Execute Measurement ---
    mt.sweep()
    status = mt.query_meas_status()
    evm = mt.query_evm()
    carrier_leakage = mt.query_carrier_leakage()

    # --- Reset ---
    mt.set_tpc_pattern("AUTO")

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
    mt.all_meas_items_off()
    mt.set_throughput_meas(True)
    mt.set_throughput_sample(2466)
    mt.set_early_decision(True)

    # --- DL RMC Settings ---
    mt.set_dl_rmc_rb("PCC", 133)
    mt.set_dl_mcs_table("PCC", "64QAM")
    mt.set_dl_mcs_index("PCC", 4)
    mt.set_avoid_csirs_for_ref_sens("PCC", "ON")

    # --- Output Level (Reference Sensitivity) ---
    mt.set_output_level("PCC", -88.1)

    # --- Input Level & TPC ---
    mt.set_input_level("PCC", 23)
    mt.set_tpc_pattern("ALL3")

    # --- Execute Measurement ---
    mt.sweep()
    status = mt.query_meas_status()
    throughput = mt.query_throughput("PER")

    # --- Reset ---
    mt.set_tpc_pattern("AUTO")
    mt.set_early_decision("OFF")
    mt.set_avoid_csirs_for_ref_sens("PCC", "OFF")

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
    print("  mt = MT8000A(inst)")
    print()
    print("  # Set band and frequency")
    print("  mt.set_band('PCC', 78)")
    print("  mt.set_dl_scs('PCC', '30KHZ')")
    print("  mt.set_dl_bandwidth('PCC', '100MHZ')")
    print()
    print("  # Run power measurement")
    print("  mt.all_meas_items_off()")
    print("  mt.set_power_meas(True, avg=1)")
    print("  mt.sweep()")
    print("  result = mt.query_power()")
    print("  print(f'Power: {result} dBm')")

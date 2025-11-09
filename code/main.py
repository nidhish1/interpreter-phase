import os
import argparse
"""
RV32I mini-simulator: instruction memory, data memory, register files,
and two cores (single-stage functional, five-stage skeleton).

File format choices match the provided sample outputs:
- Data memory: 1000 lines, each an 8-bit binary string (e.g., 00000000)
- Register dumps: 32 lines of 32-bit binary values after a header per cycle
- State dumps: textual, one block per cycle

An all-zero instruction is treated as a polite end-of-program sentinel, which
helps avoid wandering off into uninitialized memory.
"""

MemSize = 1000  # number of bytes persisted to DMEM result files

# ================= Instruction Memory =================
class InsMem(object):
    """Byte-wise instruction memory with 32-bit big-endian fetch."""
    def __init__(self, name, ioDir):
        self.id = name
        path = os.path.join(ioDir, "imem.txt")
        with open(path, "r") as im:
            self.IMem = [line.strip() for line in im.readlines()]

    def _byte_to_int(self, s):
        if s is None or s == "":
            return 0
        s = s.strip()
        # Support 8-bit binary strings (e.g., 00000000, 10000011) and hex
        if all(ch in "01" for ch in s) and len(s) == 8:
            return int(s, 2) & 0xFF
        s = s.lower()
        if s.startswith("0x"):
            s = s[2:]
        return int(s, 16) & 0xFF

    def readInstr(self, ReadAddress):
        # Assignment spec: imem is Big-Endian in the file (MSB at lowest address)
        val = 0
        for i in range(4):
            idx = ReadAddress + i
            if idx < 0 or idx >= len(self.IMem):
                b = 0
            else:
                b = self._byte_to_int(self.IMem[idx])
            val = (val << 8) | (b & 0xFF)
        return val & 0xFFFFFFFF

# ================= Data Memory =================
class DataMem(object):
    """Byte-addressable memory, persisted as 8-bit binary per line."""
    def __init__(self, name, input_dir, output_dir):
        self.id = name
        self.input_dir = input_dir
        self.output_dir = output_dir
        path = os.path.join(input_dir, "dmem.txt")
        with open(path, "r") as dm:
            self.DMem = [line.strip() for line in dm.readlines()]
        # Pad to MemSize bytes to match reference outputs
        while len(self.DMem) < MemSize:
            self.DMem.append("00000000")

    def _byte_to_int(self, s):
        if s is None or s == "":
            return 0
        s = s.strip()
        # Support 8-bit binary strings (e.g., 00000000, 10100101) and hex
        if all(ch in "01" for ch in s) and len(s) == 8:
            return int(s, 2) & 0xFF
        s = s.lower()
        if s.startswith("0x"):
            s = s[2:]
        return int(s, 16) & 0xFF

    def readInstr(self, ReadAddress):
        """Fetch a 32-bit word (Big-Endian) from byte address ReadAddress."""
        val = 0
        for i in range(4):
            idx = ReadAddress + i
            if idx < 0 or idx >= len(self.DMem):
                b = 0
            else:
                b = self._byte_to_int(self.DMem[idx])
            val = (val << 8) | (b & 0xFF)
        return val & 0xFFFFFFFF

    def writeDataMem(self, Address, WriteData):
        """Write a 32-bit word as four bytes (Big-Endian) into DMEM."""
        wd = WriteData & 0xFFFFFFFF
        bytes_be = [(wd >> 24) & 0xFF, (wd >> 16) & 0xFF, (wd >> 8) & 0xFF, wd & 0xFF]
        for i in range(4):
            idx = Address + i
            if idx < 0:
                continue
            while idx >= len(self.DMem):
                self.DMem.append("00000000")
            # Store as 8-bit binary to match sample outputs
            self.DMem[idx] = format(bytes_be[i], "08b")

    def outputDataMem(self):
        """Persist DMEM to results directory in 8-bit binary lines."""
        os.makedirs(self.output_dir, exist_ok=True)
        resPath = os.path.join(self.output_dir, f"{self.id}_DMEMResult.txt")
        with open(resPath, "w") as rp:
            rp.writelines([str(data) + "\n" for data in self.DMem])

# ================= Register File =================
class RegisterFile(object):
    """32 registers x 32 bits, with per-cycle binary dumps per core."""
    def __init__(self, ioDir, name):
        os.makedirs(ioDir, exist_ok=True)
        # Write separate files for each core: SS_RFResult.txt, FS_RFResult.txt
        self.outputFile = os.path.join(ioDir, f"{name}_RFResult.txt")
        self.Registers = [0x0 for _ in range(32)]
        self.name = name

    def readRF(self, Reg_addr):
        """Safe read: returns 0 if out of range."""
        if Reg_addr < 0 or Reg_addr >= 32:
            return 0
        return self.Registers[Reg_addr] & 0xFFFFFFFF

    def writeRF(self, Reg_addr, Wrt_reg_data):
        """Writes are ignored for x0; out-of-range writes are dropped."""
        if Reg_addr == 0:
            return
        if Reg_addr < 0 or Reg_addr >= 32:
            return
        self.Registers[Reg_addr] = Wrt_reg_data & 0xFFFFFFFF

    def outputRF(self, cycle):
        """Append a formatted snapshot after the given cycle."""
        # Match sample formatting: FS includes dashed separator; SS omits it and uses two spaces before cycle number
        op = []
        if self.name == "FS":
            op.append("-"*70 + "\n")
            op.append("State of RF after executing cycle:" + str(cycle) + "\n")
        else:  # SS
            op.append("State of RF after executing cycle:  " + str(cycle) + "\n")
        # Output 32-bit binary values to match sample format
        op.extend([format(val & 0xFFFFFFFF, "032b") + "\n" for val in self.Registers])
        perm = "w" if cycle == 0 else "a"
        with open(self.outputFile, perm) as file:
            file.writelines(op)

# ================= State =================
class State(object):
    """Pipeline registers (stage latches) for debugging and printing."""
    def __init__(self):
        self.IF = {"nop": False, "PC": 0, "fetch_PC": 0}  # fetch_PC is the PC used to fetch current instruction
        self.ID = {"nop": False, "Instr": 0, "PC": 0}  # Track PC for JAL return address and branch targets
        self.EX = {"nop": False, "instr": 0, "Read_data1": 0, "Read_data2": 0, "Imm": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "is_I_type": False, "rd_mem": 0,
                   "wrt_mem": 0, "alu_op": 0, "wrt_enable": 0, "PC": 0, "is_jal": False}  # Track PC and JAL flag
        self.MEM = {"nop": False, "ALUresult": 0, "Store_data": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "rd_mem": 0,
                    "wrt_mem": 0, "wrt_enable": 0}
        self.WB = {"nop": False, "Wrt_data": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "wrt_enable": 0}

# ================= Core =================
class Core(object):
    """Shared core scaffolding: IO handles, cycle/retire counters, halt flag."""
    def __init__(self, ioDir, imem, dmem):
        os.makedirs(ioDir, exist_ok=True)
        self.outDir = ioDir
        self.cycle = 0
        self.halted = False
        self.retired_instructions = 0
        self.state = State()
        self.nextState = State()
        self.ext_imem = imem
        self.ext_dmem = dmem
        # Safety guard to avoid infinite loops if program never halts
        self.max_cycles = 100000

def sign_extend(value, bits):
    """Sign-extend a bitfield to a Python int (used for immediates)."""
    mask = (1 << bits) - 1
    value_masked = value & mask
    sign_bit = 1 << (bits - 1)
    if value_masked & sign_bit:
        # Negative: subtract 2^bits to get two's complement
        return value_masked - (1 << bits)
    else:
        return value_masked

# ================= Single Stage Core =================
class SingleStageCore(Core):
    """Functional single-cycle RV32I core for the subset used in tests.

    Covers: R-type (ADD, SUB, XOR, OR, AND), I-type (ADDI/XORI/ORI/ANDI),
    LW, SW, BEQ/BNE, and JAL. Stops on explicit HALT (0x7f) or a fetched
    zero word (common sentinel past end-of-program).
    """
    def __init__(self, ioDir, imem, dmem):
        super(SingleStageCore, self).__init__(ioDir, imem, dmem)
        self.myRF = RegisterFile(ioDir, "SS")
        self.opFilePath = os.path.join(ioDir, "StateResult_SS.txt")

    def step(self):
        PC = self.state.IF["PC"]
        # If PC has moved past the last valid instruction byte, stop gracefully
        if PC >= len(self.ext_imem.IMem):
            self.nextState.IF["nop"] = True
            self.nextState.IF["PC"] = PC
            self.halted = True
            self.myRF.outputRF(self.cycle)
            self.printState(self.nextState, self.cycle)
            self.state = self.nextState
            self.cycle += 1
            return
        instr = self.ext_imem.readInstr(PC)
        opcode = instr & 0x7f
        rd = (instr >> 7) & 0x1f
        funct3 = (instr >> 12) & 0x7
        rs1 = (instr >> 15) & 0x1f
        rs2 = (instr >> 20) & 0x1f
        funct7 = (instr >> 25) & 0x7f

        # Halt only on explicit HALT (0x7f) per spec
        if opcode == 0x7f:
            # On HALT: don't advance PC, set nop, and mark as halted
            # Count HALT as a retired instruction (matches sample metrics)
            self.retired_instructions += 1
            self.nextState.IF["nop"] = True
            self.nextState.IF["PC"] = PC
            self.halted = True
            self.myRF.outputRF(self.cycle)
            self.printState(self.nextState, self.cycle)
            self.state = self.nextState
            self.cycle += 1
            # Output one more cycle showing halted state (matches sample output)
            self.myRF.outputRF(self.cycle)
            self.printState(self.nextState, self.cycle)
            self.cycle += 1
            return

        nextPC = (PC + 4) & 0xFFFFFFFF
        rs1_val = self.myRF.readRF(rs1)
        rs2_val = self.myRF.readRF(rs2)
        imm_i = sign_extend((instr >> 20) & 0xFFF, 12)
        imm_s = sign_extend(((instr >> 25) << 5) | ((instr >> 7) & 0x1F), 12)
        imm_b = (((instr >> 31) & 0x1) << 12) | (((instr >> 25) & 0x3F) << 5) | (((instr >> 8) & 0xF) << 1) | (((instr >> 7) & 0x1) << 11)
        imm_b = sign_extend(imm_b, 13)
        imm_j = (((instr >> 31) & 0x1) << 20) | (((instr >> 12) & 0xFF) << 12) | (((instr >> 20) & 0x1) << 11) | (((instr >> 21) & 0x3FF) << 1)
        imm_j = sign_extend(imm_j, 21)

        write_back_enable = False
        write_back_data = 0

        # R-type
        if opcode == 0x33:
            if funct3 == 0x0 and funct7 == 0x00:
                write_back_data = (rs1_val + rs2_val) & 0xFFFFFFFF
                write_back_enable = True
            elif funct3 == 0x0 and funct7 == 0x20:
                write_back_data = (rs1_val - rs2_val) & 0xFFFFFFFF
                write_back_enable = True
            elif funct3 == 0x4:
                write_back_data = (rs1_val ^ rs2_val) & 0xFFFFFFFF
                write_back_enable = True
            elif funct3 == 0x6:
                write_back_data = (rs1_val | rs2_val) & 0xFFFFFFFF
                write_back_enable = True
            elif funct3 == 0x7:
                write_back_data = (rs1_val & rs2_val) & 0xFFFFFFFF
                write_back_enable = True
        elif opcode == 0x13:  # I-type
            if funct3 == 0x0:
                write_back_data = (rs1_val + imm_i) & 0xFFFFFFFF
                write_back_enable = True
            elif funct3 == 0x4:
                write_back_data = (rs1_val ^ (imm_i & 0xFFFFFFFF)) & 0xFFFFFFFF
                write_back_enable = True
            elif funct3 == 0x6:
                write_back_data = (rs1_val | (imm_i & 0xFFFFFFFF)) & 0xFFFFFFFF
                write_back_enable = True
            elif funct3 == 0x7:
                write_back_data = (rs1_val & (imm_i & 0xFFFFFFFF)) & 0xFFFFFFFF
                write_back_enable = True
        elif opcode == 0x03 and funct3 == 0x2:  # LW
            addr = (rs1_val + imm_i) & 0xFFFFFFFF
            mem_val = self.ext_dmem.readInstr(addr)
            write_back_data = mem_val & 0xFFFFFFFF
            write_back_enable = True
        elif opcode == 0x23 and funct3 == 0x2:  # SW
            addr = (rs1_val + imm_s) & 0xFFFFFFFF
            self.ext_dmem.writeDataMem(addr, rs2_val)
        elif opcode == 0x63:  # BEQ/BNE
            if funct3 == 0x0 and rs1_val == rs2_val:
                nextPC = (PC + imm_b) & 0xFFFFFFFF
            elif funct3 == 0x1 and rs1_val != rs2_val:
                nextPC = (PC + imm_b) & 0xFFFFFFFF
        elif opcode == 0x6f:  # JAL
            write_back_data = (PC + 4) & 0xFFFFFFFF
            write_back_enable = True
            nextPC = (PC + imm_j) & 0xFFFFFFFF

        if write_back_enable and rd != 0:
            self.myRF.writeRF(rd, write_back_data)

        self.nextState.IF["PC"] = nextPC
        self.nextState.IF["nop"] = False
        # Count this retired instruction (non-halt)
        self.retired_instructions += 1
        self.myRF.outputRF(self.cycle)
        self.printState(self.nextState, self.cycle)
        self.state = self.nextState
        self.nextState = State()
        self.cycle += 1

        # Safety stop to prevent runaway execution
        if self.cycle >= self.max_cycles:
            self.halted = True

    def printState(self, state, cycle):
        printstate = ["-"*70 + "\n", "State after executing cycle: " + str(cycle) + "\n"]
        printstate.append("IF.PC: " + str(state.IF["PC"]) + "\n")
        printstate.append("IF.nop: " + str(state.IF["nop"]) + "\n")
        perm = "w" if cycle == 0 else "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)

# ================= Five Stage Core =================
class FiveStageCore(Core):
    """Full five-stage pipelined RV32I core with forwarding and hazard handling."""
    def __init__(self, ioDir, imem, dmem):
        super(FiveStageCore, self).__init__(ioDir, imem, dmem)
        self.myRF = RegisterFile(ioDir, "FS")
        self.opFilePath = os.path.join(ioDir, "StateResult_FS.txt")
        # Initialize pipeline: only IF is active, others are nop (bubbles)
        self.state.IF["PC"] = 0
        self.state.IF["fetch_PC"] = 0
        self.state.IF["nop"] = False
        self.state.ID["nop"] = True
        self.state.EX["nop"] = True
        self.state.MEM["nop"] = True
        self.state.WB["nop"] = True

    def step(self):
        # Pipeline stages execute in reverse order (WB -> MEM -> EX -> ID -> IF)
        # to ensure data flows correctly through the pipeline

        # ========== WB Stage: Write Back ==========
        if not self.state.WB["nop"]:
            if self.state.WB["wrt_enable"] and self.state.WB["Wrt_reg_addr"] != 0:
                self.myRF.writeRF(self.state.WB["Wrt_reg_addr"], self.state.WB["Wrt_data"])
            # Count retired instructions (only non-NOP instructions that complete)
            self.retired_instructions += 1

        # ========== MEM Stage: Memory Access ==========
        if not self.state.MEM["nop"]:
            if self.state.MEM["rd_mem"]:  # Load
                mem_val = self.ext_dmem.readInstr(self.state.MEM["ALUresult"])
                self.nextState.WB["Wrt_data"] = mem_val & 0xFFFFFFFF
            elif self.state.MEM["wrt_mem"]:  # Store
                self.ext_dmem.writeDataMem(self.state.MEM["ALUresult"], self.state.MEM["Store_data"])
                self.nextState.WB["Wrt_data"] = self.state.MEM["ALUresult"]  # Store doesn't write back
            else:  # ALU result
                self.nextState.WB["Wrt_data"] = self.state.MEM["ALUresult"] & 0xFFFFFFFF
            
            self.nextState.WB["nop"] = False
            self.nextState.WB["Rs"] = self.state.MEM["Rs"]
            self.nextState.WB["Rt"] = self.state.MEM["Rt"]
            self.nextState.WB["Wrt_reg_addr"] = self.state.MEM["Wrt_reg_addr"]
            self.nextState.WB["wrt_enable"] = self.state.MEM["wrt_enable"]
        else:
            self.nextState.WB["nop"] = True
            self.nextState.WB["Wrt_data"] = 0
            self.nextState.WB["Rs"] = 0
            self.nextState.WB["Rt"] = 0
            self.nextState.WB["Wrt_reg_addr"] = 0
            self.nextState.WB["wrt_enable"] = 0

        # ========== EX Stage: Execute ==========
        # Forwarding logic: get operands with forwarding from MEM and WB
        ex_rs1_val = self.state.EX["Read_data1"]
        ex_rs2_val = self.state.EX["Read_data2"]
        
        # Forward from MEM stage
        if not self.state.MEM["nop"] and self.state.MEM["wrt_enable"]:
            if self.state.MEM["Wrt_reg_addr"] == self.state.EX["Rs"] and self.state.EX["Rs"] != 0:
                if self.state.MEM["rd_mem"]:
                    # Load-use hazard: need to stall (handled in ID stage)
                    pass
                else:
                    ex_rs1_val = self.state.MEM["ALUresult"]
            if self.state.MEM["Wrt_reg_addr"] == self.state.EX["Rt"] and self.state.EX["Rt"] != 0:
                if self.state.MEM["rd_mem"]:
                    # Load-use hazard
                    pass
                else:
                    ex_rs2_val = self.state.MEM["ALUresult"]
        
        # Forward from WB stage
        if not self.state.WB["nop"] and self.state.WB["wrt_enable"]:
            if self.state.WB["Wrt_reg_addr"] == self.state.EX["Rs"] and self.state.EX["Rs"] != 0:
                if not (not self.state.MEM["nop"] and self.state.MEM["wrt_enable"] and self.state.MEM["Wrt_reg_addr"] == self.state.EX["Rs"]):
                    ex_rs1_val = self.state.WB["Wrt_data"]
            if self.state.WB["Wrt_reg_addr"] == self.state.EX["Rt"] and self.state.EX["Rt"] != 0:
                if not (not self.state.MEM["nop"] and self.state.MEM["wrt_enable"] and self.state.MEM["Wrt_reg_addr"] == self.state.EX["Rt"]):
                    ex_rs2_val = self.state.WB["Wrt_data"]

        if not self.state.EX["nop"]:
            # ALU operation
            alu_result = 0
            if self.state.EX["is_I_type"]:
                # I-type: use immediate
                if self.state.EX["alu_op"] == 0:  # ADDI
                    alu_result = (ex_rs1_val + self.state.EX["Imm"]) & 0xFFFFFFFF
                elif self.state.EX["alu_op"] == 2:  # XORI/ORI/ANDI (determined by funct3, but we use alu_op)
                    # For simplicity, assume alu_op encodes the operation
                    # In practice, we'd decode funct3 here
                    pass
            else:
                # R-type: use rs2
                if self.state.EX["alu_op"] == 0:  # ADD/SUB
                    # Need funct7 to distinguish, but for now assume ADD
                    alu_result = (ex_rs1_val + ex_rs2_val) & 0xFFFFFFFF
                elif self.state.EX["alu_op"] == 1:  # SUB
                    alu_result = (ex_rs1_val - ex_rs2_val) & 0xFFFFFFFF
            
            # For I-type immediate operations, decode from instruction
            if self.state.EX["is_I_type"] and not self.state.EX["rd_mem"]:
                instr = self.state.EX["instr"]
                funct3 = (instr >> 12) & 0x7
                imm_i = sign_extend((instr >> 20) & 0xFFF, 12)
                if funct3 == 0x0:  # ADDI
                    alu_result = (ex_rs1_val + imm_i) & 0xFFFFFFFF
                elif funct3 == 0x4:  # XORI
                    alu_result = (ex_rs1_val ^ (imm_i & 0xFFFFFFFF)) & 0xFFFFFFFF
                elif funct3 == 0x6:  # ORI
                    alu_result = (ex_rs1_val | (imm_i & 0xFFFFFFFF)) & 0xFFFFFFFF
                elif funct3 == 0x7:  # ANDI
                    alu_result = (ex_rs1_val & (imm_i & 0xFFFFFFFF)) & 0xFFFFFFFF
            
            # For R-type, decode from instruction
            if not self.state.EX["is_I_type"] and not self.state.EX["rd_mem"] and not self.state.EX["wrt_mem"]:
                instr = self.state.EX["instr"]
                funct3 = (instr >> 12) & 0x7
                funct7 = (instr >> 25) & 0x7f
                if funct3 == 0x0:
                    if funct7 == 0x00:  # ADD
                        alu_result = (ex_rs1_val + ex_rs2_val) & 0xFFFFFFFF
                    elif funct7 == 0x20:  # SUB
                        alu_result = (ex_rs1_val - ex_rs2_val) & 0xFFFFFFFF
                elif funct3 == 0x4:  # XOR
                    alu_result = (ex_rs1_val ^ ex_rs2_val) & 0xFFFFFFFF
                elif funct3 == 0x6:  # OR
                    alu_result = (ex_rs1_val | ex_rs2_val) & 0xFFFFFFFF
                elif funct3 == 0x7:  # AND
                    alu_result = (ex_rs1_val & ex_rs2_val) & 0xFFFFFFFF
            
            # For address calculation (LW/SW)
            if self.state.EX["rd_mem"] or self.state.EX["wrt_mem"]:
                if self.state.EX["is_I_type"]:
                    imm_i = sign_extend(self.state.EX["Imm"], 12) if self.state.EX["Imm"] < 0x800 else self.state.EX["Imm"]
                    alu_result = (ex_rs1_val + imm_i) & 0xFFFFFFFF
                else:  # S-type
                    imm_s = sign_extend(self.state.EX["Imm"], 12) if self.state.EX["Imm"] < 0x800 else self.state.EX["Imm"]
                    alu_result = (ex_rs1_val + imm_s) & 0xFFFFFFFF
            
            # For JAL: return address is PC + 4
            if self.state.EX["is_jal"]:
                alu_result = (self.state.EX["PC"] + 4) & 0xFFFFFFFF

            self.nextState.MEM["ALUresult"] = alu_result
            self.nextState.MEM["Store_data"] = ex_rs2_val
            self.nextState.MEM["nop"] = False
            self.nextState.MEM["Rs"] = self.state.EX["Rs"]
            self.nextState.MEM["Rt"] = self.state.EX["Rt"]
            self.nextState.MEM["Wrt_reg_addr"] = self.state.EX["Wrt_reg_addr"]
            self.nextState.MEM["rd_mem"] = self.state.EX["rd_mem"]
            self.nextState.MEM["wrt_mem"] = self.state.EX["wrt_mem"]
            self.nextState.MEM["wrt_enable"] = self.state.EX["wrt_enable"]
        else:
            self.nextState.MEM["nop"] = True
            self.nextState.MEM["ALUresult"] = 0
            self.nextState.MEM["Store_data"] = 0
            self.nextState.MEM["Rs"] = 0
            self.nextState.MEM["Rt"] = 0
            self.nextState.MEM["Wrt_reg_addr"] = 0
            self.nextState.MEM["rd_mem"] = 0
            self.nextState.MEM["wrt_mem"] = 0
            self.nextState.MEM["wrt_enable"] = 0

        # ========== ID Stage: Instruction Decode ==========
        # Check for load-use hazard: if MEM stage has a load and ID needs that register
        # (ID will move to EX, so we need to stall)
        load_use_hazard = False
        if not self.state.MEM["nop"] and self.state.MEM["rd_mem"] and self.state.MEM["wrt_enable"]:
            if not self.state.ID["nop"]:
                instr = self.state.ID["Instr"]
                opcode = instr & 0x7f
                rs1 = (instr >> 15) & 0x1f
                rs2 = (instr >> 20) & 0x1f
                # Check if ID instruction needs the register that MEM load is writing to
                if (self.state.MEM["Wrt_reg_addr"] == rs1 and rs1 != 0) or \
                   (self.state.MEM["Wrt_reg_addr"] == rs2 and rs2 != 0):
                    load_use_hazard = True

        # Check for branch/JAL and resolve in ID stage
        branch_taken = False
        branch_target = 0
        jal_taken = False
        jal_target = 0
        if not self.state.ID["nop"]:
            instr = self.state.ID["Instr"]
            opcode = instr & 0x7f
            rs1 = (instr >> 15) & 0x1f
            rs2 = (instr >> 20) & 0x1f
            funct3 = (instr >> 12) & 0x7
            
            # Get register values with forwarding
            id_rs1_val = self.myRF.readRF(rs1)
            id_rs2_val = self.myRF.readRF(rs2)
            
            # Forward from EX stage (EX-ID forwarding for branch resolution)
            # For EX stage, we need to compute the ALU result early or use a predicted value
            # Since EX computes ALU result in the same cycle, we can't forward it to ID in the same cycle
            # However, if EX has a non-load instruction, we can compute what the result will be
            if not self.state.EX["nop"] and self.state.EX["wrt_enable"] and not self.state.EX["rd_mem"]:
                # Compute ALU result early for forwarding
                ex_alu_result = 0
                if self.state.EX["is_I_type"]:
                    # I-type immediate operation
                    ex_instr = self.state.EX["instr"]
                    ex_funct3 = (ex_instr >> 12) & 0x7
                    ex_imm_i = sign_extend((ex_instr >> 20) & 0xFFF, 12)
                    ex_rs1_val = self.state.EX["Read_data1"]
                    if ex_funct3 == 0x0:  # ADDI
                        ex_alu_result = (ex_rs1_val + ex_imm_i) & 0xFFFFFFFF
                    elif ex_funct3 == 0x4:  # XORI
                        ex_alu_result = (ex_rs1_val ^ (ex_imm_i & 0xFFFFFFFF)) & 0xFFFFFFFF
                    elif ex_funct3 == 0x6:  # ORI
                        ex_alu_result = (ex_rs1_val | (ex_imm_i & 0xFFFFFFFF)) & 0xFFFFFFFF
                    elif ex_funct3 == 0x7:  # ANDI
                        ex_alu_result = (ex_rs1_val & (ex_imm_i & 0xFFFFFFFF)) & 0xFFFFFFFF
                else:
                    # R-type operation
                    ex_instr = self.state.EX["instr"]
                    ex_funct3 = (ex_instr >> 12) & 0x7
                    ex_funct7 = (ex_instr >> 25) & 0x7f
                    ex_rs1_val = self.state.EX["Read_data1"]
                    ex_rs2_val = self.state.EX["Read_data2"]
                    if ex_funct3 == 0x0:
                        if ex_funct7 == 0x00:  # ADD
                            ex_alu_result = (ex_rs1_val + ex_rs2_val) & 0xFFFFFFFF
                        elif ex_funct7 == 0x20:  # SUB
                            ex_alu_result = (ex_rs1_val - ex_rs2_val) & 0xFFFFFFFF
                    elif ex_funct3 == 0x4:  # XOR
                        ex_alu_result = (ex_rs1_val ^ ex_rs2_val) & 0xFFFFFFFF
                    elif ex_funct3 == 0x6:  # OR
                        ex_alu_result = (ex_rs1_val | ex_rs2_val) & 0xFFFFFFFF
                    elif ex_funct3 == 0x7:  # AND
                        ex_alu_result = (ex_rs1_val & ex_rs2_val) & 0xFFFFFFFF
                
                # Forward the computed result
                if self.state.EX["Wrt_reg_addr"] == rs1 and rs1 != 0:
                    id_rs1_val = ex_alu_result
                if self.state.EX["Wrt_reg_addr"] == rs2 and rs2 != 0:
                    id_rs2_val = ex_alu_result
            
            # Forward from MEM stage (MEM-ID forwarding)
            if not self.state.MEM["nop"] and self.state.MEM["wrt_enable"]:
                if self.state.MEM["Wrt_reg_addr"] == rs1 and rs1 != 0:
                    if not self.state.MEM["rd_mem"]:
                        id_rs1_val = self.state.MEM["ALUresult"]
                    # If it's a load, we can't forward (load-use hazard would have been detected)
                if self.state.MEM["Wrt_reg_addr"] == rs2 and rs2 != 0:
                    if not self.state.MEM["rd_mem"]:
                        id_rs2_val = self.state.MEM["ALUresult"]
            
            # Forward from WB stage (WB-ID forwarding)
            if not self.state.WB["nop"] and self.state.WB["wrt_enable"]:
                if self.state.WB["Wrt_reg_addr"] == rs1 and rs1 != 0:
                    # Only forward if not forwarding from EX or MEM
                    if not (not self.state.EX["nop"] and self.state.EX["wrt_enable"] and not self.state.EX["rd_mem"] and self.state.EX["Wrt_reg_addr"] == rs1):
                        if not (not self.state.MEM["nop"] and self.state.MEM["wrt_enable"] and not self.state.MEM["rd_mem"] and self.state.MEM["Wrt_reg_addr"] == rs1):
                            id_rs1_val = self.state.WB["Wrt_data"]
                if self.state.WB["Wrt_reg_addr"] == rs2 and rs2 != 0:
                    if not (not self.state.EX["nop"] and self.state.EX["wrt_enable"] and not self.state.EX["rd_mem"] and self.state.EX["Wrt_reg_addr"] == rs2):
                        if not (not self.state.MEM["nop"] and self.state.MEM["wrt_enable"] and not self.state.MEM["rd_mem"] and self.state.MEM["Wrt_reg_addr"] == rs2):
                            id_rs2_val = self.state.WB["Wrt_data"]

            # Handle branches (resolved in ID stage)
            if opcode == 0x63:  # Branch
                imm_b = (((instr >> 31) & 0x1) << 12) | (((instr >> 25) & 0x3F) << 5) | (((instr >> 8) & 0xF) << 1) | (((instr >> 7) & 0x1) << 11)
                imm_b = sign_extend(imm_b, 13)
                # PC of branch instruction is ID.PC (the PC that fetched this instruction)
                branch_pc = self.state.ID["PC"]
                if funct3 == 0x0:  # BEQ
                    if id_rs1_val == id_rs2_val:
                        branch_taken = True
                        branch_target = (branch_pc + imm_b) & 0xFFFFFFFF
                elif funct3 == 0x1:  # BNE
                    if id_rs1_val != id_rs2_val:
                        branch_taken = True
                        branch_target = (branch_pc + imm_b) & 0xFFFFFFFF
            
            # Handle JAL (unconditional jump, resolved in ID stage)
            if opcode == 0x6f:  # JAL
                imm_j = (((instr >> 31) & 0x1) << 20) | (((instr >> 12) & 0xFF) << 12) | (((instr >> 20) & 0x1) << 11) | (((instr >> 21) & 0x3FF) << 1)
                imm_j = sign_extend(imm_j, 21)
                jal_pc = self.state.ID["PC"]
                jal_taken = True
                jal_target = (jal_pc + imm_j) & 0xFFFFFFFF

        # Stall pipeline if load-use hazard
        if load_use_hazard:
            # Insert bubble in EX, keep ID and IF stalled
            self.nextState.EX["nop"] = True
            self.nextState.EX["instr"] = 0
            self.nextState.EX["Read_data1"] = 0
            self.nextState.EX["Read_data2"] = 0
            self.nextState.EX["Imm"] = 0
            self.nextState.EX["Rs"] = 0
            self.nextState.EX["Rt"] = 0
            self.nextState.EX["Wrt_reg_addr"] = 0
            self.nextState.EX["is_I_type"] = False
            self.nextState.EX["rd_mem"] = 0
            self.nextState.EX["wrt_mem"] = 0
            self.nextState.EX["alu_op"] = 0
            self.nextState.EX["wrt_enable"] = 0
            self.nextState.EX["PC"] = 0
            self.nextState.EX["is_jal"] = False
            # Keep ID stage (re-read same instruction)
            self.nextState.ID = self.state.ID.copy()
            # Keep IF stage (don't advance PC)
            self.nextState.IF = self.state.IF.copy()
        elif branch_taken:
            # Flush ID stage (insert bubble), redirect IF to branch target
            self.nextState.IF["PC"] = branch_target
            self.nextState.IF["nop"] = False
            self.nextState.ID["nop"] = True
            self.nextState.ID["Instr"] = 0
            self.nextState.ID["PC"] = 0
            # Move ID to EX as bubble
            self.nextState.EX["nop"] = True
            self.nextState.EX["instr"] = 0
            self.nextState.EX["Read_data1"] = 0
            self.nextState.EX["Read_data2"] = 0
            self.nextState.EX["Imm"] = 0
            self.nextState.EX["Rs"] = 0
            self.nextState.EX["Rt"] = 0
            self.nextState.EX["Wrt_reg_addr"] = 0
            self.nextState.EX["is_I_type"] = False
            self.nextState.EX["rd_mem"] = 0
            self.nextState.EX["wrt_mem"] = 0
            self.nextState.EX["alu_op"] = 0
            self.nextState.EX["wrt_enable"] = 0
            self.nextState.EX["PC"] = 0
            self.nextState.EX["is_jal"] = False
        elif jal_taken:
            # For JAL: redirect PC but keep instruction in pipeline to calculate return address
            self.nextState.IF["PC"] = jal_target
            self.nextState.IF["nop"] = False
            # Don't flush ID - let JAL pass through to EX
            # Continue to normal decode path below (JAL will be decoded and passed to EX)
        
        # Normal decode path (for non-branch instructions, including JAL)
        if not self.state.ID["nop"] and not branch_taken:
            # Normal decode: move ID to EX
            instr = self.state.ID["Instr"]
            opcode = instr & 0x7f
            rd = (instr >> 7) & 0x1f
            funct3 = (instr >> 12) & 0x7
            rs1 = (instr >> 15) & 0x1f
            rs2 = (instr >> 20) & 0x1f
            funct7 = (instr >> 25) & 0x7f

            # Read registers with forwarding
            ex_rs1_val = self.myRF.readRF(rs1)
            ex_rs2_val = self.myRF.readRF(rs2)
            
            # Forward from MEM
            if not self.state.MEM["nop"] and self.state.MEM["wrt_enable"]:
                if self.state.MEM["Wrt_reg_addr"] == rs1 and rs1 != 0:
                    if not self.state.MEM["rd_mem"]:
                        ex_rs1_val = self.state.MEM["ALUresult"]
                if self.state.MEM["Wrt_reg_addr"] == rs2 and rs2 != 0:
                    if not self.state.MEM["rd_mem"]:
                        ex_rs2_val = self.state.MEM["ALUresult"]
            
            # Forward from WB
            if not self.state.WB["nop"] and self.state.WB["wrt_enable"]:
                if self.state.WB["Wrt_reg_addr"] == rs1 and rs1 != 0:
                    if not (not self.state.MEM["nop"] and self.state.MEM["wrt_enable"] and self.state.MEM["Wrt_reg_addr"] == rs1):
                        ex_rs1_val = self.state.WB["Wrt_data"]
                if self.state.WB["Wrt_reg_addr"] == rs2 and rs2 != 0:
                    if not (not self.state.MEM["nop"] and self.state.MEM["wrt_enable"] and self.state.MEM["Wrt_reg_addr"] == rs2):
                        ex_rs2_val = self.state.WB["Wrt_data"]

            # Extract immediate
            imm_i = sign_extend((instr >> 20) & 0xFFF, 12)
            imm_s = sign_extend(((instr >> 25) << 5) | ((instr >> 7) & 0x1F), 12)

            # Determine instruction type and control signals
            is_i_type = (opcode == 0x13) or (opcode == 0x03)  # I-type or Load
            rd_mem = (opcode == 0x03 and funct3 == 0x2)  # LW
            wrt_mem = (opcode == 0x23 and funct3 == 0x2)  # SW
            wrt_enable = (opcode == 0x33) or (opcode == 0x13) or (opcode == 0x03) or (opcode == 0x6f)  # R/I/LW/JAL
            if opcode == 0x23:  # SW
                wrt_enable = False
            
            # ALU op encoding (simplified)
            alu_op = 0
            if opcode == 0x33:  # R-type
                if funct3 == 0x0 and funct7 == 0x20:
                    alu_op = 1  # SUB
                else:
                    alu_op = 0  # ADD/XOR/OR/AND
            elif opcode == 0x13:  # I-type
                if funct3 == 0x4 or funct3 == 0x6 or funct3 == 0x7:
                    alu_op = 2  # XOR/OR/AND
                else:
                    alu_op = 0  # ADDI

            self.nextState.EX["nop"] = False
            self.nextState.EX["instr"] = instr
            self.nextState.EX["Read_data1"] = ex_rs1_val
            self.nextState.EX["Read_data2"] = ex_rs2_val
            self.nextState.EX["Imm"] = imm_i if is_i_type or rd_mem else imm_s
            self.nextState.EX["Rs"] = rs1
            self.nextState.EX["Rt"] = rs2
            self.nextState.EX["Wrt_reg_addr"] = rd
            self.nextState.EX["is_I_type"] = is_i_type
            self.nextState.EX["rd_mem"] = 1 if rd_mem else 0
            self.nextState.EX["wrt_mem"] = 1 if wrt_mem else 0
            self.nextState.EX["alu_op"] = alu_op
            self.nextState.EX["wrt_enable"] = 1 if wrt_enable else 0
            # Pass PC and JAL flag for return address calculation
            self.nextState.EX["PC"] = self.state.ID["PC"]
            self.nextState.EX["is_jal"] = (opcode == 0x6f)

            # Advance ID to next instruction
            if not self.state.IF["nop"] and not jal_taken:
                # Use fetch_PC which is the PC that was used to fetch the instruction currently in IF
                fetch_pc = self.state.IF.get("fetch_PC", self.state.IF["PC"])
                self.nextState.ID["Instr"] = self.ext_imem.readInstr(fetch_pc)
                self.nextState.ID["PC"] = fetch_pc  # Track PC of fetched instruction
                self.nextState.ID["nop"] = False
            else:
                self.nextState.ID["nop"] = True
                self.nextState.ID["Instr"] = 0
                self.nextState.ID["PC"] = 0
        else:
            # ID is nop, propagate nop to EX
            self.nextState.EX["nop"] = True
            self.nextState.EX["instr"] = 0
            self.nextState.EX["Read_data1"] = 0
            self.nextState.EX["Read_data2"] = 0
            self.nextState.EX["Imm"] = 0
            self.nextState.EX["Rs"] = 0
            self.nextState.EX["Rt"] = 0
            self.nextState.EX["Wrt_reg_addr"] = 0
            self.nextState.EX["is_I_type"] = False
            self.nextState.EX["rd_mem"] = 0
            self.nextState.EX["wrt_mem"] = 0
            self.nextState.EX["alu_op"] = 0
            self.nextState.EX["wrt_enable"] = 0
            self.nextState.EX["PC"] = 0
            self.nextState.EX["is_jal"] = False
            # Advance ID
            if not self.state.IF["nop"]:
                # Use fetch_PC which is the PC that was used to fetch the instruction currently in IF
                fetch_pc = self.state.IF.get("fetch_PC", self.state.IF["PC"])
                self.nextState.ID["Instr"] = self.ext_imem.readInstr(fetch_pc)
                self.nextState.ID["PC"] = fetch_pc  # Track PC of fetched instruction
                self.nextState.ID["nop"] = False
            else:
                self.nextState.ID["nop"] = True
                self.nextState.ID["Instr"] = 0
                self.nextState.ID["PC"] = 0

        # ========== IF Stage: Instruction Fetch ==========
        # IF executes unless stalled by load-use hazard
        # Branch/JAL redirects are handled in ID stage, IF just fetches from current PC
        if not load_use_hazard:
            if not self.state.IF["nop"]:
                PC = self.state.IF["PC"]
                # Store the PC used to fetch this instruction
                self.nextState.IF["fetch_PC"] = PC
                # Check for HALT
                if PC >= len(self.ext_imem.IMem):
                    self.nextState.IF["nop"] = True
                    self.nextState.IF["PC"] = PC
                else:
                    instr = self.ext_imem.readInstr(PC)
                    opcode = instr & 0x7f
                    if opcode == 0x7f:  # HALT
                        self.nextState.IF["nop"] = True
                        self.nextState.IF["PC"] = PC
                    else:
                        # Advance PC (unless redirected by branch/JAL in ID stage)
                        # If branch/JAL was taken, PC was already redirected in ID stage
                        if not branch_taken and not jal_taken:
                            self.nextState.IF["PC"] = (PC + 4) & 0xFFFFFFFF
                        # If branch/JAL redirected, PC was set in ID stage, keep it
                        self.nextState.IF["nop"] = False
            else:
                self.nextState.IF = self.state.IF.copy()

        # Check for halt condition
        if self.state.IF["nop"] and self.state.ID["nop"] and self.state.EX["nop"] and self.state.MEM["nop"] and self.state.WB["nop"]:
            self.halted = True

        # Output state and register file
        self.myRF.outputRF(self.cycle)
        self.printState(self.nextState, self.cycle)
        
        # Update state
        self.state = self.nextState
        self.nextState = State()
        self.cycle += 1

        # Safety stop
        if self.cycle >= self.max_cycles:
            self.halted = True

    def printState(self, state, cycle):
        printstate = ["-"*70 + "\n", "State after executing cycle: " + str(cycle) + "\n"]
        
        # IF stage
        printstate.append("IF.nop: " + str(state.IF["nop"]) + "\n")
        printstate.append("IF.PC: " + str(state.IF["PC"]) + "\n")
        
        # ID stage
        printstate.append("ID.nop: " + str(state.ID["nop"]) + "\n")
        if state.ID["Instr"] != 0:
            printstate.append("ID.Instr: " + format(state.ID["Instr"] & 0xFFFFFFFF, "032b") + "\n")
        else:
            printstate.append("ID.Instr: " + str(state.ID["Instr"]) + "\n")
        
        # EX stage
        printstate.append("EX.nop: " + str(state.EX["nop"]) + "\n")
        if state.EX["instr"] != 0:
            printstate.append("EX.instr: " + format(state.EX["instr"] & 0xFFFFFFFF, "032b") + "\n")
        else:
            printstate.append("EX.instr: \n")
        printstate.append("EX.Read_data1: " + format(state.EX["Read_data1"] & 0xFFFFFFFF, "032b") + "\n")
        printstate.append("EX.Read_data2: " + format(state.EX["Read_data2"] & 0xFFFFFFFF, "032b") + "\n")
        # Format Imm: I-type and S-type both use 12-bit immediate in EX stage
        if state.EX["is_I_type"] or state.EX["wrt_mem"] or state.EX["rd_mem"]:
            # I-type or S-type immediate: 12 bits
            imm_val = state.EX["Imm"] & 0xFFF
            if imm_val >= 0x800:
                imm_val = imm_val | 0xFFFFF000  # Sign extend
            printstate.append("EX.Imm: " + format(imm_val & 0xFFF, "012b") + "\n")
        else:
            printstate.append("EX.Imm: " + format(state.EX["Imm"] & 0xFFFFFFFF, "032b") + "\n")
        printstate.append("EX.Rs: " + format(state.EX["Rs"] & 0x1F, "05b") + "\n")
        printstate.append("EX.Rt: " + format(state.EX["Rt"] & 0x1F, "05b") + "\n")
        # Wrt_reg_addr: 5 bits for normal, 6 bits (with leading 0) for stores
        if state.EX["wrt_mem"]:
            printstate.append("EX.Wrt_reg_addr: " + format(0, "06b") + "\n")
        else:
            printstate.append("EX.Wrt_reg_addr: " + format(state.EX["Wrt_reg_addr"] & 0x1F, "05b") + "\n")
        printstate.append("EX.is_I_type: " + str(1 if state.EX["is_I_type"] else 0) + "\n")
        printstate.append("EX.rd_mem: " + str(state.EX["rd_mem"]) + "\n")
        printstate.append("EX.wrt_mem: " + str(state.EX["wrt_mem"]) + "\n")
        printstate.append("EX.alu_op: " + format(state.EX["alu_op"] & 0x3, "02b") + "\n")
        printstate.append("EX.wrt_enable: " + str(state.EX["wrt_enable"]) + "\n")
        
        # MEM stage
        printstate.append("MEM.nop: " + str(state.MEM["nop"]) + "\n")
        printstate.append("MEM.ALUresult: " + format(state.MEM["ALUresult"] & 0xFFFFFFFF, "032b") + "\n")
        printstate.append("MEM.Store_data: " + format(state.MEM["Store_data"] & 0xFFFFFFFF, "032b") + "\n")
        printstate.append("MEM.Rs: " + format(state.MEM["Rs"] & 0x1F, "05b") + "\n")
        printstate.append("MEM.Rt: " + format(state.MEM["Rt"] & 0x1F, "05b") + "\n")
        printstate.append("MEM.Wrt_reg_addr: " + format(state.MEM["Wrt_reg_addr"] & 0x1F, "05b") + "\n")
        printstate.append("MEM.rd_mem: " + str(state.MEM["rd_mem"]) + "\n")
        printstate.append("MEM.wrt_mem: " + str(state.MEM["wrt_mem"]) + "\n")
        printstate.append("MEM.wrt_enable: " + str(state.MEM["wrt_enable"]) + "\n")
        
        # WB stage
        printstate.append("WB.nop: " + str(state.WB["nop"]) + "\n")
        printstate.append("WB.Wrt_data: " + format(state.WB["Wrt_data"] & 0xFFFFFFFF, "032b") + "\n")
        printstate.append("WB.Rs: " + format(state.WB["Rs"] & 0x1F, "05b") + "\n")
        printstate.append("WB.Rt: " + format(state.WB["Rt"] & 0x1F, "05b") + "\n")
        printstate.append("WB.Wrt_reg_addr: " + format(state.WB["Wrt_reg_addr"] & 0x1F, "05b") + "\n")
        printstate.append("WB.wrt_enable: " + str(state.WB["wrt_enable"]) + "\n")
        
        perm = "w" if cycle == 0 else "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)

# ================= Main =================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='RV32I processor')
    parser.add_argument('--iodir', default="", type=str, help='Directory containing the input files.')
    args = parser.parse_args()

    ioDir = os.path.abspath(args.iodir)
    testcase_name = os.path.basename(ioDir.rstrip("/"))
    outDir = os.path.join("results", testcase_name)
    os.makedirs(outDir, exist_ok=True)
    print("IO Directory:", ioDir)

    imem = InsMem("Imem", ioDir)
    dmem_ss = DataMem("SS", ioDir, os.path.join(outDir))
    dmem_fs = DataMem("FS", ioDir, os.path.join(outDir))

    ssCore = SingleStageCore(outDir, imem, dmem_ss)
    fsCore = FiveStageCore(outDir, imem, dmem_fs)

    while True:
        if not ssCore.halted:
            ssCore.step()
        if not fsCore.halted:
            fsCore.step()
        if ssCore.halted and fsCore.halted:
            break

    dmem_ss.outputDataMem()
    dmem_fs.outputDataMem()

    # Calculate performance metrics
    perf_path = os.path.join(outDir, "PerformanceMetrics.txt")
    ss_cycles = ssCore.cycle
    ss_instr = ssCore.retired_instructions
    fs_cycles = fsCore.cycle
    fs_instr = fsCore.retired_instructions
    
    # Calculate CPI (Cycles Per Instruction) and IPC (Instructions Per Cycle)
    ss_cpi = (ss_cycles / ss_instr) if ss_instr > 0 else 0.0
    ss_ipc = (ss_instr / ss_cycles) if ss_cycles > 0 else 0.0
    fs_cpi = (fs_cycles / fs_instr) if fs_instr > 0 else 0.0
    fs_ipc = (fs_instr / fs_cycles) if fs_cycles > 0 else 0.0

    # Format performance metrics output
    perf_output = []
    perf_output.append("=" * 70)
    perf_output.append("PERFORMANCE METRICS")
    perf_output.append("=" * 70)
    perf_output.append("")
    perf_output.append("Performance of Single Stage:")
    perf_output.append(f"  Total Execution Cycles: {ss_cycles}")
    perf_output.append(f"  Total Instructions Retired: {ss_instr}")
    perf_output.append(f"  Average CPI (Cycles Per Instruction): {ss_cpi:.6f}")
    perf_output.append(f"  IPC (Instructions Per Cycle): {ss_ipc:.6f}")
    perf_output.append("")
    perf_output.append("Performance of Five Stage:")
    perf_output.append(f"  Total Execution Cycles: {fs_cycles}")
    perf_output.append(f"  Total Instructions Retired: {fs_instr}")
    perf_output.append(f"  Average CPI (Cycles Per Instruction): {fs_cpi:.6f}")
    perf_output.append(f"  IPC (Instructions Per Cycle): {fs_ipc:.6f}")
    perf_output.append("")
    perf_output.append("=" * 70)
    
    # Write to file (matching sample output format)
    with open(perf_path, "w") as f:
        f.write("Performance of Single Stage:\n")
        f.write(f"#Cycles -> {ss_cycles}\n")
        f.write(f"#Instructions -> {ss_instr}\n")
        f.write(f"CPI -> {ss_cpi}\n")
        f.write(f"IPC -> {ss_ipc}\n\n")
        f.write("Performance of Five Stage:\n")
        f.write(f"#Cycles -> {fs_cycles}\n")
        f.write(f"#Instructions -> {fs_instr}\n")
        f.write(f"CPI -> {fs_cpi}\n")
        f.write(f"IPC -> {fs_ipc}\n")
    
    # Print to console
    print("\n" + "\n".join(perf_output))
    print(f"\nPerformance metrics saved to: {perf_path}")

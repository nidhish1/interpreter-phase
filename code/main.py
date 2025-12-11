import os
import argparse

"""
RV32I mini-simulator: instruction memory, data memory, register files,
and two cores (single-stage functional, five-stage skeleton).
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
        if all(ch in "01" for ch in s) and len(s) == 8:
            return int(s, 2) & 0xFF
        s = s.lower()
        if s.startswith("0x"):
            s = s[2:]
        return int(s, 16) & 0xFF

    def readInstr(self, ReadAddress):
        # Big-Endian read
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
        while len(self.DMem) < MemSize:
            self.DMem.append("00000000")

    def _byte_to_int(self, s):
        if s is None or s == "":
            return 0
        s = s.strip()
        if all(ch in "01" for ch in s) and len(s) == 8:
            return int(s, 2) & 0xFF
        s = s.lower()
        if s.startswith("0x"):
            s = s[2:]
        return int(s, 16) & 0xFF

    def readInstr(self, ReadAddress):
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
        wd = WriteData & 0xFFFFFFFF
        # Write in little-endian format (LSB at lowest address)
        bytes_le = [wd & 0xFF, (wd >> 8) & 0xFF, (wd >> 16) & 0xFF, (wd >> 24) & 0xFF]
        for i in range(4):
            idx = Address + i
            if idx < 0:
                continue
            while idx >= len(self.DMem):
                self.DMem.append("00000000")
            self.DMem[idx] = format(bytes_le[i], "08b")

    def outputDataMem(self):
        os.makedirs(self.output_dir, exist_ok=True)
        resPath = os.path.join(self.output_dir, f"{self.id}_DMEMResult.txt")
        with open(resPath, "w") as rp:
            rp.writelines([str(data) + "\n" for data in self.DMem])

# ================= Register File =================
class RegisterFile(object):
    def __init__(self, ioDir, name):
        os.makedirs(ioDir, exist_ok=True)
        self.outputFile = os.path.join(ioDir, f"{name}_RFResult.txt")
        self.Registers = [0x0 for _ in range(32)]
        self.name = name

    def readRF(self, Reg_addr):
        if Reg_addr < 0 or Reg_addr >= 32:
            return 0
        return self.Registers[Reg_addr] & 0xFFFFFFFF

    def writeRF(self, Reg_addr, Wrt_reg_data):
        if Reg_addr == 0:
            return
        if Reg_addr < 0 or Reg_addr >= 32:
            return
        self.Registers[Reg_addr] = Wrt_reg_data & 0xFFFFFFFF

    def outputRF(self, cycle):
        op = []
        if self.name == "FS":
            op.append("-"*70 + "\n")
            op.append("State of RF after executing cycle:" + str(cycle) + "\n")
        else:
            op.append("State of RF after executing cycle:  " + str(cycle) + "\n")
        op.extend([format(val & 0xFFFFFFFF, "032b") + "\n" for val in self.Registers])
        perm = "w" if cycle == 0 else "a"
        with open(self.outputFile, perm) as file:
            file.writelines(op)

# ================= State =================
class State(object):
    def __init__(self):
        self.IF = {"nop": False, "PC": 0}
        self.ID = {"nop": True, "Instr": 0, "PC": 0}
        self.EX = {"nop": True, "instr": 0, "Read_data1": 0, "Read_data2": 0, "Imm": 0,
                   "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "is_I_type": False, "rd_mem": 0,
                   "wrt_mem": 0, "alu_op": 0, "wrt_enable": 0, "PC": 0, "is_jal": False}
        self.MEM = {"nop": True, "ALUresult": 0, "Store_data": 0, "Rs": 0, "Rt": 0,
                    "Wrt_reg_addr": 0, "rd_mem": 0, "wrt_mem": 0, "wrt_enable": 0}
        self.WB = {"nop": True, "Wrt_data": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "wrt_enable": 0}

        # Explicit pipeline registers for the five-stage core
        self.IF_ID = {"nop": True, "PC": 0, "Instr": 0}
        self.ID_EX = {"nop": True, "instr": 0, "PC": 0, "Read_data1": 0, "Read_data2": 0, "Imm": 0,
                      "rs1": 0, "rs2": 0, "rd": 0, "opcode": 0, "funct3": 0, "funct7": 0,
                      "MemRead": 0, "MemWrite": 0, "RegWrite": 0, "MemtoReg": 0,
                      "ALUSrc": 0, "ALUOp": 0, "isJAL": 0, "is_halt": 0}
        self.EX_MEM = {"nop": True, "PC": 0, "ALUResult": 0, "WriteData": 0, "rd": 0, "rs1": 0, "rs2": 0,
                       "MemRead": 0, "MemWrite": 0, "RegWrite": 0, "MemtoReg": 0, "isJAL": 0, "is_halt": 0}
        self.MEM_WB = {"nop": True, "ALUResult": 0, "ReadData": 0, "WriteData": 0, "rd": 0, "rs1": 0, "rs2": 0,
                       "RegWrite": 0, "MemtoReg": 0, "isJAL": 0, "is_halt": 0}

    def copy(self, target):
        # Shallow copy for stalling logic
        return target.copy()

# ================= Core =================
class Core(object):
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
        self.max_cycles = 10000

def sign_extend(value, bits):
    mask = (1 << bits) - 1
    value_masked = value & mask
    sign_bit = 1 << (bits - 1)
    if value_masked & sign_bit:
        return value_masked - (1 << bits)
    else:
        return value_masked

# ================= Single Stage Core =================
class SingleStageCore(Core):
    def __init__(self, ioDir, imem, dmem):
        super(SingleStageCore, self).__init__(ioDir, imem, dmem)
        self.myRF = RegisterFile(ioDir, "SS")
        self.opFilePath = os.path.join(ioDir, "StateResult_SS.txt")

    def step(self):
        PC = self.state.IF["PC"]
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

        if opcode == 0x7f: # HALT
            self.retired_instructions += 1
            self.nextState.IF["nop"] = True
            self.nextState.IF["PC"] = PC
            self.halted = True
            self.myRF.outputRF(self.cycle)
            self.printState(self.nextState, self.cycle)
            self.state = self.nextState
            self.cycle += 1
            self.myRF.outputRF(self.cycle)
            self.printState(self.nextState, self.cycle)
            self.cycle += 1
            return

        nextPC = (PC + 4) & 0xFFFFFFFF
        rs1_val = self.myRF.readRF(rs1)
        rs2_val = self.myRF.readRF(rs2)
        imm_i = sign_extend((instr >> 20) & 0xFFF, 12)
        imm_s = sign_extend(((instr >> 25) << 5) | ((instr >> 7) & 0x1F), 12)
        imm_b = sign_extend((((instr >> 31) & 0x1) << 12) | (((instr >> 25) & 0x3F) << 5) | (((instr >> 8) & 0xF) << 1) | (((instr >> 7) & 0x1) << 11), 13)
        imm_j = sign_extend((((instr >> 31) & 0x1) << 20) | (((instr >> 12) & 0xFF) << 12) | (((instr >> 20) & 0x1) << 11) | (((instr >> 21) & 0x3FF) << 1), 21)

        write_back_enable = False
        write_back_data = 0

        if opcode == 0x33: # R-type
            if funct3 == 0x0 and funct7 == 0x00: write_back_data = (rs1_val + rs2_val)
            elif funct3 == 0x0 and funct7 == 0x20: write_back_data = (rs1_val - rs2_val)
            elif funct3 == 0x4: write_back_data = (rs1_val ^ rs2_val)
            elif funct3 == 0x6: write_back_data = (rs1_val | rs2_val)
            elif funct3 == 0x7: write_back_data = (rs1_val & rs2_val)
            write_back_enable = True
        elif opcode == 0x13: # I-type
            if funct3 == 0x0: write_back_data = (rs1_val + imm_i)
            elif funct3 == 0x4: write_back_data = (rs1_val ^ (imm_i & 0xFFFFFFFF))
            elif funct3 == 0x6: write_back_data = (rs1_val | (imm_i & 0xFFFFFFFF))
            elif funct3 == 0x7: write_back_data = (rs1_val & (imm_i & 0xFFFFFFFF))
            write_back_enable = True
        elif opcode == 0x03 and funct3 == 0x2: # LW
            addr = (rs1_val + imm_i) & 0xFFFFFFFF
            write_back_data = self.ext_dmem.readInstr(addr)
            write_back_enable = True
        elif opcode == 0x23 and funct3 == 0x2: # SW
            addr = (rs1_val + imm_s) & 0xFFFFFFFF
            self.ext_dmem.writeDataMem(addr, rs2_val)
        elif opcode == 0x63: # BEQ/BNE
            if (funct3 == 0x0 and rs1_val == rs2_val) or (funct3 == 0x1 and rs1_val != rs2_val):
                nextPC = (PC + imm_b) & 0xFFFFFFFF
        elif opcode == 0x6f: # JAL
            write_back_data = (PC + 4) & 0xFFFFFFFF
            write_back_enable = True
            nextPC = (PC + imm_j) & 0xFFFFFFFF

        if write_back_enable and rd != 0:
            self.myRF.writeRF(rd, write_back_data & 0xFFFFFFFF)

        self.nextState.IF["PC"] = nextPC
        self.nextState.IF["nop"] = False
        self.retired_instructions += 1
        self.myRF.outputRF(self.cycle)
        self.printState(self.nextState, self.cycle)
        self.state = self.nextState
        self.nextState = State()
        self.cycle += 1
        if self.cycle >= self.max_cycles: self.halted = True

    def printState(self, state, cycle):
        printstate = ["-"*70 + "\n", "State after executing cycle: " + str(cycle) + "\n"]
        printstate.append("IF.PC: " + str(state.IF["PC"]) + "\n")
        printstate.append("IF.nop: " + str(state.IF["nop"]) + "\n")
        perm = "w" if cycle == 0 else "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)

# ================= Five Stage Core =================
class FiveStageCore(Core):
    def __init__(self, ioDir, imem, dmem):
        super(FiveStageCore, self).__init__(ioDir, imem, dmem)
        self.myRF = RegisterFile(ioDir, "FS")
        self.opFilePath = os.path.join(ioDir, "StateResult_FS.txt")
        self.state.IF["PC"] = 0
        self.state.IF["nop"] = False
        self.state.IF_ID["nop"] = True
        self.state.ID_EX["nop"] = True
        self.state.EX_MEM["nop"] = True
        self.state.MEM_WB["nop"] = True
        self.redirect = False
        self.redirect_pc = 0
        self.stall = False

    def step(self):
        # Per-cycle control flags
        self.redirect = False
        self.redirect_pc = 0
        self.stall = False

        # 1. WB Stage
        self.WB_stage()
        # 2. MEM Stage
        self.MEM_stage()
        # 3. EX Stage
        self.EX_stage()
        # 4. ID Stage
        self.ID_stage()
        # 5. IF Stage
        self.IF_stage()

        self.myRF.outputRF(self.cycle)
        self.printState(self.nextState, self.cycle)
        
        # Check HALT using nextState (after all stages have updated it)
        if (self.nextState.IF["nop"] and self.nextState.IF_ID["nop"] and self.nextState.ID_EX["nop"] and
            self.nextState.EX_MEM["nop"] and self.nextState.MEM_WB["nop"]):
            self.halted = True
        
        self.state = self.nextState
        self.nextState = State()
        self.cycle += 1
        if self.cycle >= self.max_cycles:
            self.halted = True

    def WB_stage(self):
        if self.state.MEM_WB["nop"]:
            return
        # Write to register file if needed
        if self.state.MEM_WB["RegWrite"] and self.state.MEM_WB["rd"] != 0:
            self.myRF.writeRF(self.state.MEM_WB["rd"], self.state.MEM_WB["WriteData"] & 0xFFFFFFFF)
        # Count all instructions that reach WB (including stores, branches, etc.)
            self.retired_instructions += 1

    def MEM_stage(self):
        if self.state.EX_MEM["nop"]:
            self.nextState.MEM_WB["nop"] = True
            return

        read_data = 0
        if self.state.EX_MEM["MemRead"]:
            read_data = self.ext_dmem.readInstr(self.state.EX_MEM["ALUResult"]) & 0xFFFFFFFF
        if self.state.EX_MEM["MemWrite"]:
            self.ext_dmem.writeDataMem(self.state.EX_MEM["ALUResult"], self.state.EX_MEM["WriteData"])

        write_data = read_data if self.state.EX_MEM["MemtoReg"] else (self.state.EX_MEM["ALUResult"] & 0xFFFFFFFF)

        self.nextState.MEM_WB["nop"] = False
        self.nextState.MEM_WB["ALUResult"] = self.state.EX_MEM["ALUResult"] & 0xFFFFFFFF
        self.nextState.MEM_WB["ReadData"] = read_data
        self.nextState.MEM_WB["WriteData"] = write_data
        self.nextState.MEM_WB["rd"] = self.state.EX_MEM["rd"]
        self.nextState.MEM_WB["rs1"] = self.state.EX_MEM["rs1"]
        self.nextState.MEM_WB["rs2"] = self.state.EX_MEM["rs2"]
        self.nextState.MEM_WB["RegWrite"] = self.state.EX_MEM["RegWrite"]
        self.nextState.MEM_WB["MemtoReg"] = self.state.EX_MEM["MemtoReg"]
        self.nextState.MEM_WB["isJAL"] = self.state.EX_MEM["isJAL"]
        self.nextState.MEM_WB["is_halt"] = self.state.EX_MEM.get("is_halt", 0)

    def _forward_operand(self, reg_num, default_val):
        val = default_val
        if reg_num == 0:
            return val
        # Forward from EX/MEM (ALU result) - highest priority if not a load
        # EX_MEM contains instruction that was in EX stage in previous cycle, now in MEM stage
        # Check if that instruction writes to the register we need
        forwarded_from_mem = False
        if (not self.state.EX_MEM["nop"] and self.state.EX_MEM["RegWrite"] and
                self.state.EX_MEM["rd"] == reg_num):
            # Can forward ALU result if not a load (loads need to wait for memory read)
            if not self.state.EX_MEM["MemRead"]:
                val = self.state.EX_MEM["ALUResult"] & 0xFFFFFFFF
                forwarded_from_mem = True
            # If it's a load, we can't forward yet (load-use hazard should have stalled)
        # Forward from MEM/WB - only if EX/MEM didn't forward (lower priority)
        if not forwarded_from_mem:
            if (not self.state.MEM_WB["nop"] and self.state.MEM_WB["RegWrite"] and
                    self.state.MEM_WB["rd"] == reg_num):
                val = self.state.MEM_WB["WriteData"] & 0xFFFFFFFF
        return val

    def EX_stage(self):
        if self.state.ID_EX["nop"]:
            self.nextState.EX_MEM["nop"] = True
            return

        op1 = self._forward_operand(self.state.ID_EX["rs1"], self.state.ID_EX["Read_data1"]) & 0xFFFFFFFF
        op2_reg = self._forward_operand(self.state.ID_EX["rs2"], self.state.ID_EX["Read_data2"]) & 0xFFFFFFFF
        imm_val = self.state.ID_EX["Imm"] & 0xFFFFFFFF
        # For I-type, loads, and stores we must use the immediate; R-type uses register
        if self.state.ID_EX["opcode"] in (0x13, 0x03, 0x23):
            op2 = imm_val
        else:
            op2 = op2_reg

        alu_res = 0
        opcode = self.state.ID_EX["opcode"]
        funct3 = self.state.ID_EX["funct3"]
        funct7 = self.state.ID_EX["funct7"]

        if opcode == 0x33:  # R-type
            if funct3 == 0x0:
                alu_res = (op1 + op2_reg) & 0xFFFFFFFF if funct7 == 0x00 else (op1 - op2_reg) & 0xFFFFFFFF
            elif funct3 == 0x4:
                alu_res = (op1 ^ op2_reg) & 0xFFFFFFFF
            elif funct3 == 0x6:
                alu_res = (op1 | op2_reg) & 0xFFFFFFFF
            elif funct3 == 0x7:
                alu_res = (op1 & op2_reg) & 0xFFFFFFFF
        elif opcode in (0x13, 0x03, 0x23):  # I-type, load, store
            if opcode == 0x23:  # Store - always use ADD for address calculation
                alu_res = (op1 + op2) & 0xFFFFFFFF
            elif funct3 == 0x0:
                alu_res = (op1 + op2) & 0xFFFFFFFF
            elif funct3 == 0x4:
                alu_res = (op1 ^ op2) & 0xFFFFFFFF
            elif funct3 == 0x6:
                alu_res = (op1 | op2) & 0xFFFFFFFF
            elif funct3 == 0x7:
                alu_res = (op1 & op2) & 0xFFFFFFFF
        elif opcode == 0x6F:  # JAL
            alu_res = (self.state.ID_EX["PC"] + 4) & 0xFFFFFFFF

        self.nextState.EX_MEM["nop"] = False
        self.nextState.EX_MEM["PC"] = self.state.ID_EX["PC"]
        self.nextState.EX_MEM["ALUResult"] = alu_res
        self.nextState.EX_MEM["WriteData"] = op2_reg
        self.nextState.EX_MEM["rd"] = self.state.ID_EX["rd"]
        self.nextState.EX_MEM["rs1"] = self.state.ID_EX["rs1"]
        self.nextState.EX_MEM["rs2"] = self.state.ID_EX["rs2"]
        self.nextState.EX_MEM["MemRead"] = self.state.ID_EX["MemRead"]
        self.nextState.EX_MEM["MemWrite"] = self.state.ID_EX["MemWrite"]
        self.nextState.EX_MEM["RegWrite"] = self.state.ID_EX["RegWrite"]
        self.nextState.EX_MEM["MemtoReg"] = self.state.ID_EX["MemtoReg"]
        self.nextState.EX_MEM["isJAL"] = self.state.ID_EX["isJAL"]
        self.nextState.EX_MEM["is_halt"] = self.state.ID_EX.get("is_halt", 0)

    def ID_stage(self):
        # Default bubble
        self.nextState.ID_EX["nop"] = True
        self.nextState.ID_EX["RegWrite"] = 0

        if self.state.IF_ID["nop"]:
            return

        instr = self.state.IF_ID["Instr"]
        pc = self.state.IF_ID["PC"]
        opcode = instr & 0x7f
        rd = (instr >> 7) & 0x1f
        funct3 = (instr >> 12) & 0x7
        rs1 = (instr >> 15) & 0x1f
        rs2 = (instr >> 20) & 0x1f
        funct7 = (instr >> 25) & 0x7f

        # Load-use hazard detection (load currently in EX)
        if (not self.state.ID_EX["nop"] and self.state.ID_EX["MemRead"] and self.state.ID_EX["rd"] != 0 and
                (self.state.ID_EX["rd"] == rs1 or self.state.ID_EX["rd"] == rs2)):
            self.stall = True
            self.nextState.ID_EX["nop"] = True
            self.nextState.IF_ID = self.state.IF_ID.copy()
            self.nextState.IF = self.state.IF.copy()
            return

        is_halt = (opcode == 0x7f)
        # Register reads with simple forwarding for branch decisions
        val1 = self.myRF.readRF(rs1)
        val2 = self.myRF.readRF(rs2)
        val1 = self._forward_operand(rs1, val1)
        val2 = self._forward_operand(rs2, val2)
        
        imm_i = sign_extend((instr >> 20) & 0xFFF, 12)
        imm_s = sign_extend(((instr >> 25) << 5) | ((instr >> 7) & 0x1F), 12)
        imm_b = sign_extend((((instr >> 31) & 0x1) << 12) | (((instr >> 25) & 0x3F) << 5) |
                            (((instr >> 8) & 0xF) << 1) | (((instr >> 7) & 0x1) << 11), 13)
        imm_j = sign_extend((((instr >> 31) & 0x1) << 20) | (((instr >> 12) & 0xFF) << 12) |
                            (((instr >> 20) & 0x1) << 11) | (((instr >> 21) & 0x3FF) << 1), 21)

        MemRead = 1 if opcode == 0x03 else 0
        MemWrite = 1 if opcode == 0x23 else 0
        RegWrite = 0 if is_halt else (1 if opcode in (0x33, 0x13, 0x03, 0x6F) else 0)
        MemtoReg = 1 if opcode == 0x03 else 0
        ALUSrc = 1 if opcode in (0x13, 0x03, 0x23) else 0
        isJAL = 1 if opcode == 0x6F else 0

        # Branch/JAL resolution
        branch_taken = False
        target_pc = 0
        if opcode == 0x63:
            if (funct3 == 0x0 and val1 == val2) or (funct3 == 0x1 and val1 != val2):
                branch_taken = True
                target_pc = (pc + imm_b) & 0xFFFFFFFF
            RegWrite = 0  # branches do not write back
        if isJAL:
            branch_taken = True
            target_pc = (pc + imm_j) & 0xFFFFFFFF

        # Fill ID/EX pipeline register
        self.nextState.ID_EX["nop"] = False
        self.nextState.ID_EX["instr"] = instr
        self.nextState.ID_EX["PC"] = pc
        self.nextState.ID_EX["Read_data1"] = val1 & 0xFFFFFFFF
        self.nextState.ID_EX["Read_data2"] = val2 & 0xFFFFFFFF
        # Select immediate based on instruction type
        if opcode in (0x13, 0x03):  # I-type or load
            imm_to_use = imm_i
        elif opcode == 0x23:  # Store
            imm_to_use = imm_s
        else:  # R-type, branch, etc. - imm not used but set to 0
            imm_to_use = 0
        # Store as 32-bit value (sign-extended immediate)
        self.nextState.ID_EX["Imm"] = imm_to_use & 0xFFFFFFFF
        self.nextState.ID_EX["rs1"] = rs1
        self.nextState.ID_EX["rs2"] = rs2
        self.nextState.ID_EX["rd"] = rd
        self.nextState.ID_EX["opcode"] = opcode
        self.nextState.ID_EX["funct3"] = funct3
        self.nextState.ID_EX["funct7"] = funct7
        self.nextState.ID_EX["MemRead"] = MemRead
        self.nextState.ID_EX["MemWrite"] = MemWrite
        self.nextState.ID_EX["RegWrite"] = RegWrite
        self.nextState.ID_EX["MemtoReg"] = MemtoReg
        self.nextState.ID_EX["ALUSrc"] = ALUSrc
        self.nextState.ID_EX["ALUOp"] = 0
        self.nextState.ID_EX["isJAL"] = isJAL
        # Mark halt so we can stop fetching later
        self.nextState.ID_EX["is_halt"] = 1 if is_halt else 0

        if opcode == 0x33 and funct3 == 0x0 and funct7 == 0x20:
            self.nextState.ID_EX["ALUOp"] = 1  # SUB
        elif opcode == 0x13 and funct3 in (0x4, 0x6, 0x7):
            self.nextState.ID_EX["ALUOp"] = 2  # Logic immediates

        # Redirect PC on branch/jump
        if branch_taken:
            self.redirect = True
            self.redirect_pc = target_pc

    def IF_stage(self):
        if self.stall:
            # Hold IF/ID and PC
            self.nextState.IF["PC"] = self.state.IF["PC"]
            self.nextState.IF["nop"] = self.state.IF["nop"]
            return

        fetch_pc = self.redirect_pc if self.redirect else self.state.IF["PC"]

        if self.state.IF["nop"] and not self.redirect:
            self.nextState.IF["nop"] = True
            return

        if fetch_pc >= len(self.ext_imem.IMem):
            self.nextState.IF["nop"] = True
            self.nextState.IF["PC"] = fetch_pc
            self.nextState.IF_ID["nop"] = True
            return

        instr = self.ext_imem.readInstr(fetch_pc)
        opcode = instr & 0x7f

        if opcode == 0x7f:  # HALT
            # Inject HALT into pipeline and stop fetching further
            self.nextState.IF_ID["nop"] = False
            self.nextState.IF_ID["Instr"] = instr
            self.nextState.IF_ID["PC"] = fetch_pc
            self.nextState.IF["PC"] = fetch_pc  # hold PC
            self.nextState.IF["nop"] = True    # stop further fetches
        else:
            self.nextState.IF_ID["nop"] = False
            self.nextState.IF_ID["Instr"] = instr
            self.nextState.IF_ID["PC"] = fetch_pc
            self.nextState.IF["PC"] = (fetch_pc + 4) & 0xFFFFFFFF
                     self.nextState.IF["nop"] = False

            if self.redirect:
                # We fetched from the target; ensure the wrong-path fetch is dropped.
                pass

    def printState(self, state, cycle):
        printstate = ["-"*70 + "\n", "State after executing cycle: " + str(cycle) + "\n"]
        printstate.append("IF.nop: " + str(state.IF["nop"]) + "\n")
        printstate.append("IF.PC: " + str(state.IF["PC"]) + "\n")
        
        printstate.append("ID.nop: " + str(state.IF_ID["nop"]) + "\n")
        id_instr = state.IF_ID["Instr"]
        id_instr_str = format(id_instr & 0xFFFFFFFF, "032b") if not state.IF_ID["nop"] else ""
        printstate.append("ID.Instr: " + id_instr_str + "\n")

        printstate.append("EX.nop: " + str(state.ID_EX["nop"]) + "\n")
        ex_instr = state.ID_EX["instr"]
        ex_instr_str = format(ex_instr & 0xFFFFFFFF, "032b") if not state.ID_EX["nop"] else ""
        printstate.append("EX.instr: " + ex_instr_str + "\n")
        printstate.append("EX.Read_data1: " + format(state.ID_EX["Read_data1"] & 0xFFFFFFFF, "032b") + "\n")
        printstate.append("EX.Read_data2: " + format(state.ID_EX["Read_data2"] & 0xFFFFFFFF, "032b") + "\n")
        # Format immediate: 32-bit when nop, 12-bit when instruction
        if state.ID_EX["nop"]:
            printstate.append("EX.Imm: " + format(state.ID_EX["Imm"] & 0xFFFFFFFF, "032b") + "\n")
        else:
            imm_val = state.ID_EX["Imm"] & 0xFFFFFFFF
            imm_12bit = imm_val & 0xFFF
            printstate.append("EX.Imm: " + format(imm_12bit, "012b") + "\n")
        printstate.append("EX.Rs: " + format(state.ID_EX["rs1"] & 0x1F, "05b") + "\n")
        printstate.append("EX.Rt: " + format(state.ID_EX["rs2"] & 0x1F, "05b") + "\n")
        printstate.append("EX.Wrt_reg_addr: " + format(state.ID_EX["rd"] & 0x1F, "05b") + "\n")
        printstate.append("EX.is_I_type: " + str(1 if state.ID_EX["ALUSrc"] else 0) + "\n")
        printstate.append("EX.rd_mem: " + str(state.ID_EX["MemRead"]) + "\n")
        printstate.append("EX.wrt_mem: " + str(state.ID_EX["MemWrite"]) + "\n")
        printstate.append("EX.alu_op: " + format(state.ID_EX["ALUOp"] & 0x3, "02b") + "\n")
        printstate.append("EX.wrt_enable: " + str(state.ID_EX["RegWrite"]) + "\n")

        printstate.append("MEM.nop: " + str(state.EX_MEM["nop"]) + "\n")
        printstate.append("MEM.ALUresult: " + format(state.EX_MEM["ALUResult"] & 0xFFFFFFFF, "032b") + "\n")
        printstate.append("MEM.Store_data: " + format(state.EX_MEM["WriteData"] & 0xFFFFFFFF, "032b") + "\n")
        printstate.append("MEM.Rs: " + format(state.EX_MEM["rs1"] & 0x1F, "05b") + "\n")
        printstate.append("MEM.Rt: " + format(state.EX_MEM["rs2"] & 0x1F, "05b") + "\n")
        printstate.append("MEM.Wrt_reg_addr: " + format(state.EX_MEM["rd"] & 0x1F, "05b") + "\n")
        printstate.append("MEM.rd_mem: " + str(state.EX_MEM["MemRead"]) + "\n")
        printstate.append("MEM.wrt_mem: " + str(state.EX_MEM["MemWrite"]) + "\n")
        printstate.append("MEM.wrt_enable: " + str(state.EX_MEM["RegWrite"]) + "\n")

        printstate.append("WB.nop: " + str(state.MEM_WB["nop"]) + "\n")
        printstate.append("WB.Wrt_data: " + format(state.MEM_WB["WriteData"] & 0xFFFFFFFF, "032b") + "\n")
        printstate.append("WB.Rs: " + format(state.MEM_WB["rs1"] & 0x1F, "05b") + "\n")
        printstate.append("WB.Rt: " + format(state.MEM_WB["rs2"] & 0x1F, "05b") + "\n")
        printstate.append("WB.Wrt_reg_addr: " + format(state.MEM_WB["rd"] & 0x1F, "05b") + "\n")
        printstate.append("WB.wrt_enable: " + str(state.MEM_WB["RegWrite"]) + "\n")
        
        perm = "w" if cycle == 0 else "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)

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

    perf_path = os.path.join(outDir, "PerformanceMetrics.txt")
    ss_cycles = ssCore.cycle
    ss_instr = ssCore.retired_instructions
    fs_cycles = fsCore.cycle
    fs_instr = fsCore.retired_instructions
    
    ss_cpi = (ss_cycles / ss_instr) if ss_instr > 0 else 0.0
    ss_ipc = (ss_instr / ss_cycles) if ss_cycles > 0 else 0.0
    fs_cpi = (fs_cycles / fs_instr) if fs_instr > 0 else 0.0
    fs_ipc = (fs_instr / fs_cycles) if fs_cycles > 0 else 0.0

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
    
    print("\n" + "\n".join(perf_output))
    print(f"\nPerformance metrics saved to: {perf_path}")
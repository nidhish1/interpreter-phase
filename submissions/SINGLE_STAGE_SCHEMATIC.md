# Single-Stage Processor Schematic

## Architecture Overview

The single-stage processor executes one complete instruction per clock cycle. All stages (fetch, decode, execute, memory access, and writeback) occur in the same cycle.

## Schematic Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SINGLE-STAGE PROCESSOR                          │
└─────────────────────────────────────────────────────────────────────────┘

                    ┌──────────────┐
                    │  Instruction │
                    │    Memory    │
                    │   (imem.txt) │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   PC (32-bit) │
                    └──────┬───────┘
                           │
                    ┌──────▼──────────────────────────────────────┐
                    │         INSTRUCTION FETCH (IF)               │
                    │  - Read instruction from imem[PC]           │
                    │  - Increment PC = PC + 4 (or branch target) │
                    └──────┬───────────────────────────────────────┘
                           │
                    ┌──────▼───────────────────────────────────────┐
                    │      INSTRUCTION DECODE (ID)                 │
                    │  - Extract: opcode, rd, rs1, rs2, funct3/7   │
                    │  - Extract and sign-extend immediates        │
                    │  - Read registers: RF[rs1], RF[rs2]          │
                    └──────┬───────────────────────────────────────┘
                           │
                    ┌──────▼───────────────────────────────────────┐
                    │         EXECUTE (EX)                         │
                    │  ┌────────────────────────────────────────┐  │
                    │  │  Control Unit                         │  │
                    │  │  - Decode opcode → control signals    │  │
                    │  │  - ALUOp, MemRead, MemWrite,          │  │
                    │  │    RegWrite, Branch, Jump              │  │
                    │  └──────────────┬─────────────────────────┘  │
                    │                 │                            │
                    │  ┌──────────────▼─────────────────────────┐  │
                    │  │  ALU (Arithmetic Logic Unit)           │  │
                    │  │  - ADD/SUB: rs1_val + rs2_val          │  │
                    │  │  - XOR/OR/AND: bitwise operations       │  │
                    │  │  - ADDI/XORI/ORI/ANDI: rs1_val + imm   │  │
                    │  │  - Address calc: rs1_val + imm (LW/SW) │  │
                    │  │  - Branch compare: rs1_val == rs2_val  │  │
                    │  └──────────────┬─────────────────────────┘  │
                    │                 │                            │
                    │  ┌──────────────▼─────────────────────────┐  │
                    │  │  Branch/Jump Logic                     │  │
                    │  │  - BEQ: if (rs1 == rs2) PC = PC + imm │  │
                    │  │  - BNE: if (rs1 != rs2) PC = PC + imm │  │
                    │  │  - JAL: PC = PC + imm, rd = PC + 4    │  │
                    │  └──────────────┬─────────────────────────┘  │
                    └─────────────────┼───────────────────────────┘
                                       │
                    ┌──────────────────▼──────────────────────────┐
                    │      MEMORY ACCESS (MEM)                    │
                    │  ┌──────────────────────────────────────┐  │
                    │  │  Data Memory (dmem.txt)              │  │
                    │  │  - LW: Read mem[address] → data      │  │
                    │  │  - SW: Write data → mem[address]     │  │
                    │  └──────────────────────────────────────┘  │
                    └──────────────────┬──────────────────────────┘
                                       │
                    ┌──────────────────▼──────────────────────────┐
                    │      WRITE BACK (WB)                        │
                    │  - Select write data:                        │
                    │    * ALU result (R-type, I-type)            │
                    │    * Memory data (LW)                       │
                    │    * PC + 4 (JAL)                           │
                    │  - Write to RF[rd] if rd != 0               │
                    └──────────────────┬──────────────────────────┘
                                       │
                    ┌──────────────────▼──────────────────────────┐
                    │      REGISTER FILE (32 registers)           │
                    │  - 32 × 32-bit registers                    │
                    │  - x0 (zero register) always = 0            │
                    │  - Read: RF[rs1], RF[rs2]                   │
                    │  - Write: RF[rd] = write_data               │
                    └──────────────────────────────────────────────┘
```

## Data Flow

### 1. Instruction Fetch
- PC points to current instruction
- Read 4 bytes from instruction memory starting at PC
- Assemble into 32-bit instruction (Big-Endian)
- Update PC: PC = PC + 4 (or branch/jump target)

### 2. Instruction Decode
- Extract fields:
  - `opcode = instr[6:0]`
  - `rd = instr[11:7]`
  - `funct3 = instr[14:12]`
  - `rs1 = instr[19:15]`
  - `rs2 = instr[24:20]`
  - `funct7 = instr[31:25]`
- Extract and sign-extend immediates:
  - I-type: `imm[11:0]`
  - S-type: `imm[11:0]` (from bits 31:25 and 11:7)
  - B-type: `imm[12:1]` (from bits 31, 30:25, 11:8, 7)
  - J-type: `imm[20:1]` (from bits 31, 19:12, 20, 30:21)
- Read register values: `rs1_val = RF[rs1]`, `rs2_val = RF[rs2]`

### 3. Execute
- **R-type instructions**:
  - ADD: `result = rs1_val + rs2_val`
  - SUB: `result = rs1_val - rs2_val`
  - XOR: `result = rs1_val ^ rs2_val`
  - OR: `result = rs1_val | rs2_val`
  - AND: `result = rs1_val & rs2_val`
- **I-type instructions**:
  - ADDI: `result = rs1_val + imm_i`
  - XORI: `result = rs1_val ^ imm_i`
  - ORI: `result = rs1_val | imm_i`
  - ANDI: `result = rs1_val & imm_i`
- **Load/Store**:
  - Calculate address: `addr = rs1_val + imm_i` (LW) or `rs1_val + imm_s` (SW)
- **Branches**:
  - BEQ: `if (rs1_val == rs2_val) PC = PC + imm_b`
  - BNE: `if (rs1_val != rs2_val) PC = PC + imm_b`
- **Jump**:
  - JAL: `PC = PC + imm_j`, `rd = PC + 4`

### 4. Memory Access
- **Load Word (LW)**: Read 32-bit word from `dmem[address]`
- **Store Word (SW)**: Write `rs2_val` to `dmem[address]`
- **Other instructions**: Pass ALU result through

### 5. Write Back
- Select write data:
  - R-type, I-type: ALU result
  - LW: Memory read data
  - JAL: PC + 4 (return address)
- Write to register: `if (rd != 0) RF[rd] = write_data`

## Code Implementation

The single-stage processor is implemented in the `SingleStageCore` class in `code/main.py`.

### Key Components:

1. **Instruction Memory (`InsMem` class)**:
   - Reads from `imem.txt`
   - `readInstr(PC)`: Fetches 32-bit instruction at byte address PC

2. **Data Memory (`DataMem` class)**:
   - Reads from/writes to `dmem.txt`
   - `readInstr(addr)`: Reads 32-bit word from byte address
   - `writeDataMem(addr, data)`: Writes 32-bit word to byte address

3. **Register File (`RegisterFile` class)**:
   - 32 registers initialized to 0
   - `readRF(reg_addr)`: Returns register value
   - `writeRF(reg_addr, data)`: Writes to register (ignores x0)

4. **Single-Stage Core (`SingleStageCore` class)**:
   - `step()`: Executes one instruction per cycle
   - Implements all instruction types
   - Updates PC, registers, and memory

### Execution Flow (from code):

```python
def step(self):
    # 1. Fetch instruction
    PC = self.state.IF["PC"]
    instr = self.ext_imem.readInstr(PC)
    
    # 2. Decode instruction
    opcode = instr & 0x7f
    rd = (instr >> 7) & 0x1f
    rs1 = (instr >> 15) & 0x1f
    rs2 = (instr >> 20) & 0x1f
    funct3 = (instr >> 12) & 0x7
    funct7 = (instr >> 25) & 0x7f
    
    # 3. Extract immediates
    imm_i = sign_extend((instr >> 20) & 0xFFF, 12)
    imm_s = sign_extend(((instr >> 25) << 5) | ((instr >> 7) & 0x1F), 12)
    imm_b = ... # Branch immediate
    imm_j = ... # Jump immediate
    
    # 4. Read registers
    rs1_val = self.myRF.readRF(rs1)
    rs2_val = self.myRF.readRF(rs2)
    
    # 5. Execute based on opcode
    if opcode == 0x33:  # R-type
        # Perform ALU operation
    elif opcode == 0x13:  # I-type
        # Perform ALU operation with immediate
    elif opcode == 0x03:  # LW
        # Load from memory
    elif opcode == 0x23:  # SW
        # Store to memory
    elif opcode == 0x63:  # Branch
        # Update PC if condition met
    elif opcode == 0x6f:  # JAL
        # Jump and link
    
    # 6. Write back to register
    if write_back_enable and rd != 0:
        self.myRF.writeRF(rd, write_back_data)
    
    # 7. Update PC
    self.nextState.IF["PC"] = nextPC
```

## Control Signals

The single-stage processor uses implicit control based on opcode and funct fields:

| Instruction | Opcode | funct3 | funct7 | Control Signals |
|------------|--------|--------|--------|----------------|
| ADD        | 0x33   | 0x0    | 0x00   | ALUSrc=0, ALUOp=ADD, RegWrite=1 |
| SUB        | 0x33   | 0x0    | 0x20   | ALUSrc=0, ALUOp=SUB, RegWrite=1 |
| XOR        | 0x33   | 0x4    | 0x00   | ALUSrc=0, ALUOp=XOR, RegWrite=1 |
| OR         | 0x33   | 0x6    | 0x00   | ALUSrc=0, ALUOp=OR, RegWrite=1 |
| AND        | 0x33   | 0x7    | 0x00   | ALUSrc=0, ALUOp=AND, RegWrite=1 |
| ADDI       | 0x13   | 0x0    | -      | ALUSrc=1, ALUOp=ADD, RegWrite=1 |
| XORI       | 0x13   | 0x4    | -      | ALUSrc=1, ALUOp=XOR, RegWrite=1 |
| ORI        | 0x13   | 0x6    | -      | ALUSrc=1, ALUOp=OR, RegWrite=1 |
| ANDI       | 0x13   | 0x7    | -      | ALUSrc=1, ALUOp=AND, RegWrite=1 |
| LW         | 0x03   | 0x2    | -      | ALUSrc=1, MemRead=1, RegWrite=1 |
| SW         | 0x23   | 0x2    | -      | ALUSrc=1, MemWrite=1, RegWrite=0 |
| BEQ        | 0x63   | 0x0    | -      | Branch=1, BranchOp=EQ |
| BNE        | 0x63   | 0x1    | -      | Branch=1, BranchOp=NE |
| JAL        | 0x6f   | -      | -      | Jump=1, RegWrite=1 |
| HALT       | 0x7f   | -      | -      | Halt=1 |

## Timing

- **One cycle per instruction**: All stages complete in a single clock cycle
- **CPI = 1.0** (for non-branching code)
- **No pipeline hazards**: Since only one instruction executes at a time
- **Simple and predictable**: Easy to verify correctness

## Advantages

1. **Simplicity**: Easy to understand and implement
2. **No hazards**: No data or control hazards
3. **Deterministic**: Predictable execution time
4. **Easy debugging**: All instruction effects visible in one cycle

## Disadvantages

1. **Low performance**: Only one instruction per cycle
2. **No parallelism**: Cannot overlap instruction execution
3. **Higher CPI**: Compared to pipelined processors

## Example Execution

For instruction `ADDI R1, R0, #5` (R1 = R0 + 5):

```
Cycle 0:
  PC = 0
  Fetch: instr = 0x00500093 (ADDI R1, R0, #5)
  Decode: opcode=0x13, rd=1, rs1=0, imm=5
  Read: rs1_val = RF[0] = 0
  Execute: result = 0 + 5 = 5
  Memory: (no access)
  Writeback: RF[1] = 5
  Update: PC = 4
  
Cycle 1:
  PC = 4
  (next instruction...)
```

## Files

- **Implementation**: `code/main.py` - `SingleStageCore` class
- **Input**: `code/input/<testcase>/imem.txt`, `dmem.txt`
- **Output**: `results/<testcase>/SS_RFResult.txt`, `SS_DMEMResult.txt`, `StateResult_SS.txt`


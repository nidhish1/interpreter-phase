# Five-Stage Pipelined Processor Schematic

## Architecture Overview

The five-stage pipelined processor executes multiple instructions simultaneously across five pipeline stages. Instructions flow through IF → ID → EX → MEM → WB stages, with pipeline registers (latches) between each stage. The processor handles RAW hazards through forwarding and stalling, and control hazards through branch prediction and flushing.

## Schematic Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    FIVE-STAGE PIPELINED PROCESSOR                           │
└─────────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────────┐
│  STAGE 1: INSTRUCTION FETCH (IF)                                            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│         ┌──────────────┐                                                     │
│         │  Instruction │                                                     │
│         │    Memory    │                                                     │
│         │   (imem.txt) │                                                     │
│         └──────┬───────┘                                                     │
│                │                                                             │
│         ┌──────▼───────┐         ┌──────────────┐                            │
│         │   PC (32-bit)│◄────────┤ Branch/Jump  │                            │
│         └──────┬───────┘         │   MUX       │                            │
│                │                 └──────┬───────┘                            │
│         ┌──────▼───────────────────────┘                                    │
│         │  IF Stage:                                                         │
│         │  - Fetch instruction from imem[PC]                                │
│         │  - PC = PC + 4 (or branch/jump target)                             │
│         │  - Stall if load-use hazard detected                               │
│         └──────┬─────────────────────────────────────────────────────────────┘
│                │                                                             │
│         ┌──────▼─────────────────────────────────────────────────────────────┐
│         │                    IF/ID Pipeline Register                         │
│         │  ┌──────────────────────────────────────────────────────────────┐ │
│         │  │ IF.nop: bool                                                 │ │
│         │  │ IF.PC: 32-bit (PC of fetched instruction)                   │ │
│         │  │ IF.fetch_PC: 32-bit (PC used to fetch instruction)          │ │
│         │  └──────────────────────────────────────────────────────────────┘ │
│         └──────┬─────────────────────────────────────────────────────────────┘
│                │
┌──────────────────────────────────────────────────────────────────────────────┐
│  STAGE 2: INSTRUCTION DECODE / REGISTER READ (ID)                           │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│         ┌──────▼───────────────────────────────────────────────────────────┐
│         │  ID Stage:                                                         │
│         │  ┌─────────────────────────────────────────────────────────────┐  │
│         │  │ Instruction Decode:                                         │  │
│         │  │ - Extract: opcode, rd, rs1, rs2, funct3, funct7              │  │
│         │  │ - Extract and sign-extend immediates (I, S, B, J types)     │  │
│         │  └─────────────────────────────────────────────────────────────┘  │
│         │                                                                   │
│         │  ┌─────────────────────────────────────────────────────────────┐  │
│         │  │ Register File Read:                                        │  │
│         │  │ - Read RF[rs1], RF[rs2]                                    │  │
│         │  │ - Forwarding from EX, MEM, WB stages                       │  │
│         │  └─────────────────────────────────────────────────────────────┘  │
│         │                                                                   │
│         │  ┌─────────────────────────────────────────────────────────────┐  │
│         │  │ Branch Resolution:                                          │  │
│         │  │ - Compare rs1_val == rs2_val (BEQ) or != (BNE)             │  │
│         │  │ - Calculate branch target: PC + imm_b                       │  │
│         │  │ - If taken: flush ID, redirect IF to target                │  │
│         │  │ - Forwarding for branch operands (EX-ID, MEM-ID, WB-ID)  │  │
│         │  └─────────────────────────────────────────────────────────────┘  │
│         │                                                                   │
│         │  ┌─────────────────────────────────────────────────────────────┐  │
│         │  │ JAL Resolution:                                            │  │
│         │  │ - Calculate jump target: PC + imm_j                        │  │
│         │  │ - Redirect IF to target                                    │  │
│         │  │ - Pass instruction to EX for return address calculation   │  │
│         │  └─────────────────────────────────────────────────────────────┘  │
│         │                                                                   │
│         │  ┌─────────────────────────────────────────────────────────────┐  │
│         │  │ Load-Use Hazard Detection:                                  │  │
│         │  │ - Check if MEM stage has load                              │  │
│         │  │ - Check if ID instruction needs that register               │  │
│         │  │ - If hazard: stall pipeline (insert bubble in EX)          │  │
│         │  └─────────────────────────────────────────────────────────────┘  │
│         │                                                                   │
│         │  ┌─────────────────────────────────────────────────────────────┐  │
│         │  │ Forwarding MUX (for ID stage):                              │  │
│         │  │ - EX-ID: Compute ALU result early for branch resolution    │  │
│         │  │ - MEM-ID: Forward ALU result from MEM stage                 │  │
│         │  │ - WB-ID: Forward result from WB stage                      │  │
│         │  │ - Priority: EX > MEM > WB > RF                             │  │
│         │  └─────────────────────────────────────────────────────────────┘  │
│         └──────┬───────────────────────────────────────────────────────────┘
│                │                                                             │
│         ┌──────▼─────────────────────────────────────────────────────────────┐
│         │                    ID/EX Pipeline Register                         │
│         │  ┌──────────────────────────────────────────────────────────────┐ │
│         │  │ ID.nop: bool                                                 │ │
│         │  │ ID.Instr: 32-bit instruction                                 │ │
│         │  │ ID.PC: 32-bit (PC of instruction in ID)                     │ │
│         │  └──────────────────────────────────────────────────────────────┘ │
│         └──────┬─────────────────────────────────────────────────────────────┘
│                │
┌──────────────────────────────────────────────────────────────────────────────┐
│  STAGE 3: EXECUTE (EX)                                                       │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│         ┌──────▼───────────────────────────────────────────────────────────┐
│         │  EX Stage:                                                         │
│         │                                                                   │
│         │  ┌─────────────────────────────────────────────────────────────┐  │
│         │  │ Forwarding MUX (for EX stage):                              │  │
│         │  │ - MEM-EX: Forward ALU result from MEM stage                    │  │
│         │  │ - WB-EX: Forward result from WB stage                        │  │
│         │  │ - Priority: MEM > WB > RF                                    │  │
│         │  │ - Select forwarded values for rs1 and rs2                    │  │
│         │  └─────────────────────────────────────────────────────────────┘  │
│         │                                                                   │
│         │  ┌─────────────────────────────────────────────────────────────┐  │
│         │  │ ALU (Arithmetic Logic Unit):                                │  │
│         │  │ - R-type: rs1_val op rs2_val (ADD, SUB, XOR, OR, AND)       │  │
│         │  │ - I-type: rs1_val op imm (ADDI, XORI, ORI, ANDI)           │  │
│         │  │ - Address calc: rs1_val + imm (for LW/SW)                  │  │
│         │  │ - JAL: Calculate return address (PC + 4)                    │  │
│         │  └─────────────────────────────────────────────────────────────┘  │
│         │                                                                   │
│         │  ┌─────────────────────────────────────────────────────────────┐  │
│         │  │ Control Signals:                                            │  │
│         │  │ - is_I_type: I-type instruction flag                        │  │
│         │  │ - rd_mem: Load instruction flag                             │  │
│         │  │ - wrt_mem: Store instruction flag                           │  │
│         │  │ - wrt_enable: Write to register flag                       │  │
│         │  │ - alu_op: ALU operation code                                │  │
│         │  └─────────────────────────────────────────────────────────────┘  │
│         └──────┬───────────────────────────────────────────────────────────┘
│                │                                                             │
│         ┌──────▼─────────────────────────────────────────────────────────────┐
│         │                    EX/MEM Pipeline Register                       │
│         │  ┌──────────────────────────────────────────────────────────────┐ │
│         │  │ EX.nop: bool                                                 │ │
│         │  │ EX.instr: 32-bit instruction                                │ │
│         │  │ EX.Read_data1: 32-bit (rs1 value)                           │ │
│         │  │ EX.Read_data2: 32-bit (rs2 value)                           │ │
│         │  │ EX.Imm: 32-bit immediate                                    │ │
│         │  │ EX.Rs: 5-bit (rs1 register number)                          │ │
│         │  │ EX.Rt: 5-bit (rs2 register number)                           │ │
│         │  │ EX.Wrt_reg_addr: 5-bit (rd register number)                │ │
│         │  │ EX.is_I_type: bool                                          │ │
│         │  │ EX.rd_mem: bool                                             │ │
│         │  │ EX.wrt_mem: bool                                            │ │
│         │  │ EX.alu_op: 2-bit ALU operation code                         │ │
│         │  │ EX.wrt_enable: bool                                         │ │
│         │  │ EX.PC: 32-bit (for JAL return address)                      │ │
│         │  │ EX.is_jal: bool                                             │ │
│         │  └──────────────────────────────────────────────────────────────┘ │
│         └──────┬─────────────────────────────────────────────────────────────┘
│                │
┌──────────────────────────────────────────────────────────────────────────────┐
│  STAGE 4: MEMORY ACCESS (MEM)                                                │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│         ┌──────▼───────────────────────────────────────────────────────────┐
│         │  MEM Stage:                                                         │
│         │                                                                   │
│         │  ┌─────────────────────────────────────────────────────────────┐  │
│         │  │ Data Memory Access:                                        │  │
│         │  │ - Load Word (LW): Read mem[ALUresult] → data              │  │
│         │  │ - Store Word (SW): Write Store_data → mem[ALUresult]       │  │
│         │  │ - Other instructions: Pass ALUresult through                │  │
│         │  └─────────────────────────────────────────────────────────────┘  │
│         │                                                                   │
│         │  ┌─────────────────────────────────────────────────────────────┐  │
│         │  │ Write Data Selection:                                       │  │
│         │  │ - Load: Memory read data                                   │  │
│         │  │ - Store: ALU result (address)                              │  │
│         │  │ - ALU ops: ALU result                                       │  │
│         │  └─────────────────────────────────────────────────────────────┘  │
│         └──────┬───────────────────────────────────────────────────────────┘
│                │                                                             │
│         ┌──────▼─────────────────────────────────────────────────────────────┐
│         │                    MEM/WB Pipeline Register                       │
│         │  ┌──────────────────────────────────────────────────────────────┐ │
│         │  │ MEM.nop: bool                                                │ │
│         │  │ MEM.ALUresult: 32-bit ALU result or memory address          │ │
│         │  │ MEM.Store_data: 32-bit data to store (for SW)                │ │
│         │  │ MEM.Rs: 5-bit (rs1 register number)                          │ │
│         │  │ MEM.Rt: 5-bit (rs2 register number)                           │ │
│         │  │ MEM.Wrt_reg_addr: 5-bit (rd register number)                │ │
│         │  │ MEM.rd_mem: bool                                             │ │
│         │  │ MEM.wrt_mem: bool                                            │ │
│         │  │ MEM.wrt_enable: bool                                         │ │
│         │  └──────────────────────────────────────────────────────────────┘ │
│         └──────┬─────────────────────────────────────────────────────────────┘
│                │
┌──────────────────────────────────────────────────────────────────────────────┐
│  STAGE 5: WRITE BACK (WB)                                                     │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│         ┌──────▼───────────────────────────────────────────────────────────┐
│         │  WB Stage:                                                         │
│         │                                                                   │
│         │  ┌─────────────────────────────────────────────────────────────┐  │
│         │  │ Register File Write:                                        │  │
│         │  │ - Write Wrt_data to RF[Wrt_reg_addr]                        │  │
│         │  │ - Ignore if Wrt_reg_addr == 0 (x0 register)                │  │
│         │  │ - Count instruction as retired                              │  │
│         │  └─────────────────────────────────────────────────────────────┘  │
│         │                                                                   │
│         │  ┌─────────────────────────────────────────────────────────────┐  │
│         │  │ Forwarding Source:                                          │  │
│         │  │ - WB stage provides data for forwarding to EX and ID        │  │
│         │  │ - Used when no closer forwarding available                  │  │
│         │  └─────────────────────────────────────────────────────────────┘  │
│         └──────┬───────────────────────────────────────────────────────────┘
│                │                                                             │
│         ┌──────▼─────────────────────────────────────────────────────────────┐
│         │                    Register File (32 registers)                    │
│         │  ┌──────────────────────────────────────────────────────────────┐ │
│         │  │ - 32 × 32-bit registers (x0 through x31)                   │ │
│         │  │ - x0 (zero register) always = 0                             │ │
│         │  │ - Read ports: rs1, rs2                                      │ │
│         │  │ - Write port: rd (from WB stage)                            │ │
│         │  └──────────────────────────────────────────────────────────────┘ │
│         └─────────────────────────────────────────────────────────────────────┘
```

## Forwarding Paths

### 1. EX-ID Forwarding (for Branch Resolution)
```
EX Stage (current cycle) → ID Stage (same cycle)
- Compute ALU result early in EX stage
- Forward to ID stage for branch comparison
- Used when branch depends on result from EX stage
```

### 2. MEM-ID Forwarding (for Branch Resolution)
```
MEM Stage → ID Stage
- Forward ALU result from MEM stage
- Used when branch depends on result from MEM stage
- Priority: Higher than WB-ID forwarding
```

### 3. WB-ID Forwarding (for Branch Resolution)
```
WB Stage → ID Stage
- Forward result from WB stage
- Used when branch depends on result from WB stage
- Priority: Lowest (only if no EX or MEM forwarding)
```

### 4. MEM-EX Forwarding
```
MEM Stage → EX Stage
- Forward ALU result from MEM stage
- Used when EX stage needs result from MEM stage
- Priority: Higher than WB-EX forwarding
```

### 5. WB-EX Forwarding
```
WB Stage → EX Stage
- Forward result from WB stage
- Used when EX stage needs result from WB stage
- Priority: Lowest (only if no MEM forwarding)
```

## Hazard Detection and Handling

### RAW (Read After Write) Hazards

#### Case 1: Can be resolved by forwarding
```
Instruction i:   ADD R1, R2, R3    (Writes R1)
Instruction i+1: ADD R4, R1, R5    (Reads R1)

Solution: Forward R1 from MEM or WB stage to EX stage
```

#### Case 2: Load-Use Hazard (requires stalling)
```
Instruction i:   LW R1, R2, #0     (Loads R1 from memory)
Instruction i+1: ADD R4, R1, R5    (Needs R1 immediately)

Solution: 
- Detect hazard in ID stage
- Insert bubble (NOP) in EX stage
- Stall ID and IF stages for one cycle
- After one cycle, forward loaded value from MEM stage
```

### Control Hazards

#### Branch Instructions
```
Instruction i:   BEQ R1, R2, target
Instruction i+1: ADD R3, R4, R5    (Fetched speculatively)

Solution:
- Assume branch NOT TAKEN (fetch PC+4)
- Resolve branch in ID stage
- If taken: Flush ID stage (insert bubble), redirect IF to target
- If not taken: Continue normally
```

#### Jump Instructions (JAL)
```
Instruction i:   JAL R10, target
Instruction i+1: ADD R3, R4, R5    (Fetched speculatively)

Solution:
- Detect JAL in ID stage
- Redirect IF to jump target immediately
- Keep JAL in pipeline to calculate return address (PC+4)
- Flush is not needed (unconditional jump)
```

## Pipeline Stalls

### Load-Use Hazard Stall
```
Cycle N:   IF: I+1    ID: I      EX: I-1    MEM: LW R1    WB: I-2
Cycle N+1: IF: stall  ID: stall  EX: bubble MEM: LW R1    WB: I-1
Cycle N+2: IF: I+2    ID: I+1    EX: I      MEM: (data)   WB: LW R1
```

### Branch Taken Stall
```
Cycle N:   IF: I+1    ID: BEQ     EX: I-1    MEM: I-2    WB: I-3
Cycle N+1: IF: target ID: bubble EX: bubble MEM: I-1    WB: I-2
Cycle N+2: IF: target+4 ID: target EX: I-1  MEM: bubble WB: I-1
```

## Code Implementation

The five-stage pipeline is implemented in the `FiveStageCore` class in `code/main.py`.

### Key Components:

1. **Pipeline State (`State` class)**:
   - Stores pipeline registers for each stage
   - Tracks nop flags, instruction data, and control signals

2. **Stage Execution Order**:
   - Stages execute in reverse order: WB → MEM → EX → ID → IF
   - Ensures data flows correctly through pipeline

3. **Forwarding Logic**:
   - Implemented in ID and EX stages
   - Checks for data dependencies and forwards from appropriate stage

4. **Hazard Detection**:
   - Load-use hazard: Detected in ID stage
   - Control hazard: Branches resolved in ID stage

### Execution Flow (from code):

```python
def step(self):
    # Execute stages in reverse order (WB → MEM → EX → ID → IF)
    
    # ========== WB Stage: Write Back ==========
    if not self.state.WB["nop"]:
        if self.state.WB["wrt_enable"] and self.state.WB["Wrt_reg_addr"] != 0:
            self.myRF.writeRF(self.state.WB["Wrt_reg_addr"], self.state.WB["Wrt_data"])
        self.retired_instructions += 1
    
    # ========== MEM Stage: Memory Access ==========
    if not self.state.MEM["nop"]:
        if self.state.MEM["rd_mem"]:  # Load
            mem_val = self.ext_dmem.readInstr(self.state.MEM["ALUresult"])
            self.nextState.WB["Wrt_data"] = mem_val
        elif self.state.MEM["wrt_mem"]:  # Store
            self.ext_dmem.writeDataMem(self.state.MEM["ALUresult"], self.state.MEM["Store_data"])
        else:  # ALU result
            self.nextState.WB["Wrt_data"] = self.state.MEM["ALUresult"]
    
    # ========== EX Stage: Execute ==========
    # Forwarding from MEM and WB stages
    ex_rs1_val = self.state.EX["Read_data1"]
    ex_rs2_val = self.state.EX["Read_data2"]
    
    # Forward from MEM stage
    if not self.state.MEM["nop"] and self.state.MEM["wrt_enable"]:
        if self.state.MEM["Wrt_reg_addr"] == self.state.EX["Rs"]:
            if not self.state.MEM["rd_mem"]:
                ex_rs1_val = self.state.MEM["ALUresult"]
        # Similar for rs2...
    
    # Forward from WB stage
    if not self.state.WB["nop"] and self.state.WB["wrt_enable"]:
        # Forward if not already forwarding from MEM...
        if self.state.WB["Wrt_reg_addr"] == self.state.EX["Rs"]:
            ex_rs1_val = self.state.WB["Wrt_data"]
    
    # Perform ALU operation
    if self.state.EX["is_jal"]:
        alu_result = self.state.EX["PC"] + 4  # Return address
    else:
        alu_result = ...  # ALU operation based on instruction type
    
    # ========== ID Stage: Instruction Decode ==========
    # Load-use hazard detection
    load_use_hazard = False
    if not self.state.MEM["nop"] and self.state.MEM["rd_mem"]:
        if self.state.MEM["Wrt_reg_addr"] == rs1 or self.state.MEM["Wrt_reg_addr"] == rs2:
            load_use_hazard = True
    
    # Forwarding for branch resolution (EX-ID, MEM-ID, WB-ID)
    id_rs1_val = self.myRF.readRF(rs1)
    id_rs2_val = self.myRF.readRF(rs2)
    
    # Forward from EX stage (compute ALU result early)
    if not self.state.EX["nop"] and self.state.EX["wrt_enable"]:
        # Compute ALU result early and forward...
        id_rs1_val = ex_alu_result
    
    # Forward from MEM stage
    if not self.state.MEM["nop"] and self.state.MEM["wrt_enable"]:
        if self.state.MEM["Wrt_reg_addr"] == rs1:
            id_rs1_val = self.state.MEM["ALUresult"]
    
    # Forward from WB stage
    if not self.state.WB["nop"] and self.state.WB["wrt_enable"]:
        if self.state.WB["Wrt_reg_addr"] == rs1:
            id_rs1_val = self.state.WB["Wrt_data"]
    
    # Branch resolution
    if opcode == 0x63:  # Branch
        if funct3 == 0x0 and id_rs1_val == id_rs2_val:  # BEQ
            branch_taken = True
            branch_target = branch_pc + imm_b
    
    # JAL resolution
    if opcode == 0x6f:  # JAL
        jal_taken = True
        jal_target = jal_pc + imm_j
    
    # Stall if load-use hazard
    if load_use_hazard:
        # Insert bubble in EX, stall ID and IF
        self.nextState.EX["nop"] = True
        self.nextState.ID = self.state.ID.copy()  # Keep ID
        self.nextState.IF = self.state.IF.copy()  # Keep IF
    
    # Flush if branch taken
    elif branch_taken:
        self.nextState.IF["PC"] = branch_target
        self.nextState.ID["nop"] = True  # Flush ID
        self.nextState.EX["nop"] = True  # Flush EX
    
    # ========== IF Stage: Instruction Fetch ==========
    if not load_use_hazard:
        if not self.state.IF["nop"]:
            PC = self.state.IF["PC"]
            instr = self.ext_imem.readInstr(PC)
            if opcode == 0x7f:  # HALT
                self.nextState.IF["nop"] = True
            else:
                if not branch_taken and not jal_taken:
                    self.nextState.IF["PC"] = PC + 4
```

## Forwarding Priority

### For EX Stage Operands:
1. **MEM-EX**: Highest priority (most recent result)
2. **WB-EX**: Lower priority (older result)
3. **RF**: Default (register file value)

### For ID Stage Operands (Branch Resolution):
1. **EX-ID**: Highest priority (compute ALU result early)
2. **MEM-ID**: Medium priority
3. **WB-ID**: Lower priority
4. **RF**: Default (register file value)

## Pipeline Register Fields

### IF/ID Register:
- `IF.nop`: No operation flag
- `IF.PC`: Program counter
- `IF.fetch_PC`: PC used to fetch instruction

### ID/EX Register:
- `ID.nop`: No operation flag
- `ID.Instr`: 32-bit instruction
- `ID.PC`: PC of instruction in ID stage

### EX/MEM Register:
- `EX.nop`: No operation flag
- `EX.instr`: 32-bit instruction
- `EX.Read_data1`: rs1 value (with forwarding)
- `EX.Read_data2`: rs2 value (with forwarding)
- `EX.Imm`: Immediate value
- `EX.Rs`, `EX.Rt`: Source register numbers
- `EX.Wrt_reg_addr`: Destination register number
- `EX.is_I_type`: I-type instruction flag
- `EX.rd_mem`: Load instruction flag
- `EX.wrt_mem`: Store instruction flag
- `EX.alu_op`: ALU operation code
- `EX.wrt_enable`: Write enable flag
- `EX.PC`: PC for JAL return address
- `EX.is_jal`: JAL instruction flag

### MEM/WB Register:
- `MEM.nop`: No operation flag
- `MEM.ALUresult`: ALU result or memory address
- `MEM.Store_data`: Data to store
- `MEM.Rs`, `MEM.Rt`: Register numbers
- `MEM.Wrt_reg_addr`: Destination register number
- `MEM.rd_mem`: Load flag
- `MEM.wrt_mem`: Store flag
- `MEM.wrt_enable`: Write enable flag

### WB Register:
- `WB.nop`: No operation flag
- `WB.Wrt_data`: Data to write to register
- `WB.Rs`, `WB.Rt`: Register numbers
- `WB.Wrt_reg_addr`: Destination register number
- `WB.wrt_enable`: Write enable flag

## Example Pipeline Execution

### Example 1: No Hazards
```
Cycle 0: IF: I0    ID: -     EX: -    MEM: -    WB: -
Cycle 1: IF: I1    ID: I0     EX: -    MEM: -    WB: -
Cycle 2: IF: I2    ID: I1     EX: I0   MEM: -    WB: -
Cycle 3: IF: I3    ID: I2     EX: I1   MEM: I0   WB: -
Cycle 4: IF: I4    ID: I3     EX: I2   MEM: I1   WB: I0
Cycle 5: IF: I5    ID: I4     EX: I3   MEM: I2   WB: I1
```

### Example 2: Load-Use Hazard with Stalling
```
Instruction sequence:
I0: LW R1, R2, #0
I1: ADD R3, R1, R4

Cycle 0: IF: I0    ID: -     EX: -    MEM: -    WB: -
Cycle 1: IF: I1    ID: I0    EX: -    MEM: -    WB: -
Cycle 2: IF: I2    ID: I1    EX: I0   MEM: -    WB: -
Cycle 3: IF: stall ID: I1    EX: bubble MEM: I0 WB: -    (Hazard detected!)
Cycle 4: IF: I2    ID: I1    EX: I0   MEM: (data) WB: -    (Forward data)
Cycle 5: IF: I3    ID: I2    EX: I1   MEM: -    WB: I0
```

### Example 3: Branch Taken
```
Instruction sequence:
I0: ADD R1, R2, R3
I1: BEQ R1, R4, target
I2: ADD R5, R6, R7  (speculatively fetched)
I3: target: SUB R8, R9, R10

Cycle 0: IF: I0    ID: -     EX: -    MEM: -    WB: -
Cycle 1: IF: I1    ID: I0    EX: -    MEM: -    WB: -
Cycle 2: IF: I2    ID: I1    EX: I0   MEM: -    WB: -
Cycle 3: IF: target ID: bubble EX: bubble MEM: I0 WB: -  (Branch taken, flush)
Cycle 4: IF: target+4 ID: target EX: -    MEM: -    WB: I0
```

## Performance Characteristics

- **Ideal CPI**: 1.0 (one instruction per cycle when pipeline is full)
- **Actual CPI**: > 1.0 due to:
  - Pipeline fill (first few cycles)
  - Pipeline drain (last few cycles)
  - Stalls (load-use hazards)
  - Branch mispredictions (1 cycle penalty)
- **Throughput**: Up to 5 instructions in flight simultaneously
- **Latency**: 5 cycles from fetch to completion

## Advantages

1. **Higher throughput**: Multiple instructions in flight
2. **Better resource utilization**: Stages work in parallel
3. **Forwarding reduces stalls**: Most RAW hazards resolved without stalling
4. **Scalable**: Can add more pipeline stages for higher performance

## Disadvantages

1. **Complexity**: More complex than single-stage
2. **Hazard handling**: Requires forwarding and stalling logic
3. **Control hazards**: Branch mispredictions cause pipeline flushes
4. **Pipeline bubbles**: Reduce efficiency when hazards occur

## Files

- **Implementation**: `code/main.py` - `FiveStageCore` class
- **Input**: `code/input/<testcase>/imem.txt`, `dmem.txt`
- **Output**: `results/<testcase>/FS_RFResult.txt`, `FS_DMEMResult.txt`, `StateResult_FS.txt`


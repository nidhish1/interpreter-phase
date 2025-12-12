# RISC-V Processor Simulator - Phase 2

**Student:** Nidhish Gautam (ng3483)  
**Course:** ECE GY 6913 - Computing Systems Architecture  
**Project:** Five-Stage Pipelined RISC-V Processor Implementation

This project implements cycle-accurate simulators of a 32-bit RISC-V processor in Python, supporting both single-stage and five-stage pipelined processor architectures with comprehensive hazard handling.

---

## ⚡ Quick Reference

```bash
# Run all testcases
make run-all

# Compare with expected outputs  
make compare-all

# View performance metrics
cat results/testcase1/PerformanceMetrics.txt
```

**Key Files:**
- 📄 `submission_simple.latex` - Final report (use this one!)
- 📄 `mermaid_diagrams.md` - Schematic diagrams
- 💻 `code/main.py` - Simulator implementation

---

## 🎯 Project Tasks Summary

| Task | Points | Description | Status |
|------|--------|-------------|--------|
| 1 | 20 | Single-stage schematic + simulator | ✅ Complete |
| 2 | 20 | Five-stage schematic + hazard handling | ✅ Complete |
| 3 | 5 | Performance metrics (CPI, cycles, IPC) | ✅ Complete |
| 4 | 5 | Performance comparison | ✅ Complete |
| 5 | +1 | Optimization proposals | ✅ Complete |
| **Total** | **51/51** | | **All Done** |

### Task Details

**Task 1:** Single-Stage Processor
- Class: `SingleStageCore` in `main.py`
- CPI = 1.0, simple design, no hazards
- Schematic: `mermaid_diagrams.md` → render → `single_stage_schematic.png`

**Task 2:** Five-Stage Pipelined Processor  
- Class: `FiveStageCore` in `main.py`
- RAW hazards: Forwarding (EX-ID, MEM-ID, MEM-EX, WB-EX) + Stalling (load-use)
- Control hazards: Branch resolution in ID/RF, predict-not-taken, 1-cycle penalty
- Schematic: `mermaid_diagrams.md` → render → `pipelined_schematic.png`

**Task 3:** Performance Metrics
- Console output + `PerformanceMetrics.txt` file
- Reports: CPI, Total Cycles, Instructions, IPC

**Task 4:** Comparison
- **Result:** Five-stage is 3-4x faster (higher clock frequency dominates)
- Detailed analysis in `submission_simple.latex`

**Task 5:** Optimizations (Extra Credit)
- Branch prediction, caches, enhanced forwarding, compiler opts, OoO execution
- Potential combined speedup: 5-7x

---

## 📚 Documentation

- **[submission_simple.latex](submission_simple.latex)**: Complete project report (clean, concise version)
- **[submission.latex](submission.latex)**: Detailed project report (comprehensive version)
- **[mermaid_diagrams.md](mermaid_diagrams.md)**: Mermaid code for processor schematics
- **[FIVE_STAGE_SCHEMATIC.md](submissions/FIVE_STAGE_SCHEMATIC.md)**: Detailed five-stage documentation

---

## 🚀 Quick Start

### Run All Testcases
```bash
# Using Makefile (recommended)
make run-all

# Or manually
python3 code/main.py --iodir code/input/testcase0
python3 code/main.py --iodir code/input/testcase1
python3 code/main.py --iodir code/input/testcase2
```

### Verify Results
```bash
# Compare all testcases
make compare-all

# Or compare specific testcase
python3 code/compare_outputs.py --results-root results --testcase testcase0
```

### Expected Output
```
======================================================================
PERFORMANCE METRICS
======================================================================

Performance of Single Stage:
  Total Execution Cycles: 40
  Total Instructions Retired: 39
  Average CPI (Cycles Per Instruction): 1.025641
  IPC (Instructions Per Cycle): 0.975000

Performance of Five Stage:
  Total Execution Cycles: 46
  Total Instructions Retired: 39
  Average CPI (Cycles Per Instruction): 1.179487
  IPC (Instructions Per Cycle): 0.847826
======================================================================
```

---

## 📁 Project Structure

```
phase1/
├── code/
│   ├── main.py                    # Main simulator (SingleStageCore + FiveStageCore)
│   ├── compare_outputs.py         # Output comparison tool
│   ├── input/                     # Test case inputs
│   │   ├── testcase0/             # Simple test (6 instructions, no branches)
│   │   ├── testcase1/             # Medium test (39 instructions)
│   │   └── testcase2/             # Complex test (loops + branches, 35 instructions)
│   └── sample_output/             # Expected outputs for verification
├── results/                       # Generated outputs (auto-created)
├── submissions/                   # Additional documentation
├── mermaid_diagrams.md            # Schematic diagrams (Mermaid code)
├── submission.latex               # Project report (detailed version)
├── Makefile                       # Build automation
└── README.md                      # This file
```

---

## 🏗️ Architecture Overview

### Single-Stage Core (SS)
**Executes one instruction per cycle** - all phases complete in one cycle:
1. Fetch instruction from IMEM
2. Decode and read registers
3. Execute ALU operation
4. Access memory (if needed)
5. Write back to register file
6. Update PC

**Characteristics:**
- CPI = 1.0 (perfect)
- Long clock cycle (all stages sequential)
- No hazard handling needed

### Five-Stage Pipeline Core (FS)
**Instruction-level parallelism** - 5 instructions in flight simultaneously:
1. **IF**: Fetch instruction
2. **ID/RF**: Decode, read registers, **resolve branches** ⭐
3. **EX**: Execute ALU operations (with forwarding)
4. **MEM**: Memory access
5. **WB**: Write back

**Pipeline Registers:** IF/ID, ID/EX, EX/MEM, MEM/WB (each with nop bit)

**Characteristics:**
- CPI = 1.18-1.83 (with hazards)
- Short clock cycle (only slowest stage)
- **3-4x faster** than single-stage overall

## Features

### Supported Instructions

- **R-type**: ADD, SUB, XOR, OR, AND
- **I-type**: ADDI, XORI, ORI, ANDI, LW (Load Word)
- **S-type**: SW (Store Word)
- **B-type**: BEQ (Branch if Equal), BNE (Branch if Not Equal)
- **J-type**: JAL (Jump and Link)
- **HALT**: Special instruction to stop execution

---

## ⚙️ Hazard Handling (Five-Stage Pipeline)

### RAW (Read-After-Write) Hazards

**Strategy:** Forwarding first, stalling only when necessary

**Forwarding Paths:**
- **EX→ID**: Forward from EX to ID for branch resolution (same cycle)
- **MEM→ID**: Forward from MEM to ID for branches  
- **MEM→EX**: Forward ALU results to next instruction
- **WB→EX**: Forward from WB to EX

**When Forwarding Isn't Enough:**
- **Load-Use Hazard**: When instruction in EX is a LOAD and current instruction in ID needs that value
- **Action:** Stall pipeline for 1 cycle (insert bubble in EX)
- **Result:** Data available from WB stage after stall

### Control Flow Hazards (Branches)

**Branch Handling Strategy:**

1. **Predict-Not-Taken:**
   - When branch fetched in IF, assume NOT TAKEN
   - PC speculatively updated to PC+4
   - Next sequential instruction fetched

2. **Branch Resolution in ID/RF Stage:**
   - Compare rs1 and rs2 (with forwarding if needed)
   - Calculate branch target: PC + imm_b
   - Determine if branch actually taken

3. **Handle Misprediction:**
   - If branch IS taken: Flush IF/ID (set nop=True), redirect PC to target
   - If branch NOT taken: Continue normally (prediction correct)
   - **Penalty:** 1 cycle (one bubble in pipeline)

**Example:**
```
Cycle N:   Branch in ID → Resolved as TAKEN
Cycle N+1: IF/ID.nop = True (bubble), IF fetches from branch target
Cycle N+2: Pipeline resumes with correct instruction
```

---

## Project Structure

```
phase1/
├── code/
│   ├── main.py              # Main simulator implementation
│   ├── compare_outputs.py   # Script to compare results with sample outputs
│   ├── input/               # Test case input files
│   │   ├── testcase0/
│   │   │   ├── imem.txt     # Instruction memory (byte-addressable, Big-Endian)
│   │   │   ├── dmem.txt     # Data memory (byte-addressable, Big-Endian)
│   │   │   └── code.asm     # Assembly code (for reference)
│   │   ├── testcase1/
│   │   └── testcase2/
│   └── sample_output/       # Expected outputs for comparison
│       ├── testcase0/
│       ├── testcase1/
│       └── testcase2/
├── results/                 # Generated output files (created after running)
│   ├── testcase0/
│   ├── testcase1/
│   └── testcase2/
├── Makefile                 # Build automation
└── README.md               # This file
```

## Output Files

For each test case, the simulator generates the following output files in `results/<testcase>/`:

### Single-Stage Core (SS)
- `SS_RFResult.txt`: Cycle-by-cycle register file state
- `SS_DMEMResult.txt`: Final data memory state after execution
- `StateResult_SS.txt`: Cycle-by-cycle microarchitectural state

### Five-Stage Pipeline Core (FS)
- `FS_RFResult.txt`: Cycle-by-cycle register file state
- `FS_DMEMResult.txt`: Final data memory state after execution
- `StateResult_FS.txt`: Cycle-by-cycle pipeline state (all 5 stages)

### Performance Metrics
- `PerformanceMetrics.txt`: Contains:
  - Total execution cycles
  - Total instructions retired
  - CPI (Cycles Per Instruction)
  - IPC (Instructions Per Cycle)

## Requirements

- Python 3.x
- Make (for using the Makefile)

## Usage

### Using the Makefile (Recommended)

The Makefile provides convenient commands for running and comparing test cases:

```bash
# Run a specific test case
make run TESTCASE=testcase0

# Run all test cases
make run-all

# Clean results and run all test cases
make clean-run

# Compare results with sample outputs for a specific test case
make compare TESTCASE=testcase0

# Compare results for all test cases
make compare-all

# Clean generated results
make clean-results

# Show help
make help
```

### Direct Python Execution

You can also run the simulator directly:

```bash
# Run a specific test case
python3 code/main.py --iodir code/input/testcase0

# Compare results
python3 code/compare_outputs.py \
  --results-dir results/testcase0 \
  --sample-dir code/sample_output/testcase0
```

## Memory Format

Both instruction memory (`imem.txt`) and data memory (`dmem.txt`) are:
- **Byte-addressable**: Each line represents one byte
- **Big-Endian format**: Most significant byte is stored at the lowest address
- **32-bit words**: Four consecutive bytes form one 32-bit instruction or data word

### Example

For a 32-bit instruction `0x12345678` stored at address 0:
```
Address 0: 00010010  (0x12 - MSB)
Address 1: 00110100  (0x34)
Address 2: 01010110  (0x56)
Address 3: 01111000  (0x78 - LSB)
```

## Instruction Encoding

The simulator follows the RISC-V instruction encoding format:

- **Opcode**: Bits [6:0]
- **rd**: Destination register [11:7]
- **funct3**: Function code [14:12]
- **rs1**: Source register 1 [19:15]
- **rs2**: Source register 2 [24:20]
- **funct7**: Function code [31:25]

Immediates are extracted and sign-extended according to the instruction type.

## Pipeline Stages (Five-Stage Core)

1. **IF (Instruction Fetch)**: Fetches instruction from instruction memory using PC
2. **ID (Instruction Decode/Register Read)**: Decodes instruction, reads registers, resolves branches
3. **EX (Execute)**: Performs ALU operations, calculates addresses
4. **MEM (Memory Access)**: Loads from or stores to data memory
5. **WB (Write Back)**: Writes results back to register file

## 📊 Performance Results Summary

### Testcase Results

| Testcase | Architecture | Cycles | Instructions | CPI | IPC |
|----------|-------------|--------|--------------|-----|-----|
| TC0 | Single-Stage | 7 | 6 | 1.167 | 0.857 |
| TC0 | Five-Stage | 11 | 6 | 1.833 | 0.545 |
| TC1 | Single-Stage | 40 | 39 | 1.026 | 0.975 |
| TC1 | Five-Stage | 46 | 39 | 1.179 | 0.848 |
| TC2 | Single-Stage | 36 | 35 | 1.029 | 0.972 |
| TC2 | Five-Stage | 53 | 35 | 1.514 | 0.660 |

### Key Findings

- **Five-stage is 3-4x faster** (due to shorter clock cycle)
- CPI increases with hazards (1.18-1.83 vs 1.0)
- Clock frequency advantage (3.64x) dominates CPI disadvantage
- **Speedup formula:** Speedup = (CPI_SS / CPI_FS) × (T_clock_SS / T_clock_FS) ≈ 3.1x

## Adding New Test Cases

To add a new test case:

1. Create a new directory in `code/input/` (e.g., `testcase3/`)
2. Add the required files:
   - `imem.txt`: Instruction memory
   - `dmem.txt`: Data memory
   - (Optional) `code.asm`: Assembly code for reference
3. Optionally add expected outputs in `code/sample_output/testcase3/`
4. Run `make run-all` or `make clean-run` - the new test case will be automatically discovered and executed

## Register File

- **32 registers**: x0 through x31
- **x0 (zero register)**: Always contains 0, writes to x0 are ignored
- **Initial state**: All registers start at 0

## HALT Instruction

The simulator stops execution when:
- A HALT instruction (opcode 0x7F) is encountered
- The PC moves beyond the instruction memory bounds
- Maximum cycle limit is reached (safety guard: 100,000 cycles)

## Performance Metrics

The simulator automatically tracks and reports performance metrics for both cores. Metrics are printed to the console and saved to `PerformanceMetrics.txt` in the results directory.

### Metrics Tracked:
- **Total Execution Cycles**: Total number of clock cycles executed
- **Total Instructions Retired**: Total number of instructions that completed execution
- **Average CPI (Cycles Per Instruction)**: Average number of cycles per instruction = Total Cycles / Total Instructions
- **IPC (Instructions Per Cycle)**: Average number of instructions completed per cycle = Total Instructions / Total Cycles

### How It Works:

**Single-Stage Core:**
- Instructions are counted when they complete execution (in the `step()` method)
- Each instruction takes exactly 1 cycle to execute (CPI = 1.0 for ideal case)
- Actual CPI may be > 1.0 due to HALT instruction requiring extra cycles

**Five-Stage Pipeline Core:**
- Instructions are counted when they complete the WB stage (retirement)
- Ideal CPI = 1.0 when pipeline is full
- Actual CPI > 1.0 due to:
  - Pipeline fill (first few cycles)
  - Pipeline drain (last few cycles)
  - Stalls (load-use hazards)
  - Branch mispredictions (1 cycle penalty per taken branch)

### Example Output:

```
======================================================================
PERFORMANCE METRICS
======================================================================

Performance of Single Stage:
  Total Execution Cycles: 7
  Total Instructions Retired: 6
  Average CPI (Cycles Per Instruction): 1.166667
  IPC (Instructions Per Cycle): 0.857143

Performance of Five Stage:
  Total Execution Cycles: 13
  Total Instructions Retired: 8
  Average CPI (Cycles Per Instruction): 1.625000
  IPC (Instructions Per Cycle): 0.615385

======================================================================
```

The metrics are also saved to `results/<testcase>/PerformanceMetrics.txt` in a format matching the sample outputs.

## Troubleshooting

### Infinite Loop
If a test case runs for 100,000 cycles, it likely indicates:
- Missing or incorrect HALT instruction
- Incorrect branch logic causing infinite loops
- Register values not updating correctly

### Output Mismatches
If outputs don't match sample outputs:
- Check instruction encoding and immediate extraction
- Verify forwarding paths are working correctly
- Ensure pipeline stalls are inserted correctly for load-use hazards
- Verify branch target calculations

### Common Issues
- **Sign extension errors**: Check that negative immediates are properly sign-extended
- **Memory alignment**: Ensure addresses are properly aligned for word accesses
- **Register x0**: Remember that x0 is always 0 and cannot be written

## Implementation Details

### Single-Stage Core
- Executes one instruction per cycle
- All stages (fetch, decode, execute, memory, writeback) happen in the same cycle
- Simple and easy to verify correctness

### Five-Stage Pipeline Core
- Instructions flow through pipeline stages
- Pipeline bubbles (NOPs) are inserted for hazards
- Forwarding minimizes stalls for data dependencies
- Branches are resolved in ID stage with 1-cycle penalty if taken

## License

This is an educational project for computer architecture coursework.

---

## 🎨 Generating Schematic Diagrams

### For Task 1 & Task 2 Diagrams:

1. Open `mermaid_diagrams.md`
2. Copy the Mermaid code for Task 1 or Task 2
3. Go to https://mermaid.live/
4. Paste and render the diagram
5. Export as PNG:
   - Task 1 → Save as `figure1.png`
   - Task 2 → Save as `figure2.png`
6. Place PNG files in project root (same directory as LaTeX files)
7. Compile `submission.latex`

**Alternative:** Use Mermaid CLI:
```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i mermaid_diagrams.md -o diagrams.png
```

---

## 🧪 Testing & Verification

### All Testcases Pass:
- ✅ testcase0: Memory outputs match, Performance metrics correct
- ✅ testcase1: Memory outputs match, Performance metrics correct  
- ✅ testcase2: Memory outputs match (53 cycles, expected behavior)

### Verification Commands:
```bash
# Run and compare
make clean-run
make compare-all

# Should see:
[OK] FS_DMEMResult.txt
[OK] FS_RFResult.txt
[OK] PerformanceMetrics.txt
[OK] SS_DMEMResult.txt
```

---

## 📝 Author

**Nidhish Gautam** (ng3483)  
RISC-V Processor Simulator Implementation  
ECE GY 6913 - Computing Systems Architecture


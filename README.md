# RISC-V Processor Simulator

This project implements cycle-accurate simulators of a 32-bit RISC-V processor in Python. The simulators support both single-stage and five-stage pipelined processor implementations with hazard handling.

## Documentation

- **[Single-Stage Processor Schematic](SINGLE_STAGE_SCHEMATIC.md)**: Detailed schematic, architecture, and code mapping for the single-stage processor
- **[Five-Stage Pipeline Processor Schematic](FIVE_STAGE_SCHEMATIC.md)**: Detailed schematic, forwarding paths, hazard handling, and code mapping for the five-stage pipelined processor
- **[Performance Comparison Analysis](PERFORMANCE_COMPARISON.md)**: Comprehensive comparison of single-stage vs five-stage pipeline performance, including when each is better
- **[Performance Optimizations](OPTIMIZATIONS.md)**: Detailed analysis of optimizations and features that can be added to improve performance (branch prediction, caches, out-of-order execution, etc.)

## Project Overview

The simulator implements a subset of the RISC-V RV32I instruction set architecture and provides two processor implementations:

1. **Single-Stage Core (SS)**: A functional single-cycle processor that executes one instruction per cycle
2. **Five-Stage Pipeline Core (FS)**: A pipelined processor with five stages (IF, ID, EX, MEM, WB) that handles data hazards through forwarding and stalling

## Features

### Supported Instructions

- **R-type**: ADD, SUB, XOR, OR, AND
- **I-type**: ADDI, XORI, ORI, ANDI, LW (Load Word)
- **S-type**: SW (Store Word)
- **B-type**: BEQ (Branch if Equal), BNE (Branch if Not Equal)
- **J-type**: JAL (Jump and Link)
- **HALT**: Special instruction to stop execution

### Hazard Handling (Five-Stage Pipeline)

- **RAW Hazards**: Handled using forwarding from MEM→EX, WB→EX, and EX→ID stages
- **Load-Use Hazards**: Detected and handled by stalling the pipeline
- **Control Hazards**: Branches are resolved in ID stage with "not taken" prediction

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

## Forwarding Paths

The five-stage pipeline implements forwarding to resolve RAW hazards:

- **EX→ID**: For branch resolution (computes ALU result early)
- **MEM→EX**: Forward ALU result from MEM stage to EX stage
- **WB→EX**: Forward result from WB stage to EX stage
- **MEM→ID**: Forward ALU result from MEM stage to ID stage (for branches)
- **WB→ID**: Forward result from WB stage to ID stage (for branches)

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

## Author

RISC-V Processor Simulator Implementation


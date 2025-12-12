# Mermaid Diagrams for RISC-V Simulator Report

## Instructions:
1. Copy the Mermaid code below
2. Go to https://mermaid.live/ or use Mermaid CLI
3. Paste the code and render
4. Export as PNG or PDF
5. Save as the filename specified below
6. Place in the same directory as submission.latex

---

## TASK 1 DIAGRAM: Single-Stage Processor Schematic (20 points)
**Save as: `figure1.png`**
**Task Requirement:** Draw the schematic for a single stage processor and fill in your code to run the simulator.

```mermaid
graph TB
    %% Main Components
    PC[PC Register]
    IMEM[Instruction Memory]
    RF[Register File]
    ALU[ALU]
    DMEM[Data Memory]
    CTRL[Control Unit]
    IMMGEN[Immediate Generator]
    
    %% Multiplexers
    MUX1[MUX ALU Src]
    MUX2[MUX Write Back]
    MUX3[MUX Next PC]
    
    %% PC Logic
    PCPLUS4[PC + 4]
    BRANCHCALC[Branch Target]
    JALTARGET[JAL Target]
    BRANCHCMP[Branch Compare]
    
    %% Main Datapath
    PC -->|address| IMEM
    IMEM -->|instruction| CTRL
    
    %% Control signals
    CTRL -->|rs1| RF
    CTRL -->|rs2| RF
    CTRL -->|rd| RF
    
    %% Immediate generation
    IMEM -->|instruction| IMMGEN
    IMMGEN -->|immediate| MUX1
    IMMGEN -->|imm_b| BRANCHCALC
    IMMGEN -->|imm_j| JALTARGET
    
    %% Register file datapath
    RF -->|read_data1| ALU
    RF -->|read_data1| BRANCHCMP
    RF -->|read_data2| MUX1
    RF -->|read_data2| BRANCHCMP
    RF -->|read_data2| DMEM
    
    %% ALU datapath
    MUX1 -->|operand2| ALU
    ALU -->|result| DMEM
    ALU -->|result| MUX2
    
    %% Memory datapath
    DMEM -->|read_data| MUX2
    
    %% Write back
    MUX2 -->|write_data| RF
    
    %% PC update
    PC --> PCPLUS4
    PC --> BRANCHCALC
    PC --> JALTARGET
    
    PCPLUS4 --> MUX3
    BRANCHCALC --> MUX3
    JALTARGET --> MUX3
    BRANCHCMP -.->|branch_taken| MUX3
    
    MUX3 -->|next_pc| PC
    
    %% Styling
    classDef memoryStyle fill:#e1f5ff,stroke:#333,stroke-width:2px
    classDef computeStyle fill:#fff4e1,stroke:#333,stroke-width:2px
    classDef controlStyle fill:#ffe1e1,stroke:#333,stroke-width:2px
    classDef muxStyle fill:#e1ffe1,stroke:#333,stroke-width:2px
    
    class IMEM,DMEM,RF memoryStyle
    class ALU,BRANCHCMP,PCPLUS4,BRANCHCALC,JALTARGET computeStyle
    class CTRL,IMMGEN controlStyle
    class MUX1,MUX2,MUX3 muxStyle
```

---

## TASK 2 DIAGRAM: Five-Stage Pipelined Processor Schematic (20 points)
**Save as: `figure2.png`**
**Task Requirement:** Draw the schematic for a five stage pipelined processor with RAW and control hazard handling (stalling + forwarding).

```mermaid
graph TB
    %% IF Stage
    subgraph IF[" IF Stage "]
        PC[PC]
        IMEM[Instruction Memory]
        PCMUX[PC MUX]
    end
    
    %% Pipeline Register IF/ID
    IFID[IF/ID Register<br/>nop, PC, Instr]
    
    %% ID Stage
    subgraph ID[" ID Stage "]
        DECODE[Decode Unit]
        RF[Register File]
        IMMGEN[Immediate Gen]
        HAZARD[Hazard Detection]
        BRANCH[Branch Logic]
    end
    
    %% Pipeline Register ID/EX
    IDEX[ID/EX Register<br/>nop, PC, Rs1/Rs2 data<br/>Imm, Control Signals]
    
    %% EX Stage
    subgraph EX[" EX Stage "]
        FORWARD[Forwarding Unit]
        ALU[ALU]
        ALUMUX[ALU MUX]
    end
    
    %% Pipeline Register EX/MEM
    EXMEM[EX/MEM Register<br/>nop, ALU Result<br/>Store Data, Control]
    
    %% MEM Stage
    subgraph MEM[" MEM Stage "]
        DMEM[Data Memory]
    end
    
    %% Pipeline Register MEM/WB
    MEMWB[MEM/WB Register<br/>nop, ALU Result<br/>Load Data, Control]
    
    %% WB Stage
    subgraph WB[" WB Stage "]
        WBMUX[WB MUX]
    end
    
    %% Main Flow
    PC --> IMEM
    IMEM --> IFID
    IFID --> DECODE
    DECODE --> RF
    DECODE --> IMMGEN
    DECODE --> HAZARD
    DECODE --> BRANCH
    RF --> IDEX
    IMMGEN --> IDEX
    
    IDEX --> FORWARD
    IDEX --> ALUMUX
    FORWARD -.->|Forwarded Data| ALUMUX
    ALUMUX --> ALU
    ALU --> EXMEM
    
    EXMEM --> DMEM
    DMEM --> MEMWB
    
    MEMWB --> WBMUX
    WBMUX --> RF
    
    %% Forwarding Paths
    EXMEM -.->|Forward to EX| FORWARD
    MEMWB -.->|Forward to EX| FORWARD
    EXMEM -.->|Forward to ID| BRANCH
    MEMWB -.->|Forward to ID| BRANCH
    
    %% Branch Control
    BRANCH -.->|Redirect| PCMUX
    BRANCH -.->|Flush| IFID
    
    %% Hazard Control
    HAZARD -.->|Stall| IFID
    HAZARD -.->|Bubble| IDEX
    
    %% PC Update
    PCMUX --> PC
    
    %% Styling
    classDef stageStyle fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef regStyle fill:#fff3e0,stroke:#f57c00,stroke-width:3px
    classDef controlStyle fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    
    class IF,ID,EX,MEM,WB stageStyle
    class IFID,IDEX,EXMEM,MEMWB regStyle
    class HAZARD,FORWARD,BRANCH controlStyle
```

---

## Alternative: Simpler Five-Stage Diagram
**If the above is too complex, use this simplified version:**

```mermaid
graph LR
    %% Stages
    IF[IF<br/>Instruction<br/>Fetch]
    ID[ID<br/>Decode &<br/>Reg Read]
    EX[EX<br/>Execute]
    MEM[MEM<br/>Memory]
    WB[WB<br/>Write<br/>Back]
    
    %% Pipeline Registers
    IF --> |IF/ID| ID
    ID --> |ID/EX| EX
    EX --> |EX/MEM| MEM
    MEM --> |MEM/WB| WB
    
    %% Forwarding
    EX -.->|Forward| EX
    MEM -.->|Forward| EX
    WB -.->|Forward| EX
    
    EX -.->|Forward| ID
    MEM -.->|Forward| ID
    
    %% Branch Control
    ID -.->|Branch<br/>Redirect| IF
    
    %% Write Back
    WB --> |Write| ID
    
    %% Styling
    classDef stageStyle fill:#bbdefb,stroke:#1976d2,stroke-width:3px
    class IF,ID,EX,MEM,WB stageStyle
```

---

## How to Render:

### Option 1: Online (Easiest)
1. Go to https://mermaid.live/
2. Copy one of the code blocks above
3. Paste into the editor
4. Adjust colors/layout if needed
5. Click "Actions" → "PNG" or "SVG" to download
6. Save with the specified filename

### Option 2: VS Code
1. Install "Markdown Preview Mermaid Support" extension
2. Create a .md file with the mermaid code
3. Preview and take screenshot
4. Or use Mermaid CLI to export

### Option 3: Command Line (Mermaid CLI)
```bash
npm install -g @mermaid-js/mermaid-cli
mmdc -i mermaid_diagrams.md -o single_stage_schematic.png
```

### Recommended Settings:
- **Format:** PNG or PDF
- **Width:** 1200-1600 pixels for PNG
- **Background:** White
- **Scale:** 2x for high resolution

---

## Notes:
- The diagrams use different colors to distinguish component types
- Solid arrows = data flow
- Dashed arrows = control signals / forwarding
- Pipeline registers are shown as separate blocks in the pipelined diagram


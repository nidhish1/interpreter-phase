# Simple helpers to run simulator and compare against sample outputs

# You can override PYTHON on the command line:
#   make run TESTCASE=testcase1 PYTHON=./venv/bin/python
PYTHON ?= python3

# Testcase to use (testcase0 | testcase1 | testcase2)
TESTCASE ?= testcase0

# Paths
ROOT_DIR := $(abspath .)
CODE_DIR := $(abspath code)
INPUT_DIR := $(CODE_DIR)/input/$(TESTCASE)
# Simulator writes to ./results by default (see main.py)
RESULTS_DIR := $(ROOT_DIR)/results/$(TESTCASE)
SAMPLE_DIR := $(CODE_DIR)/sample_output/$(TESTCASE)

.PHONY: help run run-all compare compare-all clean-results clean-run

help:
	@echo "Targets:"
	@echo "  make run TESTCASE=testcase0 [PYTHON=...]     # Run simulator for a testcase"
	@echo "  make run-all [PYTHON=...]                     # Run simulator for all testcases"
	@echo "  make compare TESTCASE=testcase0 [PYTHON=...] # Compare results vs sample_output"
	@echo "  make compare-all [PYTHON=...]                # Compare for testcase0..2"
	@echo "  make clean-results                           # Remove generated results"
	@echo "  make clean-run [PYTHON=...]                  # Clean and run all testcases"

run:
	@echo "Running simulator for $(INPUT_DIR) -> $(RESULTS_DIR)"
	$(PYTHON) $(CODE_DIR)/main.py --iodir $(INPUT_DIR)
	@echo "Done. Results in: $(RESULTS_DIR)"

compare:
	@echo "Comparing results $(RESULTS_DIR) vs sample $(SAMPLE_DIR)"
	$(PYTHON) $(CODE_DIR)/compare_outputs.py \
	  --results-dir $(RESULTS_DIR) \
	  --sample-dir $(SAMPLE_DIR)

# Automatically discover all testcases from input directory
TESTCASES := $(shell find $(CODE_DIR)/input -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort)

run-all:
	@echo "Running simulator for all testcases: $(TESTCASES)"
	@for testcase in $(TESTCASES); do \
		$(MAKE) run TESTCASE=$$testcase PYTHON="$(PYTHON)"; \
	done

compare-all:
	@echo "Comparing results for all testcases: $(TESTCASES)"
	@for testcase in $(TESTCASES); do \
		$(MAKE) compare TESTCASE=$$testcase PYTHON="$(PYTHON)"; \
	done

clean-results:
	@echo "Removing $(ROOT_DIR)/results and $(CODE_DIR)/results (if present)"
	rm -rf $(ROOT_DIR)/results
	rm -rf $(CODE_DIR)/results
	@echo "Done."

clean-run: clean-results run-all



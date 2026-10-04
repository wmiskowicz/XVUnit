// The testbench module name must match its file name (counter_tb.sv).
`include "xvunit_defines.svh"

module counter_tb;

  localparam int WIDTH = 4;

  logic             clk = 1'b0;
  logic             rst;
  logic             en;
  logic [WIDTH-1:0] count;

  always #5ns clk = ~clk;

  counter #(.WIDTH(WIDTH)) dut (.*);

  `TEST_SUITE_BEGIN

    `TEST_CASE_SETUP begin
      en  = 1'b0;
      rst = 1'b1;
      repeat (2) @(negedge clk);
      rst = 1'b0;
    end

    `TEST_CASE("resets_to_zero") begin
      `CHECK_EQUAL(count, 0);
    end

    `TEST_CASE("holds_when_disabled") begin
      repeat (5) @(negedge clk);
      `CHECK_EQUAL(count, 0);
    end

    `TEST_CASE("counts_up") begin
      en = 1'b1;
      repeat (3) @(negedge clk);
      `CHECK_EQUAL(count, 3);
    end

    `TEST_CASE("wraps_around") begin
      en = 1'b1;
      repeat (2**WIDTH + 1) @(negedge clk);
      `CHECK_EQUAL(count, 1, "counter should wrap to 0 after its max value");
    end

  `TEST_SUITE_END

  `WATCHDOG(10us);

endmodule

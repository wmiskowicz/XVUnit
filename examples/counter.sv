// Simple up-counter with synchronous reset and enable.
module counter #(
  parameter int WIDTH = 4
) (
  input  logic             clk,
  input  logic             rst,
  input  logic             en,
  output logic [WIDTH-1:0] count
);

  always_ff @(posedge clk) begin
    if (rst)     count <= '0;
    else if (en) count <= count + 1'b1;
  end

endmodule

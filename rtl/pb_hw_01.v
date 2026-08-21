`timescale 1ns/1ps

module pb_hw01_raw_pipeline(
    input wire clk,
    input wire rst,
    input wire in_valid,
    input wire in_tag,
    input wire [1:0] in_state,
    input wire [7:0] in_action,
    input wire [7:0] expected_action,
    input wire [7:0] in_authority,
    input wire [7:0] current_authority,
    input wire [7:0] in_epoch,
    input wire [7:0] current_epoch,
    input wire [15:0] in_nonce,
    input wire [7:0] in_provenance,
    input wire [7:0] in_context,
    input wire [7:0] current_context,
    output reg out_valid,
    output reg out_allow
);
    reg s0_valid;
    reg [1:0] s0_state;

    always @(posedge clk) begin
        if (rst) begin
            s0_valid <= 1'b0;
            s0_state <= 2'b00;
            out_valid <= 1'b0;
            out_allow <= 1'b0;
        end else begin
            out_valid <= s0_valid;
            out_allow <= s0_valid && (s0_state == 2'b01);
            s0_valid <= in_valid;
            s0_state <= in_state;
        end
    end
endmodule


module pb_hw01_capability_pipeline(
    input wire clk,
    input wire rst,
    input wire in_valid,
    input wire in_tag,
    input wire [1:0] in_state,
    input wire [7:0] in_action,
    input wire [7:0] expected_action,
    input wire [7:0] in_authority,
    input wire [7:0] current_authority,
    input wire [7:0] in_epoch,
    input wire [7:0] current_epoch,
    input wire [15:0] in_nonce,
    input wire [7:0] in_provenance,
    input wire [7:0] in_context,
    input wire [7:0] current_context,
    output reg out_valid,
    output reg out_allow
);
    localparam REPLAY_ENTRIES = 8;

    reg s0_valid;
    reg s0_tag;
    reg [1:0] s0_state;
    reg [7:0] s0_action;
    reg [7:0] s0_expected_action;
    reg [7:0] s0_authority;
    reg [7:0] s0_current_authority;
    reg [7:0] s0_epoch;
    reg [7:0] s0_current_epoch;
    reg [15:0] s0_nonce;
    reg [7:0] s0_provenance;
    reg [7:0] s0_context;
    reg [7:0] s0_current_context;

    reg [15:0] replay_nonce [0:REPLAY_ENTRIES-1];
    reg replay_valid [0:REPLAY_ENTRIES-1];
    reg [2:0] replay_ptr;
    reg replay_hit;
    integer i;

    always @* begin
        replay_hit = 1'b0;
        for (i = 0; i < REPLAY_ENTRIES; i = i + 1) begin
            if (replay_valid[i] && replay_nonce[i] == s0_nonce)
                replay_hit = 1'b1;
        end
    end

    always @(posedge clk) begin
        if (rst) begin
            s0_valid <= 1'b0;
            out_valid <= 1'b0;
            out_allow <= 1'b0;
            replay_ptr <= 3'b000;
            for (i = 0; i < REPLAY_ENTRIES; i = i + 1) begin
                replay_valid[i] <= 1'b0;
                replay_nonce[i] <= 16'b0;
            end
        end else begin
            out_valid <= s0_valid;
            out_allow <= 1'b0;

            if (
                s0_valid &&
                s0_tag &&
                s0_state == 2'b01 &&
                s0_action == s0_expected_action &&
                s0_authority == s0_current_authority &&
                s0_epoch == s0_current_epoch &&
                s0_provenance != 8'b0 &&
                s0_context == s0_current_context &&
                !replay_hit
            ) begin
                out_allow <= 1'b1;
                replay_valid[replay_ptr] <= 1'b1;
                replay_nonce[replay_ptr] <= s0_nonce;
                replay_ptr <= replay_ptr + 3'b001;
            end

            s0_valid <= in_valid;
            s0_tag <= in_tag;
            s0_state <= in_state;
            s0_action <= in_action;
            s0_expected_action <= expected_action;
            s0_authority <= in_authority;
            s0_current_authority <= current_authority;
            s0_epoch <= in_epoch;
            s0_current_epoch <= current_epoch;
            s0_nonce <= in_nonce;
            s0_provenance <= in_provenance;
            s0_context <= in_context;
            s0_current_context <= current_context;
        end
    end
endmodule


module pb_hw01_proofbit_pipeline(
    input wire clk,
    input wire rst,
    input wire in_valid,
    input wire in_tag,
    input wire [1:0] in_state,
    input wire [7:0] in_action,
    input wire [7:0] expected_action,
    input wire [7:0] in_authority,
    input wire [7:0] current_authority,
    input wire [7:0] in_epoch,
    input wire [7:0] current_epoch,
    input wire [15:0] in_nonce,
    input wire [7:0] in_provenance,
    input wire [7:0] in_context,
    input wire [7:0] current_context,
    output reg out_valid,
    output reg out_allow
);
    localparam REPLAY_ENTRIES = 8;

    // ProofBit names the same physical checks as:
    // proof tag, epistemic state, statement binding, authority, epoch,
    // proof-id replay, provenance, and execution-context binding.
    reg s0_valid;
    reg s0_tag;
    reg [1:0] s0_state;
    reg [7:0] s0_action;
    reg [7:0] s0_expected_action;
    reg [7:0] s0_authority;
    reg [7:0] s0_current_authority;
    reg [7:0] s0_epoch;
    reg [7:0] s0_current_epoch;
    reg [15:0] s0_nonce;
    reg [7:0] s0_provenance;
    reg [7:0] s0_context;
    reg [7:0] s0_current_context;

    reg [15:0] replay_nonce [0:REPLAY_ENTRIES-1];
    reg replay_valid [0:REPLAY_ENTRIES-1];
    reg [2:0] replay_ptr;
    reg replay_hit;
    integer i;

    always @* begin
        replay_hit = 1'b0;
        for (i = 0; i < REPLAY_ENTRIES; i = i + 1) begin
            if (replay_valid[i] && replay_nonce[i] == s0_nonce)
                replay_hit = 1'b1;
        end
    end

    always @(posedge clk) begin
        if (rst) begin
            s0_valid <= 1'b0;
            out_valid <= 1'b0;
            out_allow <= 1'b0;
            replay_ptr <= 3'b000;
            for (i = 0; i < REPLAY_ENTRIES; i = i + 1) begin
                replay_valid[i] <= 1'b0;
                replay_nonce[i] <= 16'b0;
            end
        end else begin
            out_valid <= s0_valid;
            out_allow <= 1'b0;

            if (
                s0_valid &&
                s0_tag &&
                s0_state == 2'b01 &&
                s0_action == s0_expected_action &&
                s0_authority == s0_current_authority &&
                s0_epoch == s0_current_epoch &&
                s0_provenance != 8'b0 &&
                s0_context == s0_current_context &&
                !replay_hit
            ) begin
                out_allow <= 1'b1;
                replay_valid[replay_ptr] <= 1'b1;
                replay_nonce[replay_ptr] <= s0_nonce;
                replay_ptr <= replay_ptr + 3'b001;
            end

            s0_valid <= in_valid;
            s0_tag <= in_tag;
            s0_state <= in_state;
            s0_action <= in_action;
            s0_expected_action <= expected_action;
            s0_authority <= in_authority;
            s0_current_authority <= current_authority;
            s0_epoch <= in_epoch;
            s0_current_epoch <= current_epoch;
            s0_nonce <= in_nonce;
            s0_provenance <= in_provenance;
            s0_context <= in_context;
            s0_current_context <= current_context;
        end
    end
endmodule

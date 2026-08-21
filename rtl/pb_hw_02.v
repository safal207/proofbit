`timescale 1ns/1ps

// PB-HW-02: semantic cost curve.
//
// The minimal capability pipeline enforces only the frozen base authorization
// contract: tag, action, authority, epoch freshness and consume-once replay.
// It deliberately does not claim epistemic-state, provenance, execution-context
// or terminal-outcome coverage.
module pb_hw02_min_cap_pipeline(
    input  wire        clk,
    input  wire        reset,
    input  wire        in_valid,
    input  wire        in_tag,
    input  wire [7:0]  in_action,
    input  wire [7:0]  in_authority,
    input  wire [7:0]  in_epoch,
    input  wire [15:0] in_nonce,
    input  wire [7:0]  expected_action,
    input  wire [7:0]  expected_authority,
    input  wire [7:0]  current_epoch,
    output reg         dispatch_valid,
    output reg         dispatch_allowed
);
    reg        v_q;
    reg        tag_q;
    reg [7:0]  action_q;
    reg [7:0]  authority_q;
    reg [7:0]  epoch_q;
    reg [15:0] nonce_q;
    reg [7:0]  expected_action_q;
    reg [7:0]  expected_authority_q;
    reg [7:0]  current_epoch_q;

    reg [15:0] replay_nonce [0:7];
    reg [7:0]  replay_valid;
    reg [2:0]  replay_ptr;
    integer i;
    reg replay_hit;

    always @* begin
        replay_hit = 1'b0;
        for (i = 0; i < 8; i = i + 1)
            if (replay_valid[i] && replay_nonce[i] == nonce_q)
                replay_hit = 1'b1;
    end

    wire auth_ok = v_q && tag_q &&
                   (action_q == expected_action_q) &&
                   (authority_q == expected_authority_q) &&
                   (epoch_q == current_epoch_q) &&
                   !replay_hit;

    always @(posedge clk) begin
        if (reset) begin
            v_q <= 1'b0;
            dispatch_valid <= 1'b0;
            dispatch_allowed <= 1'b0;
            replay_valid <= 8'b0;
            replay_ptr <= 3'b0;
        end else begin
            dispatch_valid <= v_q;
            dispatch_allowed <= auth_ok;
            if (auth_ok) begin
                replay_nonce[replay_ptr] <= nonce_q;
                replay_valid[replay_ptr] <= 1'b1;
                replay_ptr <= replay_ptr + 3'd1;
            end

            v_q <= in_valid;
            tag_q <= in_tag;
            action_q <= in_action;
            authority_q <= in_authority;
            epoch_q <= in_epoch;
            nonce_q <= in_nonce;
            expected_action_q <= expected_action;
            expected_authority_q <= expected_authority;
            current_epoch_q <= current_epoch;
        end
    end
endmodule


// One strongest-conventional/full-evidence physical core.  PB-HW-02 uses this
// same compact representation for the conventional and ProofBit wrappers so
// any generic full-evidence enforcement cost is not falsely credited to the
// ProofBit label.
//
// kind=0 AUTHORIZATION
// kind=1 OUTCOME
// state encoding: 00 UNKNOWN, 01 PROVEN_TRUE, 10 PROVEN_FALSE, 11 CONFLICT.
module pb_hw02_full_evidence_core(
    input  wire        clk,
    input  wire        reset,
    input  wire        in_valid,
    input  wire        in_kind,
    input  wire        in_tag,
    input  wire [1:0]  in_state,
    input  wire [7:0]  in_statement,
    input  wire [7:0]  in_authority,
    input  wire [7:0]  in_epoch,
    input  wire [15:0] in_identity,
    input  wire [7:0]  in_provenance,
    input  wire [7:0]  in_context,
    input  wire [7:0]  expected_statement,
    input  wire [7:0]  expected_authority,
    input  wire [7:0]  current_epoch,
    input  wire [7:0]  current_context,
    output reg         dispatch_valid,
    output reg         dispatch_allowed,
    output reg         terminal_valid,
    output reg         terminal_success
);
    localparam [1:0] PROVEN_TRUE = 2'b01;

    reg        v_q;
    reg        kind_q;
    reg        tag_q;
    reg [1:0]  state_q;
    reg [7:0]  statement_q;
    reg [7:0]  authority_q;
    reg [7:0]  epoch_q;
    reg [15:0] identity_q;
    reg [7:0]  provenance_q;
    reg [7:0]  context_q;
    reg [7:0]  expected_statement_q;
    reg [7:0]  expected_authority_q;
    reg [7:0]  current_epoch_q;
    reg [7:0]  current_context_q;

    reg [15:0] replay_identity [0:7];
    reg [7:0]  replay_valid;
    reg [2:0]  replay_ptr;

    reg [15:0] pending_identity [0:7];
    reg [7:0]  pending_valid;
    reg [2:0]  pending_ptr;

    integer i;
    reg replay_hit;
    reg pending_hit;
    reg [2:0] pending_hit_index;

    always @* begin
        replay_hit = 1'b0;
        pending_hit = 1'b0;
        pending_hit_index = 3'b0;
        for (i = 0; i < 8; i = i + 1) begin
            if (replay_valid[i] && replay_identity[i] == identity_q)
                replay_hit = 1'b1;
            if (pending_valid[i] && pending_identity[i] == identity_q) begin
                pending_hit = 1'b1;
                pending_hit_index = i[2:0];
            end
        end
    end

    wire common_ok = v_q && tag_q &&
                     (state_q == PROVEN_TRUE) &&
                     (statement_q == expected_statement_q) &&
                     (authority_q == expected_authority_q) &&
                     (epoch_q == current_epoch_q) &&
                     (provenance_q != 8'b0) &&
                     (context_q == current_context_q);

    wire auth_ok = common_ok && !kind_q && !replay_hit;
    wire outcome_ok = common_ok && kind_q && pending_hit;

    always @(posedge clk) begin
        if (reset) begin
            v_q <= 1'b0;
            dispatch_valid <= 1'b0;
            dispatch_allowed <= 1'b0;
            terminal_valid <= 1'b0;
            terminal_success <= 1'b0;
            replay_valid <= 8'b0;
            replay_ptr <= 3'b0;
            pending_valid <= 8'b0;
            pending_ptr <= 3'b0;
        end else begin
            dispatch_valid <= v_q && !kind_q;
            dispatch_allowed <= auth_ok;
            terminal_valid <= v_q && kind_q;
            terminal_success <= outcome_ok;

            if (auth_ok) begin
                replay_identity[replay_ptr] <= identity_q;
                replay_valid[replay_ptr] <= 1'b1;
                replay_ptr <= replay_ptr + 3'd1;

                pending_identity[pending_ptr] <= identity_q;
                pending_valid[pending_ptr] <= 1'b1;
                pending_ptr <= pending_ptr + 3'd1;
            end
            if (outcome_ok)
                pending_valid[pending_hit_index] <= 1'b0;

            v_q <= in_valid;
            kind_q <= in_kind;
            tag_q <= in_tag;
            state_q <= in_state;
            statement_q <= in_statement;
            authority_q <= in_authority;
            epoch_q <= in_epoch;
            identity_q <= in_identity;
            provenance_q <= in_provenance;
            context_q <= in_context;
            expected_statement_q <= expected_statement;
            expected_authority_q <= expected_authority;
            current_epoch_q <= current_epoch;
            current_context_q <= current_context;
        end
    end
endmodule


module pb_hw02_full_conventional_pipeline(
    input wire clk, reset, in_valid, in_kind, in_tag,
    input wire [1:0] in_state,
    input wire [7:0] in_statement, in_authority, in_epoch,
    input wire [15:0] in_identity,
    input wire [7:0] in_provenance, in_context,
    input wire [7:0] expected_statement, expected_authority, current_epoch, current_context,
    output wire dispatch_valid, dispatch_allowed, terminal_valid, terminal_success
);
    pb_hw02_full_evidence_core core(
        .clk(clk), .reset(reset), .in_valid(in_valid), .in_kind(in_kind), .in_tag(in_tag),
        .in_state(in_state), .in_statement(in_statement), .in_authority(in_authority),
        .in_epoch(in_epoch), .in_identity(in_identity), .in_provenance(in_provenance),
        .in_context(in_context), .expected_statement(expected_statement),
        .expected_authority(expected_authority), .current_epoch(current_epoch),
        .current_context(current_context), .dispatch_valid(dispatch_valid),
        .dispatch_allowed(dispatch_allowed), .terminal_valid(terminal_valid),
        .terminal_success(terminal_success)
    );
endmodule


module pb_hw02_rich_proofbit_pipeline(
    input wire clk, reset, in_valid, in_kind, in_tag,
    input wire [1:0] in_state,
    input wire [7:0] in_statement, in_authority, in_epoch,
    input wire [15:0] in_identity,
    input wire [7:0] in_provenance, in_context,
    input wire [7:0] expected_statement, expected_authority, current_epoch, current_context,
    output wire dispatch_valid, dispatch_allowed, terminal_valid, terminal_success
);
    pb_hw02_full_evidence_core core(
        .clk(clk), .reset(reset), .in_valid(in_valid), .in_kind(in_kind), .in_tag(in_tag),
        .in_state(in_state), .in_statement(in_statement), .in_authority(in_authority),
        .in_epoch(in_epoch), .in_identity(in_identity), .in_provenance(in_provenance),
        .in_context(in_context), .expected_statement(expected_statement),
        .expected_authority(expected_authority), .current_epoch(current_epoch),
        .current_context(current_context), .dispatch_valid(dispatch_valid),
        .dispatch_allowed(dispatch_allowed), .terminal_valid(terminal_valid),
        .terminal_success(terminal_success)
    );
endmodule

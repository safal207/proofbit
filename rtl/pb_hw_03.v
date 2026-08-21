`timescale 1ns/1ps

// PB-HW-03: composition / instruction-transaction economics.
//
// The benchmark deliberately contains a strong conventional anti-strawman:
// pb_hw03_vector_conventional and pb_hw03_proofbit_compose are wrappers over
// the same equally expressive 4-parent composition core. Any difference
// between those two wrappers after synthesis would therefore be a tooling or
// harness surprise, not a semantic advantage granted by construction.

module pb_hw03_scalar_conventional(
    input  wire        clk,
    input  wire        reset,
    input  wire        in_valid,
    input  wire [1:0]  in_kind,       // 0=PARENT, 1=COMPOSE, 2=OUTCOME
    input  wire [1:0]  in_slot,
    input  wire [1:0]  in_state,
    input  wire [7:0]  in_authority,
    input  wire [7:0]  in_epoch,
    input  wire [7:0]  in_identity,
    input  wire [7:0]  in_provenance,
    input  wire [7:0]  in_context,
    input  wire [7:0]  derived_statement,
    input  wire [7:0]  derived_identity,
    input  wire [7:0]  expected_statement,
    input  wire [7:0]  expected_authority,
    input  wire [7:0]  current_epoch,
    input  wire [7:0]  current_context,
    output reg         compose_valid,
    output reg         compose_allowed,
    output reg         terminal_valid,
    output reg         terminal_success
);
    localparam [1:0] PROVEN_TRUE = 2'b01;

    reg [7:0]  stage_state;
    reg [31:0] stage_authority;
    reg [31:0] stage_epoch;
    reg [31:0] stage_identity;
    reg [31:0] stage_provenance;
    reg [31:0] stage_context;
    reg [3:0]  stage_valid;

    // Exact 8-bit parent-identity replay set for this bounded reference model.
    reg [255:0] seen_parent;

    reg        auth_valid;
    reg [7:0]  auth_identity;
    reg [7:0]  auth_statement;
    reg        outcome_seen_valid;
    reg [7:0]  outcome_seen_identity;

    wire [7:0] id0 = stage_identity[7:0];
    wire [7:0] id1 = stage_identity[15:8];
    wire [7:0] id2 = stage_identity[23:16];
    wire [7:0] id3 = stage_identity[31:24];

    wire p0_good = stage_valid[0] &&
                   (stage_state[1:0] == PROVEN_TRUE) &&
                   (stage_authority[7:0] == expected_authority) &&
                   (stage_epoch[7:0] == current_epoch) &&
                   (stage_provenance[7:0] != 8'h00) &&
                   (stage_context[7:0] == current_context) &&
                   !seen_parent[id0];
    wire p1_good = stage_valid[1] &&
                   (stage_state[3:2] == PROVEN_TRUE) &&
                   (stage_authority[15:8] == expected_authority) &&
                   (stage_epoch[15:8] == current_epoch) &&
                   (stage_provenance[15:8] != 8'h00) &&
                   (stage_context[15:8] == current_context) &&
                   !seen_parent[id1];
    wire p2_good = stage_valid[2] &&
                   (stage_state[5:4] == PROVEN_TRUE) &&
                   (stage_authority[23:16] == expected_authority) &&
                   (stage_epoch[23:16] == current_epoch) &&
                   (stage_provenance[23:16] != 8'h00) &&
                   (stage_context[23:16] == current_context) &&
                   !seen_parent[id2];
    wire p3_good = stage_valid[3] &&
                   (stage_state[7:6] == PROVEN_TRUE) &&
                   (stage_authority[31:24] == expected_authority) &&
                   (stage_epoch[31:24] == current_epoch) &&
                   (stage_provenance[31:24] != 8'h00) &&
                   (stage_context[31:24] == current_context) &&
                   !seen_parent[id3];

    wire unique_ids = (id0 != id1) && (id0 != id2) && (id0 != id3) &&
                      (id1 != id2) && (id1 != id3) && (id2 != id3);

    wire compose_good = p0_good && p1_good && p2_good && p3_good &&
                        unique_ids && (derived_statement == expected_statement);

    wire outcome_good = auth_valid &&
                        (derived_identity == auth_identity) &&
                        (derived_statement == auth_statement) &&
                        (in_state == PROVEN_TRUE) &&
                        (in_authority == expected_authority) &&
                        (in_epoch == current_epoch) &&
                        (in_provenance != 8'h00) &&
                        (in_context == current_context) &&
                        !(outcome_seen_valid && outcome_seen_identity == derived_identity);

    always @(posedge clk) begin
        if (reset) begin
            stage_state <= 8'h00;
            stage_authority <= 32'h0;
            stage_epoch <= 32'h0;
            stage_identity <= 32'h0;
            stage_provenance <= 32'h0;
            stage_context <= 32'h0;
            stage_valid <= 4'b0000;
            seen_parent <= 256'h0;
            auth_valid <= 1'b0;
            auth_identity <= 8'h00;
            auth_statement <= 8'h00;
            outcome_seen_valid <= 1'b0;
            outcome_seen_identity <= 8'h00;
            compose_valid <= 1'b0;
            compose_allowed <= 1'b0;
            terminal_valid <= 1'b0;
            terminal_success <= 1'b0;
        end else begin
            compose_valid <= 1'b0;
            compose_allowed <= 1'b0;
            terminal_valid <= 1'b0;
            terminal_success <= 1'b0;

            if (in_valid) begin
                case (in_kind)
                    2'd0: begin
                        case (in_slot)
                            2'd0: begin
                                stage_state[1:0] <= in_state;
                                stage_authority[7:0] <= in_authority;
                                stage_epoch[7:0] <= in_epoch;
                                stage_identity[7:0] <= in_identity;
                                stage_provenance[7:0] <= in_provenance;
                                stage_context[7:0] <= in_context;
                                stage_valid[0] <= 1'b1;
                            end
                            2'd1: begin
                                stage_state[3:2] <= in_state;
                                stage_authority[15:8] <= in_authority;
                                stage_epoch[15:8] <= in_epoch;
                                stage_identity[15:8] <= in_identity;
                                stage_provenance[15:8] <= in_provenance;
                                stage_context[15:8] <= in_context;
                                stage_valid[1] <= 1'b1;
                            end
                            2'd2: begin
                                stage_state[5:4] <= in_state;
                                stage_authority[23:16] <= in_authority;
                                stage_epoch[23:16] <= in_epoch;
                                stage_identity[23:16] <= in_identity;
                                stage_provenance[23:16] <= in_provenance;
                                stage_context[23:16] <= in_context;
                                stage_valid[2] <= 1'b1;
                            end
                            default: begin
                                stage_state[7:6] <= in_state;
                                stage_authority[31:24] <= in_authority;
                                stage_epoch[31:24] <= in_epoch;
                                stage_identity[31:24] <= in_identity;
                                stage_provenance[31:24] <= in_provenance;
                                stage_context[31:24] <= in_context;
                                stage_valid[3] <= 1'b1;
                            end
                        endcase
                    end
                    2'd1: begin
                        compose_valid <= 1'b1;
                        compose_allowed <= compose_good;
                        auth_valid <= 1'b0;
                        stage_valid <= 4'b0000;
                        if (compose_good) begin
                            seen_parent[id0] <= 1'b1;
                            seen_parent[id1] <= 1'b1;
                            seen_parent[id2] <= 1'b1;
                            seen_parent[id3] <= 1'b1;
                            auth_valid <= 1'b1;
                            auth_identity <= derived_identity;
                            auth_statement <= derived_statement;
                        end
                    end
                    2'd2: begin
                        terminal_valid <= 1'b1;
                        terminal_success <= outcome_good;
                        if (outcome_good) begin
                            outcome_seen_valid <= 1'b1;
                            outcome_seen_identity <= derived_identity;
                        end
                        if (auth_valid && derived_identity == auth_identity)
                            auth_valid <= 1'b0;
                    end
                    default: begin end
                endcase
            end
        end
    end
endmodule


module pb_hw03_vector_core(
    input  wire        clk,
    input  wire        reset,
    input  wire        in_valid,
    input  wire        in_kind,       // 0=COMPOSE4, 1=OUTCOME
    input  wire [7:0]  in_state,      // four 2-bit parent states; lane0 used for outcome
    input  wire [31:0] in_authority,
    input  wire [31:0] in_epoch,
    input  wire [31:0] in_identity,
    input  wire [31:0] in_provenance,
    input  wire [31:0] in_context,
    input  wire [7:0]  derived_statement,
    input  wire [7:0]  derived_identity,
    input  wire [7:0]  expected_statement,
    input  wire [7:0]  expected_authority,
    input  wire [7:0]  current_epoch,
    input  wire [7:0]  current_context,
    output reg         compose_valid,
    output reg         compose_allowed,
    output reg         terminal_valid,
    output reg         terminal_success
);
    localparam [1:0] PROVEN_TRUE = 2'b01;

    reg [255:0] seen_parent;
    reg        auth_valid;
    reg [7:0]  auth_identity;
    reg [7:0]  auth_statement;
    reg        outcome_seen_valid;
    reg [7:0]  outcome_seen_identity;

    wire [7:0] id0 = in_identity[7:0];
    wire [7:0] id1 = in_identity[15:8];
    wire [7:0] id2 = in_identity[23:16];
    wire [7:0] id3 = in_identity[31:24];

    wire p0_good = (in_state[1:0] == PROVEN_TRUE) &&
                   (in_authority[7:0] == expected_authority) &&
                   (in_epoch[7:0] == current_epoch) &&
                   (in_provenance[7:0] != 8'h00) &&
                   (in_context[7:0] == current_context) &&
                   !seen_parent[id0];
    wire p1_good = (in_state[3:2] == PROVEN_TRUE) &&
                   (in_authority[15:8] == expected_authority) &&
                   (in_epoch[15:8] == current_epoch) &&
                   (in_provenance[15:8] != 8'h00) &&
                   (in_context[15:8] == current_context) &&
                   !seen_parent[id1];
    wire p2_good = (in_state[5:4] == PROVEN_TRUE) &&
                   (in_authority[23:16] == expected_authority) &&
                   (in_epoch[23:16] == current_epoch) &&
                   (in_provenance[23:16] != 8'h00) &&
                   (in_context[23:16] == current_context) &&
                   !seen_parent[id2];
    wire p3_good = (in_state[7:6] == PROVEN_TRUE) &&
                   (in_authority[31:24] == expected_authority) &&
                   (in_epoch[31:24] == current_epoch) &&
                   (in_provenance[31:24] != 8'h00) &&
                   (in_context[31:24] == current_context) &&
                   !seen_parent[id3];

    wire unique_ids = (id0 != id1) && (id0 != id2) && (id0 != id3) &&
                      (id1 != id2) && (id1 != id3) && (id2 != id3);

    wire compose_good = p0_good && p1_good && p2_good && p3_good &&
                        unique_ids && (derived_statement == expected_statement);

    wire outcome_good = auth_valid &&
                        (derived_identity == auth_identity) &&
                        (derived_statement == auth_statement) &&
                        (in_state[1:0] == PROVEN_TRUE) &&
                        (in_authority[7:0] == expected_authority) &&
                        (in_epoch[7:0] == current_epoch) &&
                        (in_provenance[7:0] != 8'h00) &&
                        (in_context[7:0] == current_context) &&
                        !(outcome_seen_valid && outcome_seen_identity == derived_identity);

    always @(posedge clk) begin
        if (reset) begin
            seen_parent <= 256'h0;
            auth_valid <= 1'b0;
            auth_identity <= 8'h00;
            auth_statement <= 8'h00;
            outcome_seen_valid <= 1'b0;
            outcome_seen_identity <= 8'h00;
            compose_valid <= 1'b0;
            compose_allowed <= 1'b0;
            terminal_valid <= 1'b0;
            terminal_success <= 1'b0;
        end else begin
            compose_valid <= 1'b0;
            compose_allowed <= 1'b0;
            terminal_valid <= 1'b0;
            terminal_success <= 1'b0;

            if (in_valid) begin
                if (!in_kind) begin
                    compose_valid <= 1'b1;
                    compose_allowed <= compose_good;
                    auth_valid <= 1'b0;
                    if (compose_good) begin
                        seen_parent[id0] <= 1'b1;
                        seen_parent[id1] <= 1'b1;
                        seen_parent[id2] <= 1'b1;
                        seen_parent[id3] <= 1'b1;
                        auth_valid <= 1'b1;
                        auth_identity <= derived_identity;
                        auth_statement <= derived_statement;
                    end
                end else begin
                    terminal_valid <= 1'b1;
                    terminal_success <= outcome_good;
                    if (outcome_good) begin
                        outcome_seen_valid <= 1'b1;
                        outcome_seen_identity <= derived_identity;
                    end
                    if (auth_valid && derived_identity == auth_identity)
                        auth_valid <= 1'b0;
                end
            end
        end
    end
endmodule


module pb_hw03_vector_conventional(
    input wire clk, input wire reset, input wire in_valid, input wire in_kind,
    input wire [7:0] in_state, input wire [31:0] in_authority,
    input wire [31:0] in_epoch, input wire [31:0] in_identity,
    input wire [31:0] in_provenance, input wire [31:0] in_context,
    input wire [7:0] derived_statement, input wire [7:0] derived_identity,
    input wire [7:0] expected_statement, input wire [7:0] expected_authority,
    input wire [7:0] current_epoch, input wire [7:0] current_context,
    output wire compose_valid, output wire compose_allowed,
    output wire terminal_valid, output wire terminal_success
);
    pb_hw03_vector_core core(
        .clk(clk), .reset(reset), .in_valid(in_valid), .in_kind(in_kind),
        .in_state(in_state), .in_authority(in_authority), .in_epoch(in_epoch),
        .in_identity(in_identity), .in_provenance(in_provenance), .in_context(in_context),
        .derived_statement(derived_statement), .derived_identity(derived_identity),
        .expected_statement(expected_statement), .expected_authority(expected_authority),
        .current_epoch(current_epoch), .current_context(current_context),
        .compose_valid(compose_valid), .compose_allowed(compose_allowed),
        .terminal_valid(terminal_valid), .terminal_success(terminal_success)
    );
endmodule


module pb_hw03_proofbit_compose(
    input wire clk, input wire reset, input wire in_valid, input wire in_kind,
    input wire [7:0] in_state, input wire [31:0] in_authority,
    input wire [31:0] in_epoch, input wire [31:0] in_identity,
    input wire [31:0] in_provenance, input wire [31:0] in_context,
    input wire [7:0] derived_statement, input wire [7:0] derived_identity,
    input wire [7:0] expected_statement, input wire [7:0] expected_authority,
    input wire [7:0] current_epoch, input wire [7:0] current_context,
    output wire compose_valid, output wire compose_allowed,
    output wire terminal_valid, output wire terminal_success
);
    pb_hw03_vector_core core(
        .clk(clk), .reset(reset), .in_valid(in_valid), .in_kind(in_kind),
        .in_state(in_state), .in_authority(in_authority), .in_epoch(in_epoch),
        .in_identity(in_identity), .in_provenance(in_provenance), .in_context(in_context),
        .derived_statement(derived_statement), .derived_identity(derived_identity),
        .expected_statement(expected_statement), .expected_authority(expected_authority),
        .current_epoch(current_epoch), .current_context(current_context),
        .compose_valid(compose_valid), .compose_allowed(compose_allowed),
        .terminal_valid(terminal_valid), .terminal_success(terminal_success)
    );
endmodule

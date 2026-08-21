`timescale 1ns/1ps

module pb_hw02_tb;
    reg clk = 0;
    always #5 clk = ~clk;

    reg reset;

    reg min_valid, min_tag;
    reg [7:0] min_action, min_authority, min_epoch;
    reg [15:0] min_nonce;
    reg [7:0] min_expected_action, min_expected_authority, min_current_epoch;
    wire min_dispatch_valid, min_dispatch_allowed;

    reg rich_valid, rich_kind, rich_tag;
    reg [1:0] rich_state;
    reg [7:0] rich_statement, rich_authority, rich_epoch;
    reg [15:0] rich_identity;
    reg [7:0] rich_provenance, rich_context;
    reg [7:0] rich_expected_statement, rich_expected_authority, rich_current_epoch, rich_current_context;

    wire c_dispatch_valid, c_dispatch_allowed, c_terminal_valid, c_terminal_success;
    wire p_dispatch_valid, p_dispatch_allowed, p_terminal_valid, p_terminal_success;

    integer min_fail = 0;
    integer min_semantic_gap_accepts = 0;
    integer conv_fail = 0;
    integer proof_fail = 0;
    integer rich_safety_cases = 0;
    integer stream_mode = 0;
    integer stream_conv_dispatch = 0;
    integer stream_proof_dispatch = 0;
    integer stream_conv_terminal = 0;
    integer stream_proof_terminal = 0;
    integer min_stream_mode = 0;
    integer min_stream_dispatch = 0;
    integer k;

    localparam [1:0] UNKNOWN = 2'b00;
    localparam [1:0] PROVEN_TRUE = 2'b01;
    localparam [1:0] PROVEN_FALSE = 2'b10;
    localparam [1:0] CONFLICT = 2'b11;

    pb_hw02_min_cap_pipeline min_u(
        .clk(clk), .reset(reset), .in_valid(min_valid), .in_tag(min_tag),
        .in_action(min_action), .in_authority(min_authority), .in_epoch(min_epoch),
        .in_nonce(min_nonce), .expected_action(min_expected_action),
        .expected_authority(min_expected_authority), .current_epoch(min_current_epoch),
        .dispatch_valid(min_dispatch_valid), .dispatch_allowed(min_dispatch_allowed)
    );

    pb_hw02_full_conventional_pipeline conv_u(
        .clk(clk), .reset(reset), .in_valid(rich_valid), .in_kind(rich_kind), .in_tag(rich_tag),
        .in_state(rich_state), .in_statement(rich_statement), .in_authority(rich_authority),
        .in_epoch(rich_epoch), .in_identity(rich_identity), .in_provenance(rich_provenance),
        .in_context(rich_context), .expected_statement(rich_expected_statement),
        .expected_authority(rich_expected_authority), .current_epoch(rich_current_epoch),
        .current_context(rich_current_context), .dispatch_valid(c_dispatch_valid),
        .dispatch_allowed(c_dispatch_allowed), .terminal_valid(c_terminal_valid),
        .terminal_success(c_terminal_success)
    );

    pb_hw02_rich_proofbit_pipeline proof_u(
        .clk(clk), .reset(reset), .in_valid(rich_valid), .in_kind(rich_kind), .in_tag(rich_tag),
        .in_state(rich_state), .in_statement(rich_statement), .in_authority(rich_authority),
        .in_epoch(rich_epoch), .in_identity(rich_identity), .in_provenance(rich_provenance),
        .in_context(rich_context), .expected_statement(rich_expected_statement),
        .expected_authority(rich_expected_authority), .current_epoch(rich_current_epoch),
        .current_context(rich_current_context), .dispatch_valid(p_dispatch_valid),
        .dispatch_allowed(p_dispatch_allowed), .terminal_valid(p_terminal_valid),
        .terminal_success(p_terminal_success)
    );

    always @(posedge clk) begin
        #1;
        if (stream_mode) begin
            if (c_dispatch_valid && c_dispatch_allowed) stream_conv_dispatch = stream_conv_dispatch + 1;
            if (p_dispatch_valid && p_dispatch_allowed) stream_proof_dispatch = stream_proof_dispatch + 1;
            if (c_terminal_valid && c_terminal_success) stream_conv_terminal = stream_conv_terminal + 1;
            if (p_terminal_valid && p_terminal_success) stream_proof_terminal = stream_proof_terminal + 1;
        end
        if (min_stream_mode && min_dispatch_valid && min_dispatch_allowed)
            min_stream_dispatch = min_stream_dispatch + 1;
    end

    task reset_fixture;
        begin
            reset = 1'b1;
            min_valid = 1'b0;
            rich_valid = 1'b0;
            repeat (3) @(posedge clk);
            reset = 1'b0;
            repeat (2) @(posedge clk);
        end
    endtask

    task min_case;
        input tag;
        input [7:0] action;
        input [7:0] authority;
        input [7:0] epoch;
        input [15:0] nonce;
        input expected_allow;
        begin
            @(negedge clk);
            min_valid = 1'b1; min_tag = tag; min_action = action; min_authority = authority;
            min_epoch = epoch; min_nonce = nonce; min_expected_action = 8'hA1;
            min_expected_authority = 8'h07; min_current_epoch = 8'h03;
            @(negedge clk); min_valid = 1'b0;
            @(negedge clk);
            if (!min_dispatch_valid || min_dispatch_allowed !== expected_allow)
                min_fail = min_fail + 1;
        end
    endtask

    task rich_case;
        input kind;
        input tag;
        input [1:0] state;
        input [7:0] statement;
        input [7:0] authority;
        input [7:0] epoch;
        input [15:0] identity;
        input [7:0] provenance;
        input [7:0] ctx;
        input expected_allow;
        input score_case;
        begin
            @(negedge clk);
            rich_valid = 1'b1; rich_kind = kind; rich_tag = tag; rich_state = state;
            rich_statement = statement; rich_authority = authority; rich_epoch = epoch;
            rich_identity = identity; rich_provenance = provenance; rich_context = ctx;
            rich_expected_statement = 8'hA1; rich_expected_authority = 8'h07;
            rich_current_epoch = 8'h03; rich_current_context = 8'h22;
            @(negedge clk); rich_valid = 1'b0;
            @(negedge clk);
            if (score_case) rich_safety_cases = rich_safety_cases + 1;
            if (!kind) begin
                if (!c_dispatch_valid || c_dispatch_allowed !== expected_allow) conv_fail = conv_fail + 1;
                if (!p_dispatch_valid || p_dispatch_allowed !== expected_allow) proof_fail = proof_fail + 1;
            end else begin
                if (!c_terminal_valid || c_terminal_success !== expected_allow) conv_fail = conv_fail + 1;
                if (!p_terminal_valid || p_terminal_success !== expected_allow) proof_fail = proof_fail + 1;
            end
            if ((c_dispatch_valid !== p_dispatch_valid) ||
                (c_dispatch_allowed !== p_dispatch_allowed) ||
                (c_terminal_valid !== p_terminal_valid) ||
                (c_terminal_success !== p_terminal_success)) begin
                conv_fail = conv_fail + 1;
                proof_fail = proof_fail + 1;
            end
        end
    endtask

    initial begin
        min_tag = 0; min_action = 0; min_authority = 0; min_epoch = 0; min_nonce = 0;
        min_expected_action = 8'hA1; min_expected_authority = 8'h07; min_current_epoch = 8'h03;
        rich_kind = 0; rich_tag = 0; rich_state = 0; rich_statement = 0; rich_authority = 0;
        rich_epoch = 0; rich_identity = 0; rich_provenance = 0; rich_context = 0;
        rich_expected_statement = 8'hA1; rich_expected_authority = 8'h07;
        rich_current_epoch = 8'h03; rich_current_context = 8'h22;

        reset_fixture();

        min_case(1, 8'hA1, 8'h07, 8'h03, 16'h0101, 1);
        min_case(0, 8'hA1, 8'h07, 8'h03, 16'h0102, 0);
        min_case(1, 8'hB2, 8'h07, 8'h03, 16'h0103, 0);
        min_case(1, 8'hA1, 8'h08, 8'h03, 16'h0104, 0);
        min_case(1, 8'hA1, 8'h07, 8'h02, 16'h0105, 0);
        min_case(1, 8'hA1, 8'h07, 8'h03, 16'h0106, 1);
        min_case(1, 8'hA1, 8'h07, 8'h03, 16'h0106, 0);

        min_case(1, 8'hA1, 8'h07, 8'h03, 16'h0110, 1); min_semantic_gap_accepts = min_semantic_gap_accepts + 1;
        min_case(1, 8'hA1, 8'h07, 8'h03, 16'h0111, 1); min_semantic_gap_accepts = min_semantic_gap_accepts + 1;
        min_case(1, 8'hA1, 8'h07, 8'h03, 16'h0112, 1); min_semantic_gap_accepts = min_semantic_gap_accepts + 1;
        min_case(1, 8'hA1, 8'h07, 8'h03, 16'h0113, 1); min_semantic_gap_accepts = min_semantic_gap_accepts + 1;

        reset_fixture();

        rich_case(0,1,PROVEN_TRUE, 8'hA1,8'h07,8'h03,16'h0201,8'h11,8'h22,1,1);
        rich_case(0,1,UNKNOWN,     8'hA1,8'h07,8'h03,16'h0202,8'h11,8'h22,0,1);
        rich_case(0,1,CONFLICT,    8'hA1,8'h07,8'h03,16'h0203,8'h11,8'h22,0,1);
        rich_case(0,1,PROVEN_FALSE,8'hA1,8'h07,8'h03,16'h0204,8'h11,8'h22,0,1);
        rich_case(0,1,PROVEN_TRUE, 8'hB2,8'h07,8'h03,16'h0205,8'h11,8'h22,0,1);
        rich_case(0,1,PROVEN_TRUE, 8'hA1,8'h08,8'h03,16'h0206,8'h11,8'h22,0,1);
        rich_case(0,1,PROVEN_TRUE, 8'hA1,8'h07,8'h02,16'h0207,8'h11,8'h22,0,1);
        rich_case(0,1,PROVEN_TRUE, 8'hA1,8'h07,8'h03,16'h0208,8'h00,8'h22,0,1);
        rich_case(0,1,PROVEN_TRUE, 8'hA1,8'h07,8'h03,16'h0209,8'h11,8'h23,0,1);
        rich_case(0,1,PROVEN_TRUE, 8'hA1,8'h07,8'h03,16'h0210,8'h11,8'h22,1,0);
        rich_case(0,1,PROVEN_TRUE, 8'hA1,8'h07,8'h03,16'h0210,8'h11,8'h22,0,1);

        rich_case(1,1,PROVEN_TRUE, 8'hA1,8'h07,8'h03,16'h0301,8'h11,8'h22,0,1);

        rich_case(0,1,PROVEN_TRUE, 8'hA1,8'h07,8'h03,16'h0302,8'h11,8'h22,1,0);
        rich_case(1,1,PROVEN_TRUE, 8'hA1,8'h07,8'h03,16'h0302,8'h11,8'h22,1,1);
        rich_case(1,1,PROVEN_TRUE, 8'hA1,8'h07,8'h03,16'h0302,8'h11,8'h22,0,1);

        rich_case(0,1,PROVEN_TRUE, 8'hA1,8'h07,8'h03,16'h0303,8'h11,8'h22,1,0);
        rich_case(1,1,PROVEN_FALSE,8'hA1,8'h07,8'h03,16'h0303,8'h11,8'h22,0,1);

        reset_fixture();
        min_stream_mode = 1;
        for (k = 0; k < 32; k = k + 1) begin
            @(negedge clk);
            min_valid = 1; min_tag = 1; min_action = 8'hA1; min_authority = 8'h07;
            min_epoch = 8'h03; min_nonce = 16'h1000 + k;
        end
        @(negedge clk); min_valid = 0;
        repeat (3) @(posedge clk);
        #1; min_stream_mode = 0;

        reset_fixture();
        stream_mode = 1;
        for (k = 0; k < 16; k = k + 1) begin
            @(negedge clk);
            rich_valid = 1; rich_kind = 0; rich_tag = 1; rich_state = PROVEN_TRUE;
            rich_statement = 8'hA1; rich_authority = 8'h07; rich_epoch = 8'h03;
            rich_identity = 16'h2000 + k; rich_provenance = 8'h11; rich_context = 8'h22;
            rich_expected_statement = 8'hA1; rich_expected_authority = 8'h07;
            rich_current_epoch = 8'h03; rich_current_context = 8'h22;
            @(negedge clk);
            rich_valid = 1; rich_kind = 1; rich_tag = 1; rich_state = PROVEN_TRUE;
            rich_statement = 8'hA1; rich_authority = 8'h07; rich_epoch = 8'h03;
            rich_identity = 16'h2000 + k; rich_provenance = 8'h11; rich_context = 8'h22;
        end
        @(negedge clk); rich_valid = 0;
        repeat (4) @(posedge clk);
        #1; stream_mode = 0;

        if (min_fail != 0 || conv_fail != 0 || proof_fail != 0 ||
            min_stream_dispatch != 32 || stream_conv_dispatch != 16 ||
            stream_proof_dispatch != 16 || stream_conv_terminal != 16 ||
            stream_proof_terminal != 16 || rich_safety_cases != 14) begin
            $display("PB_HW02_SIM FAIL min_fail=%0d gaps=%0d conv_fail=%0d proof_fail=%0d safety=%0d min_stream=%0d conv_dispatch=%0d proof_dispatch=%0d conv_terminal=%0d proof_terminal=%0d",
                     min_fail, min_semantic_gap_accepts, conv_fail, proof_fail, rich_safety_cases,
                     min_stream_dispatch, stream_conv_dispatch, stream_proof_dispatch,
                     stream_conv_terminal, stream_proof_terminal);
            $fatal(1);
        end

        $display("PB_HW02_SIM PASS safety=%0d min_fail=%0d semantic_gaps=%0d conv_fail=%0d proof_fail=%0d min_stream=%0d rich_transactions=32 trusted_terminal=16 stalls=0",
                 rich_safety_cases, min_fail, min_semantic_gap_accepts, conv_fail, proof_fail, min_stream_dispatch);
        $finish;
    end
endmodule

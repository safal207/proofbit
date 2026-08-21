`timescale 1ns/1ps

module pb_hw03_tb;
    reg clk = 0;
    always #5 clk = ~clk;

    reg reset;

    // Scalar conventional interface.
    reg s_valid;
    reg [1:0] s_kind;
    reg [1:0] s_slot;
    reg [1:0] s_state;
    reg [7:0] s_authority, s_epoch, s_identity, s_provenance, s_context;
    reg [7:0] s_derived_statement, s_derived_identity;
    reg [7:0] s_expected_statement, s_expected_authority, s_current_epoch, s_current_context;
    wire s_compose_valid, s_compose_allowed, s_terminal_valid, s_terminal_success;

    // Shared vector input for conventional and ProofBit composition primitives.
    reg v_valid, v_kind;
    reg [7:0] v_state;
    reg [31:0] v_authority, v_epoch, v_identity, v_provenance, v_context;
    reg [7:0] v_derived_statement, v_derived_identity;
    reg [7:0] v_expected_statement, v_expected_authority, v_current_epoch, v_current_context;
    wire c_compose_valid, c_compose_allowed, c_terminal_valid, c_terminal_success;
    wire p_compose_valid, p_compose_allowed, p_terminal_valid, p_terminal_success;

    // Canonical 4-parent bundle used by fault scenarios.
    reg [7:0] b_state;
    reg [31:0] b_authority, b_epoch, b_identity, b_provenance, b_context;
    reg [7:0] b_derived_statement, b_derived_identity;

    integer scalar_fail = 0;
    integer conv_fail = 0;
    integer proof_fail = 0;
    integer safety_cases = 0;
    integer scalar_stream_tx = 0;
    integer vector_stream_tx = 0;
    integer scalar_stream_terminal = 0;
    integer conv_stream_terminal = 0;
    integer proof_stream_terminal = 0;
    integer scalar_stream_mode = 0;
    integer vector_stream_mode = 0;
    integer k;
    integer j;

    localparam [1:0] UNKNOWN = 2'b00;
    localparam [1:0] PROVEN_TRUE = 2'b01;
    localparam [1:0] PROVEN_FALSE = 2'b10;
    localparam [1:0] CONFLICT = 2'b11;

    pb_hw03_scalar_conventional scalar_u(
        .clk(clk), .reset(reset), .in_valid(s_valid), .in_kind(s_kind), .in_slot(s_slot),
        .in_state(s_state), .in_authority(s_authority), .in_epoch(s_epoch),
        .in_identity(s_identity), .in_provenance(s_provenance), .in_context(s_context),
        .derived_statement(s_derived_statement), .derived_identity(s_derived_identity),
        .expected_statement(s_expected_statement), .expected_authority(s_expected_authority),
        .current_epoch(s_current_epoch), .current_context(s_current_context),
        .compose_valid(s_compose_valid), .compose_allowed(s_compose_allowed),
        .terminal_valid(s_terminal_valid), .terminal_success(s_terminal_success)
    );

    pb_hw03_vector_conventional conv_u(
        .clk(clk), .reset(reset), .in_valid(v_valid), .in_kind(v_kind),
        .in_state(v_state), .in_authority(v_authority), .in_epoch(v_epoch),
        .in_identity(v_identity), .in_provenance(v_provenance), .in_context(v_context),
        .derived_statement(v_derived_statement), .derived_identity(v_derived_identity),
        .expected_statement(v_expected_statement), .expected_authority(v_expected_authority),
        .current_epoch(v_current_epoch), .current_context(v_current_context),
        .compose_valid(c_compose_valid), .compose_allowed(c_compose_allowed),
        .terminal_valid(c_terminal_valid), .terminal_success(c_terminal_success)
    );

    pb_hw03_proofbit_compose proof_u(
        .clk(clk), .reset(reset), .in_valid(v_valid), .in_kind(v_kind),
        .in_state(v_state), .in_authority(v_authority), .in_epoch(v_epoch),
        .in_identity(v_identity), .in_provenance(v_provenance), .in_context(v_context),
        .derived_statement(v_derived_statement), .derived_identity(v_derived_identity),
        .expected_statement(v_expected_statement), .expected_authority(v_expected_authority),
        .current_epoch(v_current_epoch), .current_context(v_current_context),
        .compose_valid(p_compose_valid), .compose_allowed(p_compose_allowed),
        .terminal_valid(p_terminal_valid), .terminal_success(p_terminal_success)
    );

    always @(posedge clk) begin
        #1;
        if (scalar_stream_mode && s_terminal_valid && s_terminal_success)
            scalar_stream_terminal = scalar_stream_terminal + 1;
        if (vector_stream_mode && c_terminal_valid && c_terminal_success)
            conv_stream_terminal = conv_stream_terminal + 1;
        if (vector_stream_mode && p_terminal_valid && p_terminal_success)
            proof_stream_terminal = proof_stream_terminal + 1;
    end

    task reset_fixture;
        begin
            reset = 1'b1;
            s_valid = 1'b0;
            v_valid = 1'b0;
            repeat (3) @(posedge clk);
            reset = 1'b0;
            repeat (2) @(posedge clk);
        end
    endtask

    task set_good_bundle;
        input [7:0] base_id;
        input [7:0] derived_id;
        begin
            b_state = 8'h55;
            b_authority = 32'h07070707;
            b_epoch = 32'h03030303;
            b_provenance = 32'h11111111;
            b_context = 32'h22222222;
            b_identity[7:0] = base_id;
            b_identity[15:8] = base_id + 8'd1;
            b_identity[23:16] = base_id + 8'd2;
            b_identity[31:24] = base_id + 8'd3;
            b_derived_statement = 8'hA1;
            b_derived_identity = derived_id;
        end
    endtask

    task scalar_compose_check;
        input expected_allow;
        integer n;
        begin
            for (n = 0; n < 4; n = n + 1) begin
                @(negedge clk);
                s_valid = 1'b1; s_kind = 2'd0; s_slot = n[1:0];
                s_state = b_state[n*2 +: 2];
                s_authority = b_authority[n*8 +: 8];
                s_epoch = b_epoch[n*8 +: 8];
                s_identity = b_identity[n*8 +: 8];
                s_provenance = b_provenance[n*8 +: 8];
                s_context = b_context[n*8 +: 8];
                s_derived_statement = b_derived_statement;
                s_derived_identity = b_derived_identity;
            end
            @(negedge clk);
            s_valid = 1'b1; s_kind = 2'd1;
            s_derived_statement = b_derived_statement;
            s_derived_identity = b_derived_identity;
            @(posedge clk); #1;
            if (!s_compose_valid || s_compose_allowed !== expected_allow)
                scalar_fail = scalar_fail + 1;
            @(negedge clk); s_valid = 1'b0;
        end
    endtask

    task vector_compose_check;
        input expected_allow;
        begin
            @(negedge clk);
            v_valid = 1'b1; v_kind = 1'b0;
            v_state = b_state; v_authority = b_authority; v_epoch = b_epoch;
            v_identity = b_identity; v_provenance = b_provenance; v_context = b_context;
            v_derived_statement = b_derived_statement; v_derived_identity = b_derived_identity;
            @(posedge clk); #1;
            if (!c_compose_valid || c_compose_allowed !== expected_allow)
                conv_fail = conv_fail + 1;
            if (!p_compose_valid || p_compose_allowed !== expected_allow)
                proof_fail = proof_fail + 1;
            if ((c_compose_valid !== p_compose_valid) || (c_compose_allowed !== p_compose_allowed)) begin
                conv_fail = conv_fail + 1;
                proof_fail = proof_fail + 1;
            end
            @(negedge clk); v_valid = 1'b0;
        end
    endtask

    task scalar_outcome_check;
        input [1:0] outcome_state;
        input expected_success;
        begin
            @(negedge clk);
            s_valid = 1'b1; s_kind = 2'd2; s_slot = 2'd0;
            s_state = outcome_state; s_authority = 8'h07; s_epoch = 8'h03;
            s_identity = b_derived_identity; s_provenance = 8'h11; s_context = 8'h22;
            s_derived_statement = b_derived_statement; s_derived_identity = b_derived_identity;
            @(posedge clk); #1;
            if (!s_terminal_valid || s_terminal_success !== expected_success)
                scalar_fail = scalar_fail + 1;
            @(negedge clk); s_valid = 1'b0;
        end
    endtask

    task vector_outcome_check;
        input [1:0] outcome_state;
        input expected_success;
        begin
            @(negedge clk);
            v_valid = 1'b1; v_kind = 1'b1;
            v_state = 8'h00; v_state[1:0] = outcome_state;
            v_authority = 32'h00000007; v_epoch = 32'h00000003;
            v_identity = {24'h0, b_derived_identity};
            v_provenance = 32'h00000011; v_context = 32'h00000022;
            v_derived_statement = b_derived_statement; v_derived_identity = b_derived_identity;
            @(posedge clk); #1;
            if (!c_terminal_valid || c_terminal_success !== expected_success)
                conv_fail = conv_fail + 1;
            if (!p_terminal_valid || p_terminal_success !== expected_success)
                proof_fail = proof_fail + 1;
            if ((c_terminal_valid !== p_terminal_valid) || (c_terminal_success !== p_terminal_success)) begin
                conv_fail = conv_fail + 1;
                proof_fail = proof_fail + 1;
            end
            @(negedge clk); v_valid = 1'b0;
        end
    endtask

    initial begin
        s_kind = 0; s_slot = 0; s_state = 0; s_authority = 0; s_epoch = 0;
        s_identity = 0; s_provenance = 0; s_context = 0;
        s_derived_statement = 8'hA1; s_derived_identity = 0;
        s_expected_statement = 8'hA1; s_expected_authority = 8'h07;
        s_current_epoch = 8'h03; s_current_context = 8'h22;

        v_kind = 0; v_state = 0; v_authority = 0; v_epoch = 0; v_identity = 0;
        v_provenance = 0; v_context = 0; v_derived_statement = 8'hA1; v_derived_identity = 0;
        v_expected_statement = 8'hA1; v_expected_authority = 8'h07;
        v_current_epoch = 8'h03; v_current_context = 8'h22;

        // 1. VALID end-to-end composition + separate outcome.
        reset_fixture(); set_good_bundle(8'h01, 8'h80);
        scalar_compose_check(1); vector_compose_check(1);
        scalar_outcome_check(PROVEN_TRUE, 1); vector_outcome_check(PROVEN_TRUE, 1);
        safety_cases = safety_cases + 1;

        // 2. UNKNOWN parent.
        reset_fixture(); set_good_bundle(8'h05, 8'h81); b_state[1:0] = UNKNOWN;
        scalar_compose_check(0); vector_compose_check(0); safety_cases = safety_cases + 1;

        // 3. CONFLICT parent.
        reset_fixture(); set_good_bundle(8'h09, 8'h82); b_state[3:2] = CONFLICT;
        scalar_compose_check(0); vector_compose_check(0); safety_cases = safety_cases + 1;

        // 4. PROVEN_FALSE parent.
        reset_fixture(); set_good_bundle(8'h0D, 8'h83); b_state[5:4] = PROVEN_FALSE;
        scalar_compose_check(0); vector_compose_check(0); safety_cases = safety_cases + 1;

        // 5. stale epoch.
        reset_fixture(); set_good_bundle(8'h11, 8'h84); b_epoch[31:24] = 8'h02;
        scalar_compose_check(0); vector_compose_check(0); safety_cases = safety_cases + 1;

        // 6. wrong authority.
        reset_fixture(); set_good_bundle(8'h15, 8'h85); b_authority[15:8] = 8'h08;
        scalar_compose_check(0); vector_compose_check(0); safety_cases = safety_cases + 1;

        // 7. provenance drop.
        reset_fixture(); set_good_bundle(8'h19, 8'h86); b_provenance[23:16] = 8'h00;
        scalar_compose_check(0); vector_compose_check(0); safety_cases = safety_cases + 1;

        // 8. execution-context rebound.
        reset_fixture(); set_good_bundle(8'h1D, 8'h87); b_context[7:0] = 8'h23;
        scalar_compose_check(0); vector_compose_check(0); safety_cases = safety_cases + 1;

        // 9. duplicate parent identity inside one composition.
        reset_fixture(); set_good_bundle(8'h21, 8'h88); b_identity[31:24] = b_identity[7:0];
        scalar_compose_check(0); vector_compose_check(0); safety_cases = safety_cases + 1;

        // 10. derived statement rebound.
        reset_fixture(); set_good_bundle(8'h25, 8'h89); b_derived_statement = 8'hB2;
        scalar_compose_check(0); vector_compose_check(0); safety_cases = safety_cases + 1;

        // 11. parent replay across two otherwise valid compositions.
        reset_fixture(); set_good_bundle(8'h29, 8'h8A);
        scalar_compose_check(1); vector_compose_check(1);
        scalar_outcome_check(PROVEN_TRUE, 1); vector_outcome_check(PROVEN_TRUE, 1);
        set_good_bundle(8'h40, 8'h8B); b_identity[7:0] = 8'h29;
        scalar_compose_check(0); vector_compose_check(0); safety_cases = safety_cases + 1;

        // 12. outcome without an authorization cannot manufacture success.
        reset_fixture(); set_good_bundle(8'h44, 8'h8C);
        scalar_outcome_check(PROVEN_TRUE, 0); vector_outcome_check(PROVEN_TRUE, 0);
        safety_cases = safety_cases + 1;

        // 13. duplicate outcome after one proven terminal success.
        reset_fixture(); set_good_bundle(8'h48, 8'h8D);
        scalar_compose_check(1); vector_compose_check(1);
        scalar_outcome_check(PROVEN_TRUE, 1); vector_outcome_check(PROVEN_TRUE, 1);
        scalar_outcome_check(PROVEN_TRUE, 0); vector_outcome_check(PROVEN_TRUE, 0);
        safety_cases = safety_cases + 1;

        // 14. false outcome evidence stays terminal-false.
        reset_fixture(); set_good_bundle(8'h4C, 8'h8E);
        scalar_compose_check(1); vector_compose_check(1);
        scalar_outcome_check(PROVEN_FALSE, 0); vector_outcome_check(PROVEN_FALSE, 0);
        safety_cases = safety_cases + 1;

        // Throughput/economics stream: scalar protocol is exactly
        // 4 PARENT + 1 COMPOSE + 1 OUTCOME transactions per trusted terminal.
        reset_fixture();
        scalar_stream_tx = 0; scalar_stream_terminal = 0; scalar_stream_mode = 1;
        for (k = 0; k < 16; k = k + 1) begin
            for (j = 0; j < 4; j = j + 1) begin
                @(negedge clk);
                s_valid = 1'b1; s_kind = 2'd0; s_slot = j[1:0];
                s_state = PROVEN_TRUE; s_authority = 8'h07; s_epoch = 8'h03;
                s_identity = 8'd1 + k*4 + j; s_provenance = 8'h11; s_context = 8'h22;
                s_derived_statement = 8'hA1; s_derived_identity = 8'hA0 + k;
                scalar_stream_tx = scalar_stream_tx + 1;
            end
            @(negedge clk);
            s_valid = 1'b1; s_kind = 2'd1;
            s_derived_statement = 8'hA1; s_derived_identity = 8'hA0 + k;
            scalar_stream_tx = scalar_stream_tx + 1;
            @(negedge clk);
            s_valid = 1'b1; s_kind = 2'd2; s_state = PROVEN_TRUE;
            s_authority = 8'h07; s_epoch = 8'h03; s_provenance = 8'h11; s_context = 8'h22;
            s_derived_statement = 8'hA1; s_derived_identity = 8'hA0 + k;
            scalar_stream_tx = scalar_stream_tx + 1;
        end
        @(negedge clk); s_valid = 1'b0;
        repeat (3) @(posedge clk); #1; scalar_stream_mode = 0;

        // Vector conventional and ProofBit: one COMPOSE4 + one OUTCOME.
        reset_fixture();
        vector_stream_tx = 0; conv_stream_terminal = 0; proof_stream_terminal = 0; vector_stream_mode = 1;
        for (k = 0; k < 16; k = k + 1) begin
            @(negedge clk);
            v_valid = 1'b1; v_kind = 1'b0; v_state = 8'h55;
            v_authority = 32'h07070707; v_epoch = 32'h03030303;
            v_provenance = 32'h11111111; v_context = 32'h22222222;
            v_identity[7:0] = 8'd1 + k*4;
            v_identity[15:8] = 8'd2 + k*4;
            v_identity[23:16] = 8'd3 + k*4;
            v_identity[31:24] = 8'd4 + k*4;
            v_derived_statement = 8'hA1; v_derived_identity = 8'hC0 + k;
            vector_stream_tx = vector_stream_tx + 1;
            @(negedge clk);
            v_valid = 1'b1; v_kind = 1'b1; v_state = 8'h01;
            v_authority = 32'h00000007; v_epoch = 32'h00000003;
            v_identity = {24'h0, (8'hC0 + k)};
            v_provenance = 32'h00000011; v_context = 32'h00000022;
            v_derived_statement = 8'hA1; v_derived_identity = 8'hC0 + k;
            vector_stream_tx = vector_stream_tx + 1;
        end
        @(negedge clk); v_valid = 1'b0;
        repeat (3) @(posedge clk); #1; vector_stream_mode = 0;

        if (scalar_fail != 0 || conv_fail != 0 || proof_fail != 0 || safety_cases != 14 ||
            scalar_stream_tx != 96 || vector_stream_tx != 32 ||
            scalar_stream_terminal != 16 || conv_stream_terminal != 16 || proof_stream_terminal != 16) begin
            $display("PB_HW03_SIM FAIL safety=%0d scalar_fail=%0d conv_fail=%0d proof_fail=%0d scalar_tx=%0d vector_tx=%0d scalar_terminal=%0d conv_terminal=%0d proof_terminal=%0d",
                     safety_cases, scalar_fail, conv_fail, proof_fail, scalar_stream_tx, vector_stream_tx,
                     scalar_stream_terminal, conv_stream_terminal, proof_stream_terminal);
            $fatal(1);
        end

        $display("PB_HW03_SIM PASS safety=%0d scalar_fail=%0d conv_fail=%0d proof_fail=%0d scalar_tx=%0d vector_tx=%0d scalar_terminal=%0d conv_terminal=%0d proof_terminal=%0d stalls=0",
                 safety_cases, scalar_fail, conv_fail, proof_fail, scalar_stream_tx, vector_stream_tx,
                 scalar_stream_terminal, conv_stream_terminal, proof_stream_terminal);
        $finish;
    end
endmodule

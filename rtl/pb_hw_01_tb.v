`timescale 1ns/1ps

module pb_hw01_tb;
    reg clk = 0;
    reg rst = 1;
    always #5 clk = ~clk;

    reg in_valid = 0;
    reg in_tag = 0;
    reg [1:0] in_state = 0;
    reg [7:0] in_action = 0;
    reg [7:0] expected_action = 0;
    reg [7:0] in_authority = 0;
    reg [7:0] current_authority = 0;
    reg [7:0] in_epoch = 0;
    reg [7:0] current_epoch = 0;
    reg [15:0] in_nonce = 0;
    reg [7:0] in_provenance = 0;
    reg [7:0] in_context = 0;
    reg [7:0] current_context = 0;

    wire raw_valid, raw_allow;
    wire cap_valid, cap_allow;
    wire proof_valid, proof_allow;

    integer safety_cases = 0;
    integer raw_unsafe = 0;
    integer cap_fail = 0;
    integer proof_fail = 0;
    integer stream_raw = 0;
    integer stream_cap = 0;
    integer stream_proof = 0;
    integer i;

    pb_hw01_raw_pipeline raw_uut(
        .clk(clk), .rst(rst), .in_valid(in_valid), .in_tag(in_tag),
        .in_state(in_state), .in_action(in_action), .expected_action(expected_action),
        .in_authority(in_authority), .current_authority(current_authority),
        .in_epoch(in_epoch), .current_epoch(current_epoch), .in_nonce(in_nonce),
        .in_provenance(in_provenance), .in_context(in_context),
        .current_context(current_context), .out_valid(raw_valid), .out_allow(raw_allow)
    );

    pb_hw01_capability_pipeline cap_uut(
        .clk(clk), .rst(rst), .in_valid(in_valid), .in_tag(in_tag),
        .in_state(in_state), .in_action(in_action), .expected_action(expected_action),
        .in_authority(in_authority), .current_authority(current_authority),
        .in_epoch(in_epoch), .current_epoch(current_epoch), .in_nonce(in_nonce),
        .in_provenance(in_provenance), .in_context(in_context),
        .current_context(current_context), .out_valid(cap_valid), .out_allow(cap_allow)
    );

    pb_hw01_proofbit_pipeline proof_uut(
        .clk(clk), .rst(rst), .in_valid(in_valid), .in_tag(in_tag),
        .in_state(in_state), .in_action(in_action), .expected_action(expected_action),
        .in_authority(in_authority), .current_authority(current_authority),
        .in_epoch(in_epoch), .current_epoch(current_epoch), .in_nonce(in_nonce),
        .in_provenance(in_provenance), .in_context(in_context),
        .current_context(current_context), .out_valid(proof_valid), .out_allow(proof_allow)
    );

    task drive_case;
        input tag_i;
        input [1:0] state_i;
        input [7:0] action_i;
        input [7:0] expected_i;
        input [7:0] authority_i;
        input [7:0] cur_authority_i;
        input [7:0] epoch_i;
        input [7:0] cur_epoch_i;
        input [15:0] nonce_i;
        input [7:0] provenance_i;
        input [7:0] context_i;
        input [7:0] cur_context_i;
        input expected_strong;
        begin
            @(negedge clk);
            in_valid = 1'b1;
            in_tag = tag_i;
            in_state = state_i;
            in_action = action_i;
            expected_action = expected_i;
            in_authority = authority_i;
            current_authority = cur_authority_i;
            in_epoch = epoch_i;
            current_epoch = cur_epoch_i;
            in_nonce = nonce_i;
            in_provenance = provenance_i;
            in_context = context_i;
            current_context = cur_context_i;

            @(posedge clk); #1;
            @(negedge clk);
            in_valid = 1'b0;
            @(posedge clk); #1;

            safety_cases = safety_cases + 1;
            if (!cap_valid || !proof_valid || !raw_valid) begin
                $display("PB_HW01_ERROR missing out_valid case=%0d", safety_cases);
                $finish(2);
            end
            if (cap_allow !== expected_strong) cap_fail = cap_fail + 1;
            if (proof_allow !== expected_strong) proof_fail = proof_fail + 1;
            if (cap_allow !== proof_allow) begin
                $display("PB_HW01_ERROR strong disagreement case=%0d cap=%0d proof=%0d", safety_cases, cap_allow, proof_allow);
                $finish(3);
            end
            if (!expected_strong && raw_allow) raw_unsafe = raw_unsafe + 1;
        end
    endtask

    initial begin
        repeat (3) @(posedge clk);
        @(negedge clk); rst = 0;

        // 1: valid
        drive_case(1, 2'b01, 8'hA1, 8'hA1, 8'h07, 8'h07, 8'h01, 8'h01, 16'h0001, 8'h01, 8'h01, 8'h01, 1);
        // 2: bad tag
        drive_case(0, 2'b01, 8'hA1, 8'hA1, 8'h07, 8'h07, 8'h01, 8'h01, 16'h0002, 8'h01, 8'h01, 8'h01, 0);
        // 3: non-proven / disallowed epistemic state
        drive_case(1, 2'b00, 8'hA1, 8'hA1, 8'h07, 8'h07, 8'h01, 8'h01, 16'h0003, 8'h01, 8'h01, 8'h01, 0);
        // 4: statement/action rebind
        drive_case(1, 2'b01, 8'hB2, 8'hA1, 8'h07, 8'h07, 8'h01, 8'h01, 16'h0004, 8'h01, 8'h01, 8'h01, 0);
        // 5: wrong authority
        drive_case(1, 2'b01, 8'hA1, 8'hA1, 8'h08, 8'h07, 8'h01, 8'h01, 16'h0005, 8'h01, 8'h01, 8'h01, 0);
        // 6: stale epoch
        drive_case(1, 2'b01, 8'hA1, 8'hA1, 8'h07, 8'h07, 8'h01, 8'h02, 16'h0006, 8'h01, 8'h01, 8'h01, 0);
        // 7: missing provenance/source
        drive_case(1, 2'b01, 8'hA1, 8'hA1, 8'h07, 8'h07, 8'h01, 8'h01, 16'h0007, 8'h00, 8'h01, 8'h01, 0);
        // 8: wrong execution context/domain
        drive_case(1, 2'b01, 8'hA1, 8'hA1, 8'h07, 8'h07, 8'h01, 8'h01, 16'h0008, 8'h01, 8'h02, 8'h01, 0);
        // 9: valid single-use authorization
        drive_case(1, 2'b01, 8'hA1, 8'hA1, 8'h07, 8'h07, 8'h01, 8'h01, 16'h0009, 8'h01, 8'h01, 8'h01, 1);
        // 10: replay the exact same nonce
        drive_case(1, 2'b01, 8'hA1, 8'hA1, 8'h07, 8'h07, 8'h01, 8'h01, 16'h0009, 8'h01, 8'h01, 8'h01, 0);

        if (safety_cases != 10 || cap_fail != 0 || proof_fail != 0 || raw_unsafe == 0) begin
            $display("PB_HW01_ERROR safety=%0d raw_unsafe=%0d cap_fail=%0d proof_fail=%0d", safety_cases, raw_unsafe, cap_fail, proof_fail);
            $finish(4);
        end

        // Continuous valid stream: one accepted authorization every clock after fill.
        @(negedge clk);
        for (i = 0; i < 32; i = i + 1) begin
            in_valid = 1'b1;
            in_tag = 1'b1;
            in_state = 2'b01;
            in_action = 8'hA1;
            expected_action = 8'hA1;
            in_authority = 8'h07;
            current_authority = 8'h07;
            in_epoch = 8'h03;
            current_epoch = 8'h03;
            in_nonce = 16'h0100 + i;
            in_provenance = 8'h01;
            in_context = 8'h01;
            current_context = 8'h01;
            @(posedge clk); #1;
            if (raw_valid && raw_allow) stream_raw = stream_raw + 1;
            if (cap_valid && cap_allow) stream_cap = stream_cap + 1;
            if (proof_valid && proof_allow) stream_proof = stream_proof + 1;
            @(negedge clk);
        end
        in_valid = 1'b0;
        @(posedge clk); #1;
        if (raw_valid && raw_allow) stream_raw = stream_raw + 1;
        if (cap_valid && cap_allow) stream_cap = stream_cap + 1;
        if (proof_valid && proof_allow) stream_proof = stream_proof + 1;

        if (stream_raw != 32 || stream_cap != 32 || stream_proof != 32) begin
            $display("PB_HW01_ERROR stream raw=%0d cap=%0d proof=%0d", stream_raw, stream_cap, stream_proof);
            $finish(5);
        end

        $display("PB_HW01_SIM PASS safety=%0d raw_unsafe=%0d cap_fail=%0d proof_fail=%0d stream=%0d latency_cycles=1 stalls=0", safety_cases, raw_unsafe, cap_fail, proof_fail, stream_cap);
        $finish(0);
    end
endmodule

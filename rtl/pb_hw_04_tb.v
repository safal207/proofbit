`timescale 1ns/1ps
module pb_hw04_tb;
    reg clk=0; always #5 clk=~clk;
    integer cycle=0; always @(posedge clk) cycle=cycle+1;
    reg reset;
    reg write_valid; reg [9:0] write_addr; reg [63:0] write_record;
    reg invalidate_valid; reg [9:0] invalidate_addr;
    reg compose_start; reg [9:0] addr0,addr1,addr2,addr3;
    reg [7:0] derived_statement; reg [9:0] derived_identity;
    reg [7:0] expected_statement,expected_authority,current_epoch,current_context;
    reg outcome_valid; reg [1:0] outcome_state; reg [7:0] outcome_authority,outcome_epoch,outcome_provenance,outcome_context,outcome_statement;
    reg [9:0] outcome_identity;

    wire busy_s,cv_s,ca_s,tv_s,ts_s;
    wire busy_b,cv_b,ca_b,tv_b,ts_b;
    wire busy_c,cv_c,ca_c,tv_c,ts_c;
    wire busy_p,cv_p,ca_p,tv_p,ts_p;

    pb_hw04_single_port_conventional s(.*,.busy(busy_s),.compose_valid(cv_s),.compose_allowed(ca_s),.terminal_valid(tv_s),.terminal_success(ts_s));
    pb_hw04_banked_conventional b(.*,.busy(busy_b),.compose_valid(cv_b),.compose_allowed(ca_b),.terminal_valid(tv_b),.terminal_success(ts_b));
    pb_hw04_multiport_conventional_cache c(.*,.busy(busy_c),.compose_valid(cv_c),.compose_allowed(ca_c),.terminal_valid(tv_c),.terminal_success(ts_c));
    pb_hw04_proofbit_cache p(.*,.busy(busy_p),.compose_valid(cv_p),.compose_allowed(ca_p),.terminal_valid(tv_p),.terminal_success(ts_p));

    integer failures=0;
    integer checks=0;
    integer cold_s,cold_b,cold_c,cold_p;
    integer warm_s,warm_b,warm_c,warm_p;
    integer conflict_s,conflict_b,conflict_c,conflict_p;
    integer conflict_warm_s,conflict_warm_b,conflict_warm_c,conflict_warm_p;
    integer invalid_s,invalid_b,invalid_c,invalid_p;
    integer replay_s,replay_b,replay_c,replay_p;

    function automatic [63:0] rec;
        input [1:0] st; input [7:0] auth; input [7:0] ep; input [9:0] id;
        input [7:0] prov; input [7:0] ctx; input [7:0] stmt;
        begin
            rec=64'h0;
            rec[1:0]=st; rec[9:2]=auth; rec[17:10]=ep; rec[27:18]=id;
            rec[35:28]=prov; rec[43:36]=ctx; rec[51:44]=stmt;
        end
    endfunction

    task automatic pulse_reset;
        begin
            reset=1; compose_start=0; outcome_valid=0; write_valid=0; invalidate_valid=0;
            repeat(2) @(posedge clk); #1; reset=0; @(posedge clk); #1;
        end
    endtask

    task automatic put;
        input [9:0] a; input [63:0] r;
        begin
            write_addr=a; write_record=r; write_valid=1; @(posedge clk); #1; write_valid=0;
        end
    endtask

    task automatic put_valid;
        input [9:0] a;
        begin put(a,rec(2'b01,8'h2a,8'h07,a,8'h55,8'h33,8'h10)); end
    endtask

    task automatic do_invalidate;
        input [9:0] a;
        begin invalidate_addr=a; invalidate_valid=1; @(posedge clk); #1; invalidate_valid=0; end
    endtask

    task automatic issue_compose;
        input [9:0] a0,a1,a2,a3; input [7:0] ds; input [9:0] did; input exp;
        output integer ls,lb,lc,lp;
        integer start;
        begin
            addr0=a0;addr1=a1;addr2=a2;addr3=a3;derived_statement=ds;derived_identity=did;
            compose_start=1; @(posedge clk); #1; compose_start=0; start=cycle;
            ls=-1;lb=-1;lc=-1;lp=-1;
            while(ls<0 || lb<0 || lc<0 || lp<0) begin
                @(posedge clk); #1;
                if(cv_s && ls<0) begin ls=cycle-start; checks=checks+1; if(ca_s!==exp) failures=failures+1; end
                if(cv_b && lb<0) begin lb=cycle-start; checks=checks+1; if(ca_b!==exp) failures=failures+1; end
                if(cv_c && lc<0) begin lc=cycle-start; checks=checks+1; if(ca_c!==exp) failures=failures+1; end
                if(cv_p && lp<0) begin lp=cycle-start; checks=checks+1; if(ca_p!==exp) failures=failures+1; end
            end
            if(lc!=lp) failures=failures+1;
        end
    endtask

    task automatic issue_outcome;
        input [1:0] st; input [9:0] did; input [7:0] stmt; input exp;
        begin
            outcome_state=st;outcome_identity=did;outcome_statement=stmt;outcome_valid=1;
            @(posedge clk); #1; outcome_valid=0;
            checks=checks+4;
            if(!(tv_s && ts_s===exp)) failures=failures+1;
            if(!(tv_b && ts_b===exp)) failures=failures+1;
            if(!(tv_c && ts_c===exp)) failures=failures+1;
            if(!(tv_p && ts_p===exp)) failures=failures+1;
        end
    endtask

    initial begin
        reset=0;write_valid=0;invalidate_valid=0;compose_start=0;outcome_valid=0;
        addr0=0;addr1=0;addr2=0;addr3=0;derived_statement=0;derived_identity=0;
        expected_statement=8'ha1;expected_authority=8'h2a;current_epoch=8'h07;current_context=8'h33;
        outcome_state=2'b01;outcome_authority=8'h2a;outcome_epoch=8'h07;outcome_provenance=8'h66;outcome_context=8'h33;outcome_statement=0;outcome_identity=0;

        pulse_reset();
        put_valid(10'd4);put_valid(10'd5);put_valid(10'd6);put_valid(10'd7);
        put_valid(10'd8);put_valid(10'd12);put_valid(10'd16);put_valid(10'd20);
        put_valid(10'd24);put_valid(10'd25);put_valid(10'd26);put_valid(10'd27);
        put_valid(10'd32);put_valid(10'd33);put_valid(10'd34);put_valid(10'd35);
        put_valid(10'd40);put_valid(10'd41);put_valid(10'd42);put_valid(10'd43);

        issue_compose(4,5,6,7,8'ha0,10'd100,0,cold_s,cold_b,cold_c,cold_p);
        issue_compose(4,5,6,7,8'ha1,10'd100,1,warm_s,warm_b,warm_c,warm_p);
        issue_outcome(2'b01,10'd100,8'ha1,1);

        pulse_reset();
        issue_compose(8,12,16,20,8'ha0,10'd101,0,conflict_s,conflict_b,conflict_c,conflict_p);
        issue_compose(8,12,16,20,8'ha1,10'd101,1,conflict_warm_s,conflict_warm_b,conflict_warm_c,conflict_warm_p);
        issue_outcome(2'b01,10'd101,8'ha1,1);

        pulse_reset();
        issue_compose(24,25,26,27,8'ha0,10'd102,0,invalid_s,invalid_b,invalid_c,invalid_p);
        put(10'd25,rec(2'b01,8'h2a,8'h06,10'd25,8'h55,8'h33,8'h10));
        do_invalidate(10'd25);
        issue_compose(24,25,26,27,8'ha1,10'd102,0,invalid_s,invalid_b,invalid_c,invalid_p);
        put_valid(10'd25);

        pulse_reset();
        issue_compose(32,33,34,35,8'ha1,10'd103,1,replay_s,replay_b,replay_c,replay_p);
        issue_outcome(2'b01,10'd103,8'ha1,1);
        issue_compose(32,33,34,35,8'ha1,10'd104,0,replay_s,replay_b,replay_c,replay_p);

        pulse_reset();
        issue_compose(40,41,42,43,8'ha1,10'd105,1,replay_s,replay_b,replay_c,replay_p);
        issue_outcome(2'b00,10'd105,8'ha1,0);

        if(failures==0 && warm_c<warm_b && warm_p==warm_c && conflict_b>cold_b && conflict_c<conflict_b && conflict_p==conflict_c) begin
            $display("PB_HW04_SIM PASS checks=%0d failures=%0d cold=%0d,%0d,%0d,%0d warm=%0d,%0d,%0d,%0d conflict=%0d,%0d,%0d,%0d conflict_warm=%0d,%0d,%0d,%0d invalidated=%0d,%0d,%0d,%0d", checks,failures,cold_s,cold_b,cold_c,cold_p,warm_s,warm_b,warm_c,warm_p,conflict_s,conflict_b,conflict_c,conflict_p,conflict_warm_s,conflict_warm_b,conflict_warm_c,conflict_warm_p,invalid_s,invalid_b,invalid_c,invalid_p);
        end else begin
            $display("PB_HW04_SIM FAIL checks=%0d failures=%0d cold=%0d,%0d,%0d,%0d warm=%0d,%0d,%0d,%0d conflict=%0d,%0d,%0d,%0d",checks,failures,cold_s,cold_b,cold_c,cold_p,warm_s,warm_b,warm_c,warm_p,conflict_s,conflict_b,conflict_c,conflict_p);
            $fatal(1);
        end
        $finish;
    end
endmodule

`timescale 1ns/1ps

module pb_hw04_check4(
    input wire [63:0] r0, r1, r2, r3,
    input wire [9:0] a0, a1, a2, a3,
    input wire [3:0] replay_hit,
    input wire [7:0] expected_authority,
    input wire [7:0] current_epoch,
    input wire [7:0] current_context,
    input wire [7:0] derived_statement,
    input wire [7:0] expected_statement,
    output wire good
);
    localparam [1:0] PROVEN_TRUE = 2'b01;
    function automatic parent_good;
        input [63:0] rec;
        input [9:0] addr;
        input replayed;
        begin
            parent_good =
                (rec[1:0] == PROVEN_TRUE) &&
                (rec[9:2] == expected_authority) &&
                (rec[17:10] == current_epoch) &&
                (rec[27:18] == addr) &&
                (rec[35:28] != 8'h00) &&
                (rec[43:36] == current_context) &&
                !replayed;
        end
    endfunction
    wire unique_addr = (a0 != a1) && (a0 != a2) && (a0 != a3) &&
                       (a1 != a2) && (a1 != a3) && (a2 != a3);
    assign good = parent_good(r0,a0,replay_hit[0]) &&
                  parent_good(r1,a1,replay_hit[1]) &&
                  parent_good(r2,a2,replay_hit[2]) &&
                  parent_good(r3,a3,replay_hit[3]) &&
                  unique_addr &&
                  (derived_statement == expected_statement);
endmodule

module pb_hw04_single_port_conventional(
    input wire clk, reset,
    input wire write_valid,
    input wire [9:0] write_addr,
    input wire [63:0] write_record,
    input wire compose_start,
    input wire [9:0] addr0, addr1, addr2, addr3,
    input wire [7:0] derived_statement,
    input wire [9:0] derived_identity,
    input wire [7:0] expected_statement,
    input wire [7:0] expected_authority,
    input wire [7:0] current_epoch,
    input wire [7:0] current_context,
    input wire outcome_valid,
    input wire [1:0] outcome_state,
    input wire [7:0] outcome_authority,
    input wire [7:0] outcome_epoch,
    input wire [7:0] outcome_provenance,
    input wire [7:0] outcome_context,
    input wire [7:0] outcome_statement,
    input wire [9:0] outcome_identity,
    output reg busy,
    output reg compose_valid,
    output reg compose_allowed,
    output reg terminal_valid,
    output reg terminal_success
);
    localparam [1:0] PROVEN_TRUE = 2'b01;
    localparam [2:0] IDLE=3'd0, R1=3'd1, R2=3'd2, R3=3'd3, CHECK=3'd4;
    (* ram_style = "block" *) reg [63:0] mem [0:1023];
    reg [2:0] state;
    reg [63:0] mem_r;
    reg [63:0] p0,p1,p2;
    reg [9:0] q0,q1,q2,q3;
    reg [7:0] q_derived_statement, q_expected_statement, q_expected_authority, q_epoch, q_context;
    reg [9:0] q_derived_identity;
    reg [1023:0] seen_parent;
    reg auth_valid;
    reg [9:0] auth_identity;
    reg [7:0] auth_statement;
    reg outcome_seen_valid;
    reg [9:0] outcome_seen_identity;

    wire mem_read_en = (state==IDLE && compose_start) || state==R1 || state==R2 || state==R3;
    wire [9:0] mem_read_addr = state==IDLE ? addr0 : state==R1 ? q1 : state==R2 ? q2 : q3;
    wire [3:0] replay_hit = {seen_parent[q3],seen_parent[q2],seen_parent[q1],seen_parent[q0]};
    wire compose_good;
    pb_hw04_check4 chk(.r0(p0),.r1(p1),.r2(p2),.r3(mem_r),
        .a0(q0),.a1(q1),.a2(q2),.a3(q3),.replay_hit(replay_hit),
        .expected_authority(q_expected_authority),.current_epoch(q_epoch),
        .current_context(q_context),.derived_statement(q_derived_statement),
        .expected_statement(q_expected_statement),.good(compose_good));

    wire outcome_good = auth_valid &&
        (outcome_identity == auth_identity) &&
        (outcome_statement == auth_statement) &&
        (outcome_state == PROVEN_TRUE) &&
        (outcome_authority == expected_authority) &&
        (outcome_epoch == current_epoch) &&
        (outcome_provenance != 8'h00) &&
        (outcome_context == current_context) &&
        !(outcome_seen_valid && outcome_seen_identity == outcome_identity);

    always @(posedge clk) begin
        if (write_valid)
            mem[write_addr] <= write_record;
        if (mem_read_en)
            mem_r <= mem[mem_read_addr];
        if (reset) begin
            state<=IDLE; busy<=0; compose_valid<=0; compose_allowed<=0;
            terminal_valid<=0; terminal_success<=0; seen_parent<=0;
            auth_valid<=0; outcome_seen_valid<=0; auth_identity<=0; auth_statement<=0;
            outcome_seen_identity<=0;
        end else begin
            compose_valid<=0; compose_allowed<=0; terminal_valid<=0; terminal_success<=0;
            if (outcome_valid) begin
                terminal_valid<=1;
                terminal_success<=outcome_good;
                if (outcome_good) begin outcome_seen_valid<=1; outcome_seen_identity<=outcome_identity; end
                if (auth_valid && outcome_identity==auth_identity) auth_valid<=0;
            end
            case(state)
                IDLE: if (compose_start) begin
                    q0<=addr0; q1<=addr1; q2<=addr2; q3<=addr3;
                    q_derived_statement<=derived_statement; q_derived_identity<=derived_identity;
                    q_expected_statement<=expected_statement; q_expected_authority<=expected_authority;
                    q_epoch<=current_epoch; q_context<=current_context;
                    busy<=1; state<=R1;
                end
                R1: begin p0<=mem_r; state<=R2; end
                R2: begin p1<=mem_r; state<=R3; end
                R3: begin p2<=mem_r; state<=CHECK; end
                CHECK: begin
                    compose_valid<=1; compose_allowed<=compose_good; busy<=0; state<=IDLE; auth_valid<=0;
                    if (compose_good) begin
                        seen_parent[q0]<=1; seen_parent[q1]<=1; seen_parent[q2]<=1; seen_parent[q3]<=1;
                        auth_valid<=1; auth_identity<=q_derived_identity; auth_statement<=q_derived_statement;
                    end
                end
                default: state<=IDLE;
            endcase
        end
    end
endmodule

module pb_hw04_banked_conventional(
    input wire clk, reset,
    input wire write_valid,
    input wire [9:0] write_addr,
    input wire [63:0] write_record,
    input wire compose_start,
    input wire [9:0] addr0, addr1, addr2, addr3,
    input wire [7:0] derived_statement,
    input wire [9:0] derived_identity,
    input wire [7:0] expected_statement,
    input wire [7:0] expected_authority,
    input wire [7:0] current_epoch,
    input wire [7:0] current_context,
    input wire outcome_valid,
    input wire [1:0] outcome_state,
    input wire [7:0] outcome_authority,
    input wire [7:0] outcome_epoch,
    input wire [7:0] outcome_provenance,
    input wire [7:0] outcome_context,
    input wire [7:0] outcome_statement,
    input wire [9:0] outcome_identity,
    output reg busy,
    output reg compose_valid,
    output reg compose_allowed,
    output reg terminal_valid,
    output reg terminal_success
);
    localparam [1:0] PROVEN_TRUE=2'b01;
    localparam [1:0] IDLE=2'd0, READ=2'd1;
    (* ram_style = "block" *) reg [63:0] bank0 [0:255];
    (* ram_style = "block" *) reg [63:0] bank1 [0:255];
    (* ram_style = "block" *) reg [63:0] bank2 [0:255];
    (* ram_style = "block" *) reg [63:0] bank3 [0:255];
    reg [63:0] bank_r0,bank_r1,bank_r2,bank_r3;
    reg [1:0] state;
    reg [3:0] pending,return_mask;
    reg [63:0] p0,p1,p2,p3;
    reg [9:0] q0,q1,q2,q3;
    reg [7:0] q_derived_statement, q_expected_statement, q_expected_authority, q_epoch, q_context;
    reg [9:0] q_derived_identity;
    reg [1023:0] seen_parent;
    reg auth_valid; reg [9:0] auth_identity; reg [7:0] auth_statement;
    reg outcome_seen_valid; reg [9:0] outcome_seen_identity;

    wire [1:0] b0=q0[1:0], b1=q1[1:0], b2=q2[1:0], b3=q3[1:0];
    wire serve0 = pending[0];
    wire serve1 = pending[1] && !(pending[0] && b0==b1);
    wire serve2 = pending[2] && !(pending[0] && b0==b2) && !(pending[1] && b1==b2);
    wire serve3 = pending[3] && !(pending[0] && b0==b3) && !(pending[1] && b1==b3) && !(pending[2] && b2==b3);
    wire [3:0] serve_mask={serve3,serve2,serve1,serve0};
    wire [3:0] next_pending=pending & ~serve_mask;

    wire issue_b0=(serve0&&b0==0)||(serve1&&b1==0)||(serve2&&b2==0)||(serve3&&b3==0);
    wire issue_b1=(serve0&&b0==1)||(serve1&&b1==1)||(serve2&&b2==1)||(serve3&&b3==1);
    wire issue_b2=(serve0&&b0==2)||(serve1&&b1==2)||(serve2&&b2==2)||(serve3&&b3==2);
    wire issue_b3=(serve0&&b0==3)||(serve1&&b1==3)||(serve2&&b2==3)||(serve3&&b3==3);
    wire [7:0] bank_addr0=(serve0&&b0==0)?q0[9:2]:(serve1&&b1==0)?q1[9:2]:(serve2&&b2==0)?q2[9:2]:q3[9:2];
    wire [7:0] bank_addr1=(serve0&&b0==1)?q0[9:2]:(serve1&&b1==1)?q1[9:2]:(serve2&&b2==1)?q2[9:2]:q3[9:2];
    wire [7:0] bank_addr2=(serve0&&b0==2)?q0[9:2]:(serve1&&b1==2)?q1[9:2]:(serve2&&b2==2)?q2[9:2]:q3[9:2];
    wire [7:0] bank_addr3=(serve0&&b0==3)?q0[9:2]:(serve1&&b1==3)?q1[9:2]:(serve2&&b2==3)?q2[9:2]:q3[9:2];

    wire [63:0] ret0=b0==0?bank_r0:b0==1?bank_r1:b0==2?bank_r2:bank_r3;
    wire [63:0] ret1=b1==0?bank_r0:b1==1?bank_r1:b1==2?bank_r2:bank_r3;
    wire [63:0] ret2=b2==0?bank_r0:b2==1?bank_r1:b2==2?bank_r2:bank_r3;
    wire [63:0] ret3=b3==0?bank_r0:b3==1?bank_r1:b3==2?bank_r2:bank_r3;
    wire [63:0] c0=return_mask[0]?ret0:p0;
    wire [63:0] c1=return_mask[1]?ret1:p1;
    wire [63:0] c2=return_mask[2]?ret2:p2;
    wire [63:0] c3=return_mask[3]?ret3:p3;
    wire [3:0] replay_hit={seen_parent[q3],seen_parent[q2],seen_parent[q1],seen_parent[q0]};
    wire compose_good;
    pb_hw04_check4 chk(.r0(c0),.r1(c1),.r2(c2),.r3(c3),.a0(q0),.a1(q1),.a2(q2),.a3(q3),
        .replay_hit(replay_hit),.expected_authority(q_expected_authority),.current_epoch(q_epoch),
        .current_context(q_context),.derived_statement(q_derived_statement),
        .expected_statement(q_expected_statement),.good(compose_good));
    wire outcome_good = auth_valid && outcome_identity==auth_identity && outcome_statement==auth_statement &&
        outcome_state==PROVEN_TRUE && outcome_authority==expected_authority && outcome_epoch==current_epoch &&
        outcome_provenance!=0 && outcome_context==current_context &&
        !(outcome_seen_valid && outcome_seen_identity==outcome_identity);

    always @(posedge clk) begin
        if (write_valid) begin
            case(write_addr[1:0])
                2'd0: bank0[write_addr[9:2]]<=write_record;
                2'd1: bank1[write_addr[9:2]]<=write_record;
                2'd2: bank2[write_addr[9:2]]<=write_record;
                default: bank3[write_addr[9:2]]<=write_record;
            endcase
        end
        if(state==READ) begin
            if(issue_b0) bank_r0<=bank0[bank_addr0];
            if(issue_b1) bank_r1<=bank1[bank_addr1];
            if(issue_b2) bank_r2<=bank2[bank_addr2];
            if(issue_b3) bank_r3<=bank3[bank_addr3];
        end
        if (reset) begin
            state<=IDLE; pending<=0; return_mask<=0; busy<=0; compose_valid<=0; compose_allowed<=0;
            terminal_valid<=0; terminal_success<=0; seen_parent<=0; auth_valid<=0;
            outcome_seen_valid<=0; auth_identity<=0; auth_statement<=0; outcome_seen_identity<=0;
        end else begin
            compose_valid<=0; compose_allowed<=0; terminal_valid<=0; terminal_success<=0;
            if (outcome_valid) begin
                terminal_valid<=1; terminal_success<=outcome_good;
                if(outcome_good) begin outcome_seen_valid<=1; outcome_seen_identity<=outcome_identity; end
                if(auth_valid && outcome_identity==auth_identity) auth_valid<=0;
            end
            case(state)
                IDLE: if(compose_start) begin
                    q0<=addr0; q1<=addr1; q2<=addr2; q3<=addr3; pending<=4'b1111; return_mask<=0;
                    q_derived_statement<=derived_statement; q_derived_identity<=derived_identity;
                    q_expected_statement<=expected_statement; q_expected_authority<=expected_authority;
                    q_epoch<=current_epoch; q_context<=current_context; busy<=1; state<=READ;
                end
                READ: begin
                    if(return_mask[0]) p0<=ret0;
                    if(return_mask[1]) p1<=ret1;
                    if(return_mask[2]) p2<=ret2;
                    if(return_mask[3]) p3<=ret3;
                    if(pending==0 && return_mask!=0) begin
                        compose_valid<=1; compose_allowed<=compose_good; busy<=0; state<=IDLE;
                        pending<=0; return_mask<=0; auth_valid<=0;
                        if(compose_good) begin
                            seen_parent[q0]<=1; seen_parent[q1]<=1; seen_parent[q2]<=1; seen_parent[q3]<=1;
                            auth_valid<=1; auth_identity<=q_derived_identity; auth_statement<=q_derived_statement;
                        end
                    end else begin
                        pending<=next_pending;
                        return_mask<=serve_mask;
                    end
                end
                default: state<=IDLE;
            endcase
        end
    end
endmodule

module pb_hw04_cached_core(
    input wire clk, reset,
    input wire write_valid,
    input wire [9:0] write_addr,
    input wire [63:0] write_record,
    input wire invalidate_valid,
    input wire [9:0] invalidate_addr,
    input wire compose_start,
    input wire [9:0] addr0, addr1, addr2, addr3,
    input wire [7:0] derived_statement,
    input wire [9:0] derived_identity,
    input wire [7:0] expected_statement,
    input wire [7:0] expected_authority,
    input wire [7:0] current_epoch,
    input wire [7:0] current_context,
    input wire outcome_valid,
    input wire [1:0] outcome_state,
    input wire [7:0] outcome_authority,
    input wire [7:0] outcome_epoch,
    input wire [7:0] outcome_provenance,
    input wire [7:0] outcome_context,
    input wire [7:0] outcome_statement,
    input wire [9:0] outcome_identity,
    output reg busy,
    output reg compose_valid,
    output reg compose_allowed,
    output reg terminal_valid,
    output reg terminal_success
);
    localparam [1:0] PROVEN_TRUE=2'b01;
    localparam [1:0] IDLE=2'd0, MISS_WAIT=2'd1, CHECK=2'd2;
    (* ram_style = "block" *) reg [63:0] mem0 [0:1023];
    (* ram_style = "block" *) reg [63:0] mem1 [0:1023];
    (* ram_style = "block" *) reg [63:0] mem2 [0:1023];
    (* ram_style = "block" *) reg [63:0] mem3 [0:1023];

    reg [63:0] mem_r0,mem_r1,mem_r2,mem_r3;
    reg [15:0] cache_valid;
    reg [5:0] cache_tag [0:15];
    reg [63:0] cache_data [0:15];

    reg [1:0] state;
    reg [3:0] q_hit;
    reg [63:0] p0,p1,p2,p3;
    reg [9:0] q0,q1,q2,q3;
    reg [7:0] q_derived_statement,q_expected_statement,q_expected_authority,q_epoch,q_context;
    reg [9:0] q_derived_identity;
    reg [1023:0] seen_parent;
    reg auth_valid; reg [9:0] auth_identity; reg [7:0] auth_statement;
    reg outcome_seen_valid; reg [9:0] outcome_seen_identity;

    wire [3:0] i0=addr0[3:0], i1=addr1[3:0], i2=addr2[3:0], i3=addr3[3:0];
    wire h0=cache_valid[i0] && cache_tag[i0]==addr0[9:4];
    wire h1=cache_valid[i1] && cache_tag[i1]==addr1[9:4];
    wire h2=cache_valid[i2] && cache_tag[i2]==addr2[9:4];
    wire h3=cache_valid[i3] && cache_tag[i3]==addr3[9:4];
    wire all_hit=h0&&h1&&h2&&h3;

    wire [3:0] replay_hit={seen_parent[q3],seen_parent[q2],seen_parent[q1],seen_parent[q0]};
    wire compose_good;
    pb_hw04_check4 chk(.r0(p0),.r1(p1),.r2(p2),.r3(p3),.a0(q0),.a1(q1),.a2(q2),.a3(q3),
        .replay_hit(replay_hit),.expected_authority(q_expected_authority),.current_epoch(q_epoch),
        .current_context(q_context),.derived_statement(q_derived_statement),
        .expected_statement(q_expected_statement),.good(compose_good));
    wire outcome_good = auth_valid && outcome_identity==auth_identity && outcome_statement==auth_statement &&
        outcome_state==PROVEN_TRUE && outcome_authority==expected_authority && outcome_epoch==current_epoch &&
        outcome_provenance!=0 && outcome_context==current_context &&
        !(outcome_seen_valid && outcome_seen_identity==outcome_identity);

    always @(posedge clk) begin
        if(write_valid) begin
            mem0[write_addr]<=write_record; mem1[write_addr]<=write_record;
            mem2[write_addr]<=write_record; mem3[write_addr]<=write_record;
            if(cache_valid[write_addr[3:0]] && cache_tag[write_addr[3:0]]==write_addr[9:4])
                cache_valid[write_addr[3:0]]<=0;
        end
        if(compose_start) begin
            mem_r0<=mem0[addr0];
            mem_r1<=mem1[addr1];
            mem_r2<=mem2[addr2];
            mem_r3<=mem3[addr3];
        end
        if(invalidate_valid && cache_valid[invalidate_addr[3:0]] &&
           cache_tag[invalidate_addr[3:0]]==invalidate_addr[9:4])
            cache_valid[invalidate_addr[3:0]]<=0;

        if(reset) begin
            state<=IDLE; q_hit<=0; busy<=0; compose_valid<=0; compose_allowed<=0;
            terminal_valid<=0; terminal_success<=0; cache_valid<=0; seen_parent<=0;
            auth_valid<=0; outcome_seen_valid<=0; auth_identity<=0; auth_statement<=0; outcome_seen_identity<=0;
        end else begin
            compose_valid<=0; compose_allowed<=0; terminal_valid<=0; terminal_success<=0;
            if(outcome_valid) begin
                terminal_valid<=1; terminal_success<=outcome_good;
                if(outcome_good) begin outcome_seen_valid<=1; outcome_seen_identity<=outcome_identity; end
                if(auth_valid && outcome_identity==auth_identity) auth_valid<=0;
            end
            case(state)
                IDLE: if(compose_start) begin
                    q0<=addr0; q1<=addr1; q2<=addr2; q3<=addr3;
                    q_hit<={h3,h2,h1,h0};
                    q_derived_statement<=derived_statement; q_derived_identity<=derived_identity;
                    q_expected_statement<=expected_statement; q_expected_authority<=expected_authority;
                    q_epoch<=current_epoch; q_context<=current_context; busy<=1;
                    if(h0) p0<=cache_data[i0];
                    if(h1) p1<=cache_data[i1];
                    if(h2) p2<=cache_data[i2];
                    if(h3) p3<=cache_data[i3];
                    state <= all_hit ? CHECK : MISS_WAIT;
                end
                MISS_WAIT: begin
                    if(!q_hit[0]) begin p0<=mem_r0; cache_data[q0[3:0]]<=mem_r0; cache_tag[q0[3:0]]<=q0[9:4]; cache_valid[q0[3:0]]<=1; end
                    if(!q_hit[1]) begin p1<=mem_r1; cache_data[q1[3:0]]<=mem_r1; cache_tag[q1[3:0]]<=q1[9:4]; cache_valid[q1[3:0]]<=1; end
                    if(!q_hit[2]) begin p2<=mem_r2; cache_data[q2[3:0]]<=mem_r2; cache_tag[q2[3:0]]<=q2[9:4]; cache_valid[q2[3:0]]<=1; end
                    if(!q_hit[3]) begin p3<=mem_r3; cache_data[q3[3:0]]<=mem_r3; cache_tag[q3[3:0]]<=q3[9:4]; cache_valid[q3[3:0]]<=1; end
                    state<=CHECK;
                end
                CHECK: begin
                    compose_valid<=1; compose_allowed<=compose_good; busy<=0; state<=IDLE; auth_valid<=0;
                    if(compose_good) begin
                        seen_parent[q0]<=1; seen_parent[q1]<=1; seen_parent[q2]<=1; seen_parent[q3]<=1;
                        auth_valid<=1; auth_identity<=q_derived_identity; auth_statement<=q_derived_statement;
                    end
                end
                default: state<=IDLE;
            endcase
        end
    end
endmodule

module pb_hw04_multiport_conventional_cache(
    input wire clk, reset, input wire write_valid, input wire [9:0] write_addr, input wire [63:0] write_record,
    input wire invalidate_valid, input wire [9:0] invalidate_addr, input wire compose_start,
    input wire [9:0] addr0,addr1,addr2,addr3, input wire [7:0] derived_statement, input wire [9:0] derived_identity,
    input wire [7:0] expected_statement,expected_authority,current_epoch,current_context,
    input wire outcome_valid, input wire [1:0] outcome_state, input wire [7:0] outcome_authority,outcome_epoch,
    input wire [7:0] outcome_provenance,outcome_context,outcome_statement, input wire [9:0] outcome_identity,
    output wire busy,compose_valid,compose_allowed,terminal_valid,terminal_success
);
    pb_hw04_cached_core u(.*);
endmodule

module pb_hw04_proofbit_cache(
    input wire clk, reset, input wire write_valid, input wire [9:0] write_addr, input wire [63:0] write_record,
    input wire invalidate_valid, input wire [9:0] invalidate_addr, input wire compose_start,
    input wire [9:0] addr0,addr1,addr2,addr3, input wire [7:0] derived_statement, input wire [9:0] derived_identity,
    input wire [7:0] expected_statement,expected_authority,current_epoch,current_context,
    input wire outcome_valid, input wire [1:0] outcome_state, input wire [7:0] outcome_authority,outcome_epoch,
    input wire [7:0] outcome_provenance,outcome_context,outcome_statement, input wire [9:0] outcome_identity,
    output wire busy,compose_valid,compose_allowed,terminal_valid,terminal_success
);
    pb_hw04_cached_core u(.*);
endmodule

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
    reg [63:0] p0,p1,p2,p3;
    reg [9:0] q0,q1,q2,q3;
    reg [7:0] q_derived_statement, q_expected_statement, q_expected_authority, q_epoch, q_context;
    reg [9:0] q_derived_identity;
    reg [1023:0] seen_parent;
    reg auth_valid;
    reg [9:0] auth_identity;
    reg [7:0] auth_statement;
    reg outcome_seen_valid;
    reg [9:0] outcome_seen_identity;

    wire [3:0] replay_hit = {seen_parent[q3],seen_parent[q2],seen_parent[q1],seen_parent[q0]};
    wire compose_good;
    pb_hw04_check4 chk(.r0(p0),.r1(p1),.r2(p2),.r3(p3),
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
                    p0<=mem[addr0]; busy<=1; state<=R1;
                end
                R1: begin p1<=mem[q1]; state<=R2; end
                R2: begin p2<=mem[q2]; state<=R3; end
                R3: begin p3<=mem[q3]; state<=CHECK; end
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
    localparam [1:0] IDLE=2'd0, READ=2'd1, CHECK=2'd2;
    (* ram_style = "block" *) reg [63:0] bank0 [0:255];
    (* ram_style = "block" *) reg [63:0] bank1 [0:255];
    (* ram_style = "block" *) reg [63:0] bank2 [0:255];
    (* ram_style = "block" *) reg [63:0] bank3 [0:255];
    reg [1:0] state;
    reg [3:0] pending;
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
        if (write_valid) begin
            case(write_addr[1:0])
                2'd0: bank0[write_addr[9:2]]<=write_record;
                2'd1: bank1[write_addr[9:2]]<=write_record;
                2'd2: bank2[write_addr[9:2]]<=write_record;
                default: bank3[write_addr[9:2]]<=write_record;
            endcase
        end
        if (reset) begin
            state<=IDLE; pending<=0; busy<=0; compose_valid<=0; compose_allowed<=0;
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
                    q0<=addr0; q1<=addr1; q2<=addr2; q3<=addr3; pending<=4'b1111;
                    q_derived_statement<=derived_statement; q_derived_identity<=derived_identity;
                    q_expected_statement<=expected_statement; q_expected_authority<=expected_authority;
                    q_epoch<=current_epoch; q_context<=current_context; busy<=1; state<=READ;
                end
                READ: begin
                    if(serve0) case(b0)
                        0:p0<=bank0[q0[9:2]];1:p0<=bank1[q0[9:2]];2:p0<=bank2[q0[9:2]];default:p0<=bank3[q0[9:2]];
                    endcase
                    if(serve1) case(b1)
                        0:p1<=bank0[q1[9:2]];1:p1<=bank1[q1[9:2]];2:p1<=bank2[q1[9:2]];default:p1<=bank3[q1[9:2]];
                    endcase
                    if(serve2) case(b2)
                        0:p2<=bank0[q2[9:2]];1:p2<=bank1[q2[9:2]];2:p2<=bank2[q2[9:2]];default:p2<=bank3[q2[9:2]];
                    endcase
                    if(serve3) case(b3)
                        0:p3<=bank0[q3[9:2]];1:p3<=bank1[q3[9:2]];2:p3<=bank2[q3[9:2]];default:p3<=bank3[q3[9:2]];
                    endcase
                    pending<=next_pending;
                    if(next_pending==0) state<=CHECK;
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

    reg [15:0] cache_valid;
    reg [5:0] cache_tag [0:15];
    reg [63:0] cache_data [0:15];

    reg [1:0] state;
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
        if(invalidate_valid && cache_valid[invalidate_addr[3:0]] &&
           cache_tag[invalidate_addr[3:0]]==invalidate_addr[9:4])
            cache_valid[invalidate_addr[3:0]]<=0;

        if(reset) begin
            state<=IDLE; busy<=0; compose_valid<=0; compose_allowed<=0;
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
                    q_derived_statement<=derived_statement; q_derived_identity<=derived_identity;
                    q_expected_statement<=expected_statement; q_expected_authority<=expected_authority;
                    q_epoch<=current_epoch; q_context<=current_context; busy<=1;
                    p0 <= h0 ? cache_data[i0] : mem0[addr0];
                    p1 <= h1 ? cache_data[i1] : mem1[addr1];
                    p2 <= h2 ? cache_data[i2] : mem2[addr2];
                    p3 <= h3 ? cache_data[i3] : mem3[addr3];
                    if(!h0) begin cache_data[i0]<=mem0[addr0]; cache_tag[i0]<=addr0[9:4]; cache_valid[i0]<=1; end
                    if(!h1) begin cache_data[i1]<=mem1[addr1]; cache_tag[i1]<=addr1[9:4]; cache_valid[i1]<=1; end
                    if(!h2) begin cache_data[i2]<=mem2[addr2]; cache_tag[i2]<=addr2[9:4]; cache_valid[i2]<=1; end
                    if(!h3) begin cache_data[i3]<=mem3[addr3]; cache_tag[i3]<=addr3[9:4]; cache_valid[i3]<=1; end
                    state <= all_hit ? CHECK : MISS_WAIT;
                end
                MISS_WAIT: state<=CHECK;
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

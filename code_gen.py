from ast import Str
import port_def


def generate_header_string(top_name):
    header_str  = "#include \"verilog_interface.h\"\n"
    header_str += "#include <assert.h>\n"
    header_str += "#include <stdbool.h>\n"
    header_str += "#include <stdio.h>\n"
    header_str += "#include \"{}_refine.c\"\n".format(top_name)            
    return header_str


def generate_general_variable_definition():
    gvd_str = ""
    gvd_str += "\tint i;\n"
    gvd_str += "\tint t;\n"
    return gvd_str


def generate_C_variable_definition(port_list_C, return_type_C:str):
    c_var_def_str = ""
    for port_c in port_list_C:
        port_c:port_def.PortC
        if not port_c.is_array:
            c_var_def_str += "\t{} {}_c;\n".format(port_c.type, port_c.name)
        else:
            c_var_def_str += "\t{} {}_c[{}];\n".format(port_c.type, port_c.name, port_c.array_length)
    
    if return_type_C.find("void") == -1 and return_type_C:
        c_var_def_str += "\t{} _c_ret;\n".format(return_type_C)
    
    return c_var_def_str

def generate_verilog_variable_definition(port_list_C, return_type_C):
    # verilog inputs in c, so it should use C port list
    v_var_def_str = ""
    for port_c in port_list_C:
        port_c:port_def.PortC
        if not port_c.is_array:
            v_var_def_str += "\t{} {}_v;\n".format(port_c.type, port_c.name)
        else:
            v_var_def_str += "\t{} {}_v[{}];\n".format(port_c.type, port_c.name, port_c.array_length)
    
    if return_type_C.find("void") == -1 and return_type_C:
        v_var_def_str += "\t{} _v_ret;\n".format(return_type_C)
    
    return v_var_def_str


def generate_C_verilog_result_assertion(port_list_C, return_type_C):
    assert_str = ""
    for port_c in port_list_C:
        port_c:port_def.PortC
        if not port_c.is_array:
            assert_str += "\tassert({}_c == {}_v);\n".format(port_c.name, port_c.name)
        else:
            assert_str += "\tfor (i = 0; i < {}; i++)\n".format(port_c.array_length)
            assert_str += "\t{\n"
            assert_str += "\t\tassert({}_c[i] == {}_v[i]);\n".format(port_c.name, port_c.name)
            assert_str += "\t}\n"
    if return_type_C.find("void") == -1 and return_type_C:
        assert_str += "\tassert(_c_ret == _v_ret);\n"
    
    return assert_str


def generate_C_RTL_input_assignment(top_name, port_list_RTL, port_list_C, return_type_C):
    
    input_assign_str = ""
    for port_c in port_list_C:
        port_c:port_def.PortC
        if port_c.is_array:
            input_assign_str += "\tfor (i = 0; i < {}; i++)\n".format(port_c.array_length)
            input_assign_str += "\t{\n"
            input_assign_str += "\t\t{}_v[i] = {}_c[i];\n".format(port_c.name, port_c.name)
            input_assign_str += "\t}\n"
        else:
            input_assign_str += "\t{}_v = {}_c;\n".format(port_c.name, port_c.name)
    return input_assign_str


def generate_C_execution(top_name, port_list_RTL, port_list_C, return_type_C):
    exec_C_str = ""
    param_C_str = ""
    for i in range(len(port_list_C)):
        port_c_tmp = port_list_C[i]
        port_c_tmp:port_def.PortC
        param_C_str += (port_c_tmp.name + "_c")
        if i != len(port_list_C)-1:
            param_C_str += ", "
    if return_type_C.find("void") == -1 and return_type_C:
        # has return variable
        exec_C_str += "\t_c_ret = {}_c({});\n".format(top_name, param_C_str)
    else:
        exec_C_str += "\t{}_c({});\n".format(top_name, param_C_str)
        
    return exec_C_str

def generate_RTL_initiailze_logic(top_name, port_list_RTL, port_list_C, return_type_C):
    
    has_ap_start = 0
    has_ap_rst = 0
    
    for port_rtl in port_list_RTL:
        port_rtl:port_def.PortRTL
        if port_rtl.name == "ap_start":
            has_ap_start = 1
        if port_rtl.name == "ap_rst":
            has_ap_rst = 1
    
    init_RTL_str = ""
    
    if has_ap_rst:
        init_RTL_str += "\t{}.ap_rst = 1;\n".format(top_name)
    if has_ap_start:
        init_RTL_str += "\t{}.ap_start = 0;\n".format(top_name)
    init_RTL_str += "\tset_inputs();\n"
    init_RTL_str += "\tnext_timeframe();\n"
    
    if has_ap_rst:
        init_RTL_str += "\t{}.ap_rst = 1;\n".format(top_name)
    if has_ap_start:
        init_RTL_str += "\t{}.ap_start = 0;\n".format(top_name)
    init_RTL_str += "\tset_inputs();\n"
    init_RTL_str += "\tnext_timeframe();\n"
    
    if has_ap_rst:
        init_RTL_str += "\t{}.ap_rst = 0;\n".format(top_name)
    if has_ap_start:
        init_RTL_str += "\t{}.ap_start = 0;\n".format(top_name)
    init_RTL_str += "\t\tset_inputs();\n"
    init_RTL_str += "\t\tnext_timeframe();\n"
    
    return init_RTL_str

def detect_RTL_branch (top_name, port_list_RTL, port_list_C, return_type_C):
    RTL_branch_list = []
    
    for port_c in port_list_C:
        for port_rtl in port_list_RTL:
            port_c:port_def.PortC
            port_rtl:port_def.PortRTL
        
            # (name, "memory"/"scalar", "read/write", "index")
            
            if port_rtl.name.find("{}_d0".format(port_c.name)) == 0:
                RTL_branch_list.append((port_c.name, "memory", "write", "0", port_c.type))
            if port_rtl.name.find("{}_d1".format(port_c.name)) == 0:
                RTL_branch_list.append((port_c.name, "memory", "write", "1", port_c.type))
            
            if port_rtl.name.find("{}_q0".format(port_c.name)) == 0:
                RTL_branch_list.append((port_c.name, "memory", "read", "0", port_c.type))
            if port_rtl.name.find("{}_q1".format(port_c.name)) == 0:
                RTL_branch_list.append((port_c.name, "memory", "read", "1", port_c.type))
            
            if port_rtl.name == port_c.name:
                RTL_branch_list.append((port_c.name, "scalar", "", "", port_c.type))


    return RTL_branch_list


def generate_RTL_latency_model(top_name, port_list_RTL, port_list_C, return_type_C, RTL_branch_list):
    RTL_lat_model_str = ""
    for rtl_branch in RTL_branch_list:
        if rtl_branch[1] == "memory" and rtl_branch[2] == "read":
            RTL_lat_model_str += "\tbool {}_q{}_read = 0;\n".format(rtl_branch[0], rtl_branch[3])
            RTL_lat_model_str += "\t{} {}_q{}_reg = 0;\n".format(rtl_branch[4], rtl_branch[0], rtl_branch[3])
    
    return RTL_lat_model_str


def generate_RTL_wrapper_logic(top_name, port_list_RTL, port_list_C, return_type_C, RTL_branch_list):
    RTL_wrapper_str = ""
    
    has_ap_start = 0
    has_ap_rst = 0
    
    for port_rtl in port_list_RTL:
        port_rtl:port_def.PortRTL
        if port_rtl.name == "ap_start":
            has_ap_start = 1
        if port_rtl.name == "ap_rst":
            has_ap_rst = 1
    
    # hold start signal
    if has_ap_start:
        RTL_wrapper_str += "\t\t{}.ap_start = 1;\n".format(top_name)
    if has_ap_rst:
        RTL_wrapper_str += "\t\t{}.ap_rst = 0;\n".format(top_name)
    
    # break condition
    # RTL_wrapper_str += "\t\tif({}.ap_done == 1)\n".format(top_name)
    # RTL_wrapper_str += "\t\t{\n"
    # if return_type_C.find("void") != 0:
    #     RTL_wrapper_str += "\t\t\t_v_ret = {}.ap_return;\n".format(top_name)
    # RTL_wrapper_str += "\t\t\tbreak;\n"
    # RTL_wrapper_str += "\t\t}\n"
    
    # respond to ports
    for rtl_branch in RTL_branch_list:
        # respond to read memory
        if rtl_branch[1] == "memory" and rtl_branch[2] == "read":
            RTL_wrapper_str += "\t\tif({}_q{}_read)\n".format(rtl_branch[0], rtl_branch[3])
            RTL_wrapper_str += "\t\t{\n"
            RTL_wrapper_str += "\t\t\t{}.{}_q{} = {}_q{}_reg;\n".format(top_name, rtl_branch[0], rtl_branch[3], rtl_branch[0], rtl_branch[3])
            RTL_wrapper_str += "\t\t\t{}_q{}_read = 0;\n".format(rtl_branch[0], rtl_branch[3])
            RTL_wrapper_str += "\t\t}\n"
            RTL_wrapper_str += "\t\tif({}.{}_ce{})\n".format(top_name, rtl_branch[0], rtl_branch[3])
            RTL_wrapper_str += "\t\t{\n"
            RTL_wrapper_str += "\t\t\tint {}_address{} = {}.{}_address{};\n".format(rtl_branch[0], rtl_branch[3], top_name, rtl_branch[0], rtl_branch[3])
            RTL_wrapper_str += "\t\t\t{}_q{}_reg = {}_v[{}_address{}];\n".format(rtl_branch[0], rtl_branch[3], rtl_branch[0], rtl_branch[0], rtl_branch[3])
            RTL_wrapper_str += "\t\t\t{}_q{}_read = 1;\n".format(rtl_branch[0], rtl_branch[3])
            RTL_wrapper_str += "\t\t}\n"
            
        # respond to write memory
        if rtl_branch[1] == "memory" and rtl_branch[2] == "write":
            RTL_wrapper_str += "\t\tif({}.{}_we{})\n".format(top_name, rtl_branch[0], rtl_branch[3])
            RTL_wrapper_str += "\t\t{\n"
            RTL_wrapper_str += "\t\t\tint {}_address{} = {}.{}_address{};\n".format(rtl_branch[0], rtl_branch[3], top_name, rtl_branch[0], rtl_branch[3])
            RTL_wrapper_str += "\t\t\t{}_v[{}_address{}] = {}.{}_d{};\n".format(rtl_branch[0], rtl_branch[0], rtl_branch[3], top_name, rtl_branch[0], rtl_branch[3])
            RTL_wrapper_str += "\t\t}\n"
        
        # respond to ap_none
        if rtl_branch[1] == "scalar":
            RTL_wrapper_str += "\t\t{}.{} = {}_v;\n".format(top_name, rtl_branch[0], rtl_branch[0])
    return RTL_wrapper_str



def generate_loop_body(top_name, port_list_RTL, port_list_C, return_type_C, RTL_branch_list):
    # also contains the initialization of ap_start
    loop_body_str = ""
    loop_body_str += "\t{}.ap_start = 1;\n".format(top_name)
    loop_body_str += "\tfor(t=0; t < bound; t++)\n"
    loop_body_str += "\t{\n"
    loop_body_str += generate_RTL_wrapper_logic(top_name, port_list_RTL, port_list_C, return_type_C, RTL_branch_list)
    loop_body_str += "\tset_inputs();\n"
    # break condition
    loop_body_str += "\t\tif({}.ap_done == 1)\n".format(top_name)
    loop_body_str += "\t\t{\n"
    if return_type_C.find("void") != 0:
        loop_body_str += "\t\t\t_v_ret = {}.ap_return;\n".format(top_name)
    loop_body_str += "\t\t\tbreak;\n"
    loop_body_str += "\t\t}\n"
    loop_body_str += "\tnext_timeframe();\n"
    loop_body_str += "\t}\n"
    return loop_body_str

def generate_main_body(top_name, port_list_RTL, port_list_C, return_type_C):
    main_str = ""
    main_str += "int main()\n"
    main_str += "{\n"
    # definitions
    main_str += generate_general_variable_definition()
    main_str += generate_C_variable_definition(port_list_C, return_type_C)
    main_str += generate_verilog_variable_definition(port_list_C, return_type_C)
    
    # assignment
    main_str += generate_C_RTL_input_assignment(top_name, port_list_RTL, port_list_C, return_type_C)
    
    # C exe
    main_str += generate_C_execution(top_name, port_list_RTL, port_list_C, return_type_C)
    
    # RTL init
    main_str += generate_RTL_initiailze_logic(top_name, port_list_RTL, port_list_C, return_type_C)
    
    # memory port declare
    RTL_branch_list = detect_RTL_branch (top_name, port_list_RTL, port_list_C, return_type_C)
    main_str += generate_RTL_latency_model(top_name, port_list_RTL, port_list_C, return_type_C, RTL_branch_list)
    
    # RTL execution
    main_str += generate_loop_body(top_name, port_list_RTL, port_list_C, return_type_C, RTL_branch_list)
    
    # assertion
    main_str += generate_C_verilog_result_assertion(port_list_C, return_type_C)
    main_str += "}\n"
    return main_str


####

def generate_verification_backbone(top_name, port_list_RTL, port_list_C, return_type_C):
    program_string = ""
    program_string += generate_header_string(top_name)
    program_string += generate_main_body(top_name, port_list_RTL, port_list_C, return_type_C)
    return program_string


import re
import sys
import os

import port_def
import code_gen
 


def parser_HLS():
    args = sys.argv
    design_path = ""
    project_name = "dut_HLS_project"
    top_name = "top"
    bound = 100
    if len(args) == 1:
        args.append("-h")
        
    for i in range(len(args)):
        argument = args[i]
        if argument == "-h" or argument == "--help":
            print("HLS checker: version 1.0")
            print("--design: \t\t\t\t folder for design")
            print("--name:   \t\t\t\t project name")
            print("--top:    \t\t\t\t top function name")
            print("--bound:  \t\t\t\t bound of BMC")
            print("--help:   \t\t\t\t help information")
            exit(0)
        if argument == "-d" or argument == "--design":
            design_path = args[i+1]
        if argument == "-n" or argument == "--name":
            project_name = args[i+1]
        if argument == "-t" or argument == "--top":
            top_name = args[i+1]
        if argument == "-b" or argument == "--bound":
            bound = int(args[i+1])

    return design_path, project_name, top_name, bound


def create_project():
    print("create project")
    if (os.path.exists("dut")):
        os.system("rm -r dut")
    os.system("mkdir dut")
    os.system("mkdir dut/design")
    os.system("mkdir dut/verification")
    

def fetch_design_file (design_path):
    design_files = os.listdir(design_path)
    for filename in design_files:
        if filename.find(".h") != -1 or filename.find(".c") != -1:
            os.system("cp {} ./dut/design/".format(os.path.join(design_path, filename)))


def script_generator_HLS(project_name, top_name):
    script_file = open("./dut/design/script.tcl", mode="w+")

    script_file.write("open_project -reset {}\n".format(project_name))
    script_file.write("set_top {}\n".format(top_name))

    design_files_test = os.listdir("./dut/design")

    for filename in design_files_test:
        if filename.find(".c") != -1 or filename.find(".h") != -1:
            script_file.write("add_files {}\n".format(filename))
    
    script_file.write("open_solution \"solution1\" -flow_target vivado\n")
    script_file.write("set_part {xcu50-fsvh2104-2-e}\n")
    script_file.write("create_clock -period 3.33 -name default\n")
    script_file.write("csynth_design\n")
    script_file.write("exit\n")
    script_file.close()


def launch_script():
    os.system("cd ./dut/design  ;vitis_hls -f script.tcl")

def extract_HLS_output(project_name, top_name):
    os.system("cp ./dut/design/{}/solution1/syn/verilog/{}.v ./dut/verification".format(project_name, top_name))

def generate_verification_interface(top_name):
    os.system("../hw-cbmc {} --module {} --gen-interface > ./dut/verification/verilog_interface.h".format(
        os.path.join("./dut/verification", "{}.v".format(top_name)), top_name))
    file_interface = open("./dut/verification/verilog_interface.h")
    line_list = []
    line = file_interface.readline()
    line_list.append(line)
    while line:
        line_list.append(line)
        line = file_interface.readline()
    file_interface.close()
    file_interface = open("./dut/verification/verilog_interface.h", "w")
    
    start_write = 0
    for line in line_list:
        line:str
        if line.find("/*") != -1:
            start_write = 1
        if start_write == 1:
            file_interface.write(line)

    file_interface.close()


def get_RTL_port_list(project_name, top_name):
    port_list = []
    

    os.system("cp ./dut/design/{}/solution1/syn/report/{}_csynth.xml ./dut/verification".format(project_name, top_name))
    file_report_xml = open("./dut/verification/{}_csynth.xml".format(top_name))

    line = file_report_xml.readline()
    while line:


        if line.find("<InterfaceSummary>") != -1:
            while line:
                if line.find("</InterfaceSummary>") != -1:
                    break
                if line.find("<RtlPorts>") != -1:
                    # read each RTL ports
                    while line:
                        if line.find("<\RtlPorts>") != -1:
                            break
                        if line.find("<name>") != -1:
                            line_name = line
                            line_object = file_report_xml.readline()
                            line_type = file_report_xml.readline()
                            line_scope = file_report_xml.readline()
                            line_ioprotocol = file_report_xml.readline()
                            line_ioconfig = file_report_xml.readline()
                            line_direction = file_report_xml.readline()
                            line_bitwidth = file_report_xml.readline()
                            line_attribution = file_report_xml.readline()
                            
                            name_tmp = line_name[line_name.find('>')+1:line_name.find("</")]
                            object_tmp = line_object[line_object.find('>')+1:line_object.find("</")]
                            type_tmp = line_type[line_type.find('>')+1:line_type.find("</")]
                            scope_tmp = line_scope[line_scope.find('>')+1:line_scope.find("</")]
                            ioprotocol_tmp = line_ioprotocol[line_ioprotocol.find('>')+1:line_ioprotocol.find("</")]
                            ioconfig_tmp = line_ioconfig[line_ioconfig.find('>')+1:line_ioconfig.find("</")]
                            direction_tmp = line_direction[line_direction.find('>')+1:line_direction.find("</")]
                            bitwidth_tmp = line_bitwidth[line_bitwidth.find('>')+1:line_bitwidth.find("</")]
                            attribution_tmp = line_attribution[line_attribution.find('>')+1:line_attribution.find("</")]
                            
                            port_tmp = port_def.PortRTL(name_tmp, object_tmp, type_tmp, ioprotocol_tmp, direction_tmp, int(bitwidth_tmp), attribution_tmp)
                            port_list.append(port_tmp)
                            
                        line = file_report_xml.readline()
                line = file_report_xml.readline()
        

        line = file_report_xml.readline()

    file_report_xml.close()

    return port_list


def get_C_port_list (top_name):
    port_list = []
    return_type = ""
    SRC_FILE = "./dut/design/{}.c".format(top_name)
    TOP_FILE = "./dut/design/{}_format.c".format(top_name)
    CLANG_FORMAT_SRC = 'clang-format %s -style="{ BreakBeforeBraces: Attach, BinPackParameters: false, IndentWidth: 4, TabWidth: 4, ColumnLimit: 10000, AllowShortBlocksOnASingleLine: false, AllowShortFunctionsOnASingleLine: false, AllowShortIfStatementsOnASingleLine: false, AllowShortLoopsOnASingleLine: false, AlwaysBreakTemplateDeclarations: Yes }" > %s' % (SRC_FILE, TOP_FILE)
    os.system(CLANG_FORMAT_SRC)
    with open(TOP_FILE, "r") as file_c_design:
        lines = file_c_design.readlines()
        for i in range(len(lines)):
            #if re.match(r'([void|int|float|double|long|bool|char][ ])([a-zA-Z_0-9]+)(\()(.*)(\))\{', lines[i]):
            #    print(lines[i])

            if re.match(r'([a-zA-Z_0-9]+[ ]+)([a-zA-Z_0-9]+).*\{', lines[i]):
                declare_line = lines[i]
                declare_line_group = re.search(r'([a-zA-Z_0-9]+[ ]+)([a-zA-Z_0-9]+)\((.*)\)[ ]+\{', declare_line).groups()
                declare_line_arg_list = declare_line_group[2].split(',')
                return_type = declare_line_group[0]
                
                #print(declare_line_group)
                
                for argument in declare_line_arg_list:
                    argument = argument.strip(' ')
                    argument_part = argument.split(' ')
                    type_tmp = argument_part[0]
                    is_array_tmp = 0
                    name_tmp = argument_part[1]
                    array_position_index = argument_part[1].find('[')
                    array_length_tmp = 0
                    if array_position_index != -1:
                        is_array_tmp = 1
                        array_position_index_2 = argument_part[1].find(']')
                        array_length_tmp = int(argument_part[1][array_position_index+1:array_position_index_2])
                        name_tmp = argument_part[1][0:array_position_index]
                    port_c_tmp = port_def.PortC(name_tmp, type_tmp, is_array_tmp, array_length_tmp)
                    port_list.append(port_c_tmp)
    return port_list, return_type

def refine_C_code (top_name):
    TOP_FILE = "./dut/design/{}_format.c".format(top_name)
    REFINE_FILE = "./dut/verification/{}_refine.c".format(top_name)
    REFINE_HEADER_FILE = "./dut/verification/{}_refine.h".format(top_name)
    file_c_refine = open(REFINE_FILE, "w+")
    file_c_refine_header = open(REFINE_HEADER_FILE, "w+")
    with open(TOP_FILE, "r") as file_c_design:
        lines = file_c_design.readlines()
        for i in range(len(lines)):

            if re.match(r'([a-zA-Z_0-9]+[ ]+)([a-zA-Z_0-9]+).*\{', lines[i]):
                declare_line = lines[i]
                declare_line_group = re.search(r'([a-zA-Z_0-9]+[ ]+)([a-zA-Z_0-9]+)\((.*)\)[ ]+\{', declare_line).groups()
                #declare_line_arg_list = declare_line_group[2].split(',')
                #return_type = declare_line_group[0]
                function_name = declare_line_group[1]
                function_name = function_name + "_c"
                file_c_refine.write(declare_line_group[0] + function_name + "({}){{\n".format(declare_line_group[2]))
                file_c_refine_header.write(declare_line_group[0] + function_name + "({});\n".format(declare_line_group[2]))
            else:
                file_c_refine.write(lines[i])
    file_c_refine.close()
    file_c_refine_header.close()
                
                



#def generate_verification_backbone(top_name, port_list_RTL, port_list_C, return_type_C):
#    
#    
#    file_link_c_vlg = open("./dut/verification/link_c_vlg_{}.c".format(top_name), mode="w+")
#    
#    file_link_c_vlg.write("#include<assert.h>\n")
#    file_link_c_vlg.write("#include<stdbool.h>\n")
#    file_link_c_vlg.write("#include\"verilog_interface.h\"\n")
#    file_link_c_vlg.write("#include\"../design/{}.c\"\n".format(top_name))
#    file_link_c_vlg.write("int main() {\n")
#    
#    for port_c in port_list_C:
#        # declare ports
#        port_c:PortC
#        str_port_part = "{} {}".format(port_c.type, port_c.name)
#        if port_c.is_array == 1:
#            str_port = "{}[{}];".format(str_port_part, port_c.array_length)
#        else:
#            str_port = "{};".format(str_port_part)
#        file_link_c_vlg.write(str_port + "\n")
#    print(return_type_C)
#    if return_type_C.find("void") == -1:
#        file_link_c_vlg.write("{} ret_c;\n".format(return_type_C))
#    
#    # exection c
#    parameter_str = ""
#    for i in range(len(port_list_C)):
#        port_c = port_list_C[i]
#        parameter_str += port_c.name 
#        if i != len(port_list_C) - 1:
#            parameter_str += ", "
#    if return_type_C.find("void") == -1:
#        file_link_c_vlg.write("ret_c = {}({});\n".format(top_name, parameter_str))
#    else:
#        file_link_c_vlg.write("{}({});\n".format(top_name, parameter_str))
#    
#    # execution verilog
#    
#    for port_rtl in port_list_RTL:
#        port_rtl:PortRTL
#        if port_rtl.iop == "ap_none" and port_rtl.direction == "in":
#            file_link_c_vlg.write("{}.{} = {}".format(top_name, port_rtl.name, port_rtl.name))
#    file_link_c_vlg.write("{}.ap_start = 1;\n".format(top_name))
#    
#    file_link_c_vlg.write("for (int i = 0; i < bound; i++) {\n")
#    
#    file_link_c_vlg.write("set_inputs();\n")
#    file_link_c_vlg.write("if ({}.ap_done == 1) {{\n".format(top_name))
#    file_link_c_vlg.write("break;\n")
#    file_link_c_vlg.write("}\n") # end of if ... ap_done
#    
#    for port_rtl in port_list_RTL:
#        port_rtl:PortRTL
#        if port_rtl.iop == "ap_memory":
#            print("a")
#    
#    file_link_c_vlg.write("next_timeframe();\n")
#    file_link_c_vlg.write("}\n") # end of for ... bound
#    file_link_c_vlg.write("}\n") # end of main
#    file_link_c_vlg.close()
#    return


def main():
    print("HLS checker version 1.0")
    design_path, project_name, top_name, bound = parser_HLS()
    create_project()
    print("design path  = {}".format(design_path))
    print("project name = {}".format(project_name))
    print("top name     = {}".format(top_name))
    
    file_link = open("./dut/verification/c_vlg_link.c","w+")
    
    fetch_design_file(design_path)
    script_generator_HLS(project_name, top_name)
    launch_script()
    extract_HLS_output(project_name, top_name)
    generate_verification_interface(top_name)
    port_list_RTL = get_RTL_port_list(project_name, top_name)
    port_list_C, return_type_C   = get_C_port_list(top_name)
    refine_C_code(top_name)
    link_prog = code_gen.generate_verification_backbone(top_name, port_list_RTL, port_list_C, return_type_C)
    file_link.write(link_prog)
    file_link.close()
    
    
    os.system("../hw-cbmc ./dut/verification/c_vlg_link.c ./dut/verification/{}.v --module {} --bound {}".format(top_name, top_name, bound))
    
if __name__ == "__main__":
    main()
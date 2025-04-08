from bazmek import sandbox, utils
from pathlib import Path


dockerfile = sandbox.Dockerfile(image='python:3.12.9-bookworm',
                                user='sim',
                                run=('apt update',
                                     'apt install -y iverilog',
                                     'pip install cocotb'),
                                exec=('make',))

sim_files = (sandbox.File(path=Path('adder.sv'),
                          data="""module adder (
    input  logic [7:0] a,
    input  logic [7:0] b,
    output logic [7:0] sum
);
    assign sum = a + b;
endmodule"""),
             sandbox.File(path=Path('makefile'),
                          data="""SIM = icarus
TOPLEVEL_LANG = verilog
VERILOG_SOURCES = $(shell pwd)/adder.sv
TOPLEVEL = adder
MODULE = testbench

include $(shell cocotb-config --makefiles)/Makefile.sim"""),
             sandbox.File(path=Path('testbench.py'),
                          data="""import cocotb
from cocotb import test
from cocotb.triggers import RisingEdge, Timer


@test
async def basic_assertion(dut):
    dut.a = 3
    dut.b = 4
    await Timer(1, units='ns')
    assert dut.sum.value == 7"""))

print(f'Dockerfile:\n{dockerfile.stringify(sim_files)}\n' + '=' * 79)

record = utils.sync(sandbox.run(sandbox.namefy('cocotb'),
                                Path(__file__).parent / 'ignore',
                                dockerfile,
                                add_files=sim_files,
                                get_files=(Path('/home/sim/results.xml'),)))

print(f'Status Code:\n{record.status_code}\n' + '=' * 79)
print(f'Build logs:\n{"\n".join(record.build_logs)}\n' + '=' * 79)
print(f'Run logs:\n{record.run_logs}\n' + '=' * 79)
print(f'Workspace:\n{record.workspace}\n' + '=' * 79)

file_contents = ('-' * 79).join(f'{path.absolute()}:\n{content.decode()}\n'
                                for path, content in record.files.items())
print(f'files:\n{file_contents}\n' + '=' * 79)

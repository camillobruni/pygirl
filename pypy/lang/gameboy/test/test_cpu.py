import py
from pypy.lang.gameboy.cpu import CPU, Register, DoubleRegister
from pypy.lang.gameboy.ram import RAM
from pypy.lang.gameboy import constants

def get_cpu():
    cpu =  CPU(None, RAM())
    cpu.setROM([0]*0xFFFF);
    return cpu

# ------------------------------------------------------------
# TEST REGISTER
def test_register_constructor():
    register = Register(get_cpu())
    assert register.get() == 0
    value = 10
    register = Register(get_cpu(), value)
    assert register.get() == value
    
def test_register():
    register = Register(get_cpu())
    value = 2
    oldCycles = register.cpu.cycles
    register.set(value)
    assert register.get() == value
    assert oldCycles-register.cpu.cycles == 1
    
def test_register_bounds():
    register = Register(get_cpu())
    value = 0x1234FF
    register.set(value)
    assert register.get() == 0xFF
    
# ------------------------------------------------------------
# TEST DOUBLE REGISTER

def test_double_register_constructor():
    cpu = get_cpu()
    register = DoubleRegister(cpu)
    assert register.get() == 0
    assert register.getHi() == 0
    assert register.getLo() == 0
    value = 0x1234
    reg1 = Register(cpu)
    reg1.set(0x12)
    reg2 = Register(cpu)
    reg2.set(0x34)
    register = DoubleRegister(cpu, reg1, reg2)
    assert register.hi == reg1
    assert register.lo == reg2
    assert register.getHi() == reg1.get()
    assert register.getLo() == reg2.get()
    
def test_double_register():
    register = DoubleRegister(get_cpu())
    value = 0x1234
    oldCycles = register.cpu.cycles
    register.set(value)
    assert oldCycles-register.cpu.cycles == 1
    assert register.get() == value
    
def test_double_register_bounds():
    register = DoubleRegister(get_cpu())
    value = 0xFFFF1234
    register.set(value)
    assert register.get() == 0x1234
    
def test_double_register_hilo():
    register = DoubleRegister(get_cpu())
    value = 0x1234
    valueHi = 0x12
    valueLo = 0x34
    oldCycles = register.cpu.cycles
    register.set(valueHi, valueLo)
    assert oldCycles-register.cpu.cycles == 2
    assert register.getHi() == valueHi
    assert register.getLo() == valueLo
    assert register.get() == value
    
    valueHi = 0x56
    oldCycles = register.cpu.cycles
    register.setHi(valueHi)
    assert oldCycles-register.cpu.cycles == 1
    assert register.getHi() == valueHi
    assert register.getLo() == valueLo
    
    valueLo = 0x78
    oldCycles = register.cpu.cycles
    register.setLo(valueLo)
    assert oldCycles-register.cpu.cycles == 1
    assert register.getHi() == valueHi
    assert register.getLo() == valueLo
    
    
def test_double_register_methods():
    value = 0x1234
    register = DoubleRegister(get_cpu())
    register.set(value)
    
    oldCycles = register.cpu.cycles
    register.inc()
    assert oldCycles-register.cpu.cycles == 2
    assert register.get() == value+1
    
    oldCycles = register.cpu.cycles
    register.dec()
    assert oldCycles-register.cpu.cycles == 2
    assert register.get() == value
    
    addValue = 0x1001
    oldCycles = register.cpu.cycles
    register.add(addValue)
    assert oldCycles-register.cpu.cycles == 3
    assert register.get() == value+addValue
    
    
# ------------------------------------------------------------
# TEST CPU

def test_getters():
    cpu = get_cpu()
    assert cpu.getA() == constants.RESET_A
    assert cpu.getF() == constants.RESET_F
    assert cpu.bc.get() == constants.RESET_BC
    assert cpu.de.get() == constants.RESET_DE
    assert cpu.pc.get() == constants.RESET_PC
    assert cpu.sp.get() == constants.RESET_SP
    
    
OPCODE_CYCLES = [
    (0x00, 1),
    (0x08, 5),
    (0x10, 0),
    (0x18, 3),
    (0x20, 0x38, 0x08, [2,3]),
    (0x01, 0x31, 0x10, 3),
    (0x09, 0x39, 0x10, 2),
    (0x02, 0x3A, 0x08, 2),
    (0x03, 0x33, 0x10, 2),
    (0x0B, 0x3B, 0x10, 2),
    (0x04, 0x2C, 0x01, 1), (0x34, 3), (0x3C, 1) #CPU.java line 331
]

def test_cycles():
    py.test.skip("opCode mapping in CPU is still missing.")
    cpu = get_cpu()
    for entry in OPCODE_CYCLES:
        if len(entry) == 2:
            cycle_test(cpu, entry[0], entry[1])
        elif len(entry) == 4:
            for opCode in range(entry[0], entry[1], entry[2]):
                cycle_test(cpu, opCode, entry[3])
                
        
        
def cycle_test(cpu, opCode, cycles):
    oldCycles = cpu.cycles
    cpu.execute(opCode)
    assert oldCycles - cpu.cycles == cycles
            


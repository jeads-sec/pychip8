import logging
import struct
from time import sleep
from pychip8 import *

class Chip8CPU:
    def __init__(self, rom_name, log_level='warning'):
        f = open(rom_name, 'rb')
        self.mem = bytearray(0x1000)
        with open(rom_name, 'rb') as f:
            i = 0
            b = f.read(1)
            while b != '':
                self.mem[i+0x200] = ord(b)
                b = f.read(1)
                i += 1
        
        self.v = [0]*16
        self.i = 0
        self.pc = 0x200
        self.sp = 0
        self.stack = []
        
        self.log = logging.getLogger("chip8-core")
        self.ch = logging.StreamHandler()
        self.ch.setLevel(logging.DEBUG)
        self.log.addHandler(self.ch)
        self.log.setLevel(LEVELS[log_level])
        self.loglevel = LEVELS[log_level]
        self.logEnabled = True
    
    def write_mem(self, addr, data):
        packed = struct.pack('>H', data)
        for i,byte in enumerate(packed):
            self.mem[addr+i] = byte
            
    def read_mem(self, addr):
        unpacked = struct.unpack('>H', str(self.mem[addr:addr+2]))[0]
        return unpacked
            
    def push_val(self, value):
        if len(self.stack) == 15:
            raise Exception('Stack Overflow!')
        self.stack.append(value)
    
    def parse_instruction(self, opcode):
        self.log.debug('[0x%04X]: 0x%04X' % (self.pc, opcode))
        x = opcode & 0x0F00 >> 8
        y = (opcode & 0x00F0) >> 4
        addr = opcode & 0xFFF
        byte = opcode & 0xFF
        
        if opcode == 0x00e0:
            pass
        elif opcode == 0x00ee:
            pass
        elif opcode >= 0x1000 and opcode < 0x2000:
            # JP addr
            self.pc = addr
            self.log.debug('JP 0x%04X' % addr)
        elif opcode >= 0x2000 and opcode < 0x3000:
            # CALL addr
            self.push_val(self.pc+2)
            self.pc = addr
            self.log.debug('CALL 0x%04X' % addr)
        elif opcode >= 0x3000 and opcode < 0x4000:
            # SE Vx, byte
            if self.v[x] == byte:
                self.pc += 2
                self.log.debug('SE V%x, 0x%02X [TRUE]' % (x, byte))
            else:
                self.log.debug('SE V%x, 0x%02X [FALSE]' % (x, byte))
        elif opcode >= 0x6000 and opcode < 0x7000:
            # LD Vx, byte            
            self.v[x] = byte
            self.log.debug('LD V%x, 0x%02X' % (x, byte))
        elif opcode >= 0x7000 and opcode < 0x8000:
            # ADD Vx, byte
            self.v[x] += byte
            self.log.debug('ADD V%x, 0x%02X' % (x, byte))
        elif (opcode & 0xF000) == 0x8000:
            switch = opcode & 0xF
            if switch == 0x3:
                # XOR Vx, Vy
                self.v[x] ^= self.v[y]
                self.log.debug('XOR V%x, V%x' % (x,y))
        elif opcode >= 0xA000 and opcode < 0xB000:
            # LD I, addr
            self.i = opcode & 0xFFF
            self.log.debug('LD I, 0x%X' % (opcode & 0xFFF))
        elif (opcode & 0xF055) == 0xF055:
            self.write_mem(self.i, self.v[x])
            self.log.debug('LD [I], V%x' % x)
        elif (opcode & 0xF01E) == 0xF01E:
            # ADD I, Vx
            self.i += x
            self.log.debug('ADD I, V%x' % x)
        elif (opcode & 0xF065) == 0xF065:
            # LD Vx, [I]
            self.v[x] = self.read_mem(self.i)
            self.log.debug('LD V%x, [0x%04X]' % (x, self.i))
        else:
            raise Exception('OH NOZ!')
        
        self.pc += 2
    
    def run(self):
        while True:
            opcode = struct.unpack('>H', str(self.mem[self.pc:self.pc+2]))[0]
            try:
                self.parse_instruction(opcode)
            except Exception as e:
                print e
                return False
            
            sleep(1.0/60)
import logging
import struct
import pygame
from random import randint
from time import sleep, time
from pychip8 import *

class Chip8CPU:
    def __init__(self, rom_name, log_level='warning'):
        f = open(rom_name, 'rb')
        self.mem = bytearray(0x1000)
        self.mem[0:5] =   '\xf0\x90\x90\x90\xf0'    # 0
        self.mem[6:11] =  '\x20\x60\x20\x20\x70'    # 1
        self.mem[12:17] = '\xf0\x10\xf0\x80\xf0'    # 2
        self.mem[18:23] = '\xf0\x10\xf0\x10\xf0'    # 3
        self.mem[24:29] = '\x90\x90\xf0\x10\x10'    # 4
        self.mem[30:35] = '\xf0\x80\xf0\x10\xf0'    # 5
        self.mem[36:41] = '\xf0\x80\xf0\x90\xf0'    # 6
        self.mem[42:47] = '\xf0\x10\x20\x40\x40'    # 7
        
        with open(rom_name, 'rb') as f:
            i = 0
            b = f.read(1)
            while b != '':
                self.mem[i+0x200] = ord(b)
                b = f.read(1)
                i += 1
        
        self.v = [0]*16
        self.i = 0
        self.dt = 0
        self.st = 0
        self.pc = 0x200
        self.sp = 0
        self.stack = []
        
        self.screen = bytearray(64*32)
        
        self.log = logging.getLogger("chip8-core")
        self.ch = logging.StreamHandler()
        self.ch.setLevel(logging.DEBUG)
        self.log.addHandler(self.ch)
        self.log.setLevel(LEVELS[log_level])
        self.loglevel = LEVELS[log_level]
        self.logEnabled = True
        
        pygame.init()
        self.window = pygame.display.set_mode((640,320))
    
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
    
    def pop_val(self):
        if len(self.stack) == 0:
            raise Exception('Stack Underflow!')
        return self.stack.pop()
    
    def update_screen(self):
        for i,byte in enumerate(self.screen):
            #if (i%8) == 0:
            #    print ''
            tmp = byte
            for j in range(8):
                bit = (tmp & 0x80) >> 7
                tmp <<= 1
                if bit == 1:
                    pygame.draw.rect(self.window, (255,255,255,255), (((i*8+j)%64)*10,((i*8+j)/64)*10,10,10))
                    #print '1',
                else:
                    #print '0',
                    pass
        '''for i,byte in enumerate(self.screen):
            tmp = byte
            j = 0
            while tmp != 0:
                j += 1
                bit = tmp & 1
                if bit:
                    print '(%d,%d)' % (8-j, i)
                    pygame.draw.rect(self.window, (255,255,255,255), ((8-j)*10,i*10,10,10))
                else:
                    pass
                tmp >>= 1'''
    
    def parse_instruction(self, opcode):
        self.log.info('[0x%04X]: 0x%04X' % (self.pc, opcode))
        for i,val in enumerate(self.v):
            self.log.debug('V%x: 0x%02X' % (i, val))
        x = (opcode & 0x0F00) >> 8
        y = (opcode & 0x00F0) >> 4
        nibble = opcode & 0x000F
        addr = (opcode & 0xFFF) - 2
        byte = opcode & 0xFF
        
        if opcode == 0x00e0:
            # CLS
            self.log.warning('TODO CLS')
        elif opcode == 0x00ee:
            # RET
            self.pc = self.pop_val()
            self.log.info('RET')
        elif opcode == 0x00ff:
            # HIGH
            self.log.warning('TODO HIGH')
        elif opcode >= 0x1000 and opcode < 0x2000:
            # JP addr
            self.pc = addr
            self.log.info('JP 0x%04X' % addr)
        elif opcode >= 0x2000 and opcode < 0x3000:
            # CALL addr
            self.push_val(self.pc) # +2 at end of loop will fix
            self.pc = addr
            self.log.info('CALL 0x%04X' % addr)
        elif opcode >= 0x3000 and opcode < 0x4000:
            # SE Vx, byte
            if self.v[x] == byte:
                self.pc += 2
                self.log.info('SE V%x, 0x%02X [TRUE]' % (x, byte))
            else:
                self.log.info('SE V%x, 0x%02X [FALSE]' % (x, byte))
        elif opcode >= 0x4000 and opcode < 0x5000:
            # SNE Vx, byte
            if self.v[x] != byte:
                self.pc += 2
                self.log.info('SNE V%x, 0x%02X [TRUE]' % (x, byte))
            else:
                self.log.info('SNE V%x, 0x%02X [FALSE]' % (x, byte))
        elif opcode >= 0x6000 and opcode < 0x7000:
            # LD Vx, byte            
            self.v[x] = byte
            self.log.info('LD V%x, 0x%02X' % (x, byte))
        elif opcode >= 0x7000 and opcode < 0x8000:
            # ADD Vx, byte
            self.v[x] += byte
            self.log.info('ADD V%x, 0x%02X' % (x, byte))
        elif (opcode & 0xF000) == 0x8000:
            if nibble == 0x0:
                # LD Vx, Vy
                self.v[x] = self.v[y]
                self.log.info('LD V%x, V%x' % (x,y))
            elif nibble == 0x2:
                # AND Vx, Vy
                self.v[x] &= self.v[y]
                self.log.info('AND V%x, V%x' % (x,y))
            elif nibble == 0x3:
                # XOR Vx, Vy
                self.v[x] ^= self.v[y]
                self.log.info('XOR V%x, V%x' % (x,y))
            elif nibble == 0x4:
                # ADD Vx, Vy
                self.v[x] += self.v[y]
                self.log.info('ADD V%x, V%x' % (x,y))
            else:
                raise Exception()
        elif opcode >= 0xA000 and opcode < 0xB000:
            # LD I, addr
            self.i = opcode & 0xFFF
            self.log.info('LD I, 0x%X' % (opcode & 0xFFF))
        elif opcode >= 0xC000 and opcode < 0xD000:
            # RND Vx, byte
            self.v[x] = randint(0,255) & byte
            self.log.info('RND V%x, 0x%02X' % (x,byte))
        elif opcode >= 0xD000 and opcode < 0xF000:
            # DRW Vx, Vy, nibble
            self.v[0xf] = 0
            dx = self.v[x]/8
            dy = self.v[y]
            shift = self.v[x]%8
            #self.log.info('DRW -- I: 0x%04X, (0x%04X, 0x%04X), n: %d' % (self.i, dx, dy, nibble))
            for i in range(nibble):
                byte = self.mem[self.i+i]
                #print '0x%02X 0x%02X' % (byte>>shift, (byte<<(8-shift)) & 0xFF)
                if self.screen[dx + dy*8] & (byte>>shift) or self.screen[dx + dy*8 + 1] & (byte<<(8-shift)) & 0xFF:
                    self.v[0xf] = 1
                self.screen[dx + dy*8] ^= (byte>>shift)
                if shift != 0:
                    self.screen[dx + dy*8 + 1] ^= (byte<<(8-shift)) & 0xFF
                dy += 1
                
            self.log.info('DRW V%x, V%x, %d' % (x,y,nibble))
        elif (opcode & 0xF007) == 0xF007:
            # LD Vx, DT
            self.v[x] = self.dt
            self.log.info('LD V%x, DT' % x)
        elif (opcode & 0xF015) == 0xF015:
            # LD DT, Vx
            self.dt = self.v[x]
            self.log.info('LD DT, V%x' % x)
        elif (opcode & 0xF018) == 0xF018:
            # LD ST, Vx
            self.st = self.v[x]
            self.log.info('LD ST, V%x' % x)
        elif (opcode & 0xF01E) == 0xF01E:
            # ADD I, Vx
            self.i += x
            self.log.info('ADD I, V%x' % x)
        elif (opcode & 0xF029) == 0xF029:
            # LD F, Vx
            self.i = self.v[x] * 5
            self.log.warning('LD F, V%x' % x)
        elif (opcode & 0xF033) == 0xF033:
            # LD B, Vx
            val = self.v[x]
            self.write_mem(self.i, val / 100)
            self.write_mem(self.i+1, (val / 100) % 10)
            self.write_mem(self.i+2, val % 10)
            self.log.info('LD B, V%x' % x)
        elif (opcode & 0xF055) == 0xF055:
            self.write_mem(self.i, self.v[x])
            self.log.info('LD [I], V%x' % x)
        elif (opcode & 0xF065) == 0xF065:
            # LD Vx, [I]
            self.v[x] = self.read_mem(self.i)
            self.log.info('LD V%x, [0x%04X]' % (x, self.i))
        else:
            raise Exception('OH NOZ!')
        
        self.pc += 2
    
    def run(self):
        while True:
            self.update_screen()
            pygame.display.update()
            ftime = time()
            if self.dt > 0:
                self.dt -= 1
                
            opcode = struct.unpack('>H', str(self.mem[self.pc:self.pc+2]))[0]
            try:
                self.parse_instruction(opcode)
            except Exception as e:
                print e
                return False
            
            if (time()-ftime) > 1.0/60:
                self.log.warning('Over time!')
            while (time()-ftime) < 1.0/60:
                pass
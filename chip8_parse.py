#!/usr/bin/python
from argparse import ArgumentParser

from pychip8.chip8cpu import Chip8CPU

if __name__=='__main__':
    parser = ArgumentParser(description="A Chip-8 emulator implemented in Python")
    parser.add_argument("rom_file", help="Input Chip-8 ROM file")
    parser.add_argument("-l", dest="log_level", default='warning',
            help="The logging level [debug, info, warning, error, critical]")
    
    args = parser.parse_args()
    
    cpu = Chip8CPU(args.rom_file, args.log_level)
    
    cpu.run()
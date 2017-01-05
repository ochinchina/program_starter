#!/usr/bin/python

import os
import sys
import json

def get_program_without_depends( config ):
        programs_without_depends = set()
        for program in config["programs"]:
                if not "depends" in config["programs"][program]:
                        programs_without_depends.add( program )
        return programs_without_depends
def get_program_with_depends( config, ready_programs ):
        for program in config["programs"]:
                if not program in ready_programs:
                        if "depends" in config["programs"][program]:
                                if isinstance( config["programs"][program]["depends"], list ):
                                        if set(config["programs"][program]["depends"]).issubset(ready_programs):
                                                return program
                                elif config["programs"][program]["depends"] in ready_programs:
                                        return program
        return None

def pre_start_program( config, program ):
        if "pre_start" in config["programs"][program]:
                execute_script( config["programs"][program]["pre_start"] )
def post_start_program( config, program):
        if "post_start" in config["programs"][program]:
                execute_script( config["programs"][program]["post_start"] )
def start_program( config, program):
        if "start" in config["programs"][program]:
                execute_script( config["programs"][program]["start"] )

def stop_program( config,program):
        if "stop" in config["programs"][program]:
                 execute_script( config["programs"][program]["stop"] )

def pre_stop_program( config, program ):
        if "pre_stop" in config["programs"][program]:
                 execute_script( config["programs"][program]["pre_stop"] )

def post_stop_program( config, program ):
        if "post_stop" in config["programs"][program]:
                 execute_script( config["programs"][program]["post_stop"] )

def execute_script( script ):
        print( "execute script: %s" % script )
        os.system( script )

def load_config( config_file ):
        with open( config_file ) as fp:
                return json.load( fp )
        return None

config = load_config( sys.argv[1] )
programs_in_schedule = get_program_without_depends( config )
ready_programs=set()

while len( programs_in_schedule ) > 0:
        program = programs_in_schedule.pop()
        pre_start_program( config, program )
        start_program( config, program)
        post_start_program( config, program )

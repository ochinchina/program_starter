#!/usr/bin/python

import os
import sys
import json
import yaml
import argparse

class ProgramStarter:
    def __init__( self, config ):
        self.config = config
    def start_all( self ):
        pending_programs = self._get_program_without_depends()
        started_programs = set()
        while len( pending_programs ) > 0:
            program = pending_programs.pop()
            self.start_program( program )
            started_programs.add( program )
            program = self._get_program_with_depends( started_programs )
            if program:
                pending_programs.add( program )

    def stop_all( self ):
        pending_programs = self._get_program_without_depends()
        started_programs = []
        while len( pending_programs ) > 0:
            program = pending_programs.pop()
            started_programs.append( program )
            pending_programs.add( self._get_program_with_depends( started_programs ) )
        for program in started_programs.reverse():
            self.stop_program( program )

    def start_program( self, program ):
        self._pre_start_program( program )
        self._start_program( program )
        self._post_start_program( program )

    def stop_program( self, program ):
        self._pre_stop_program( program )
        self._stop_program( program )
        self._post_stop_program( program )

    def _get_program_without_depends( self ):
        programs_without_depends = set()
        for program in self.config["programs"]:
            if not "depends" in self.config["programs"][program]:
                programs_without_depends.add( program )
        return programs_without_depends

    def _get_program_with_depends( self, started_programs ):
        for program in self.config["programs"]:
            if not program in started_programs:
                if "depends" in self.config["programs"][program]:
                    if isinstance( self.config["programs"][program]["depends"], list ):
                         if set(self.config["programs"][program]["depends"]).issubset(started_programs):
                             return program
                    elif self.config["programs"][program]["depends"] in started_programs:
                        return program
        return None
    def _execute_script( self, script ):
        print( "execute script:%s" % script )
        return os.system( script )
    def _execute_program_script( self, program, script_key ):
        print( "start to execute %s.%s" % (program,script_key) )
        if script_key in self.config["programs"][program]:
            return self._execute_script( self.config["programs"][program][script_key] )
        return 1
    def _pre_start_program( self, program ):
        return self._execute_program_script( program, "pre_start" )
    def _post_start_program( self, program ):
        return self._execute_program_script( program, "post_start" )
    def _start_program( self, program):
        return self._execute_program_script( program, "start" )
    def _pre_stop_program( self, program ):
        return self._execute_program_script( program, "pre_stop" )
    def _post_stop_program( self, program ):
        return self._execute_program_script( program, "post_stop" )
    def _stop_program( self, program ):
        return self._execute_program_script( program, "stop" )

def is_yaml_file( fileName ):
    return fileName.endswith( ".yml" ) or fileName.endswith( "yaml" )

def load_config( config_file ):
    with open( config_file ) as fp:
        if is_yaml_file( config_file ):
            return yaml.safe_load( fp )
        else:
            return json.load( fp )
    return None


def main( configFile, action="start"):
    config = load_config( configFile )
    if config:
        starter = ProgramStarter( config )
        if action == "start":
            starter.start_all()
        elif action == "stop":
            starter.stop_all()

parser = argparse.ArgumentParser(description='start/stop program from configuration file')
parser.add_argument( "--action", choices=['start','stop','start_program','stop_program'])
parser.add_argument( "--program", help="program name if action is start_program or stop_program" )
parser.add_argument( "config_file" )

result = parser.parse_args( sys.argv[1:] )
main( result.config_file, result.action )

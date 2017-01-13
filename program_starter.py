#!/usr/bin/python


import os
import sys
import json
import yaml
import argparse
import logging

class ProgramStarter:

    def __init__( self, config ):
        if isinstance( config, str ):
            self.config=self._load_config(config)
        else:
            self.config = config
        self._update_depends_info()

    def _update_depends_info( self ):
        """
        create depend_by fields for each program from the depends_on information
        """
        for program in self.config['programs']:
            self.config['programs'][program]['depend_by'] = []

        for program in self.config['programs']:
            if 'depends_on' in self.config['programs'][program]:
                for depend in self.config['programs'][program]['depends_on']:
                    self.config['programs'][depend]['depend_by'].append( program )

    def start( self, recursive, start_programs):
        """
        start program(s), if programs is empty, start all the program
        """
        programs = self._get_depend_programs( start_programs )
        pending_programs = self._get_no_depend_programs( programs )
        started_programs = []
        
        while pending_programs:
            program = pending_programs.pop()
            if recursive or program in start_programs:
                self._start_program( program )
            started_programs.append( program )
            program = self._get_next_start_program( programs, started_programs )
            if program:
                pending_programs.append( program )

    def stop( self, recursive, stop_programs ):
        """
        stop programs, if the programs is empty, stop all the programs
        """
        programs = self._get_programs_depend_on( stop_programs )
        programs.reverse()
        for program in programs:
            if recursive or program in stop_programs:
                self._stop_program(program)

    def _get_depend_programs(self, programs ):
        """
        get all the depend programs. These depend programs should be started before.
        """
        if not programs:
            pending_programs = self._get_all_programs()
        else:
            pending_programs = []
            pending_programs.extend( programs )
        depends = []
        depends.extend( pending_programs )
        while pending_programs:
            program = pending_programs.pop()
            if "depends_on" in self.config["programs"][program]:
                for dep in self.config["programs"][program]['depends_on']:
                    if not dep in depends:
                        depends.append( dep )
                        pending_programs.append( dep )
        return depends

    def _get_programs_depend_on( self, programs ):
        if not programs:
            pending_programs = self._get_all_programs()
        else:
            pending_programs = []
            pending_programs.extend( programs )

        depends=[]
        while pending_programs:
            program = pending_programs.pop()
            if program in depends:
                depends.remove( program )
            depends.append( program )
            depended = self.config['programs'][program]['depend_by']
            pending_programs.extend( depended )
        return depends
    
    def _get_all_programs(self):
        """get all the defined programs"""
        programs = []

        for program in self.config['programs']:
            programs.append( program )
        return programs

    def _get_no_depend_programs( self, programs ):
        programs_without_depends = []
        if not programs:
            programs = self.config["programs"]
        for program in programs:
            if not "depends_on" in self.config["programs"][program]:
                programs_without_depends.append( program )
        return programs_without_depends

    def _get_next_start_program( self, programs, started_programs ):
        for program in programs:
            if not program in started_programs:
                if "depends_on" in self.config["programs"][program]:
                    #check if all the depend program(s) are started or not
                    if isinstance( self.config["programs"][program]["depends_on"], list ):
                         if set(self.config["programs"][program]["depends_on"]).issubset(started_programs):
                             return program
                    elif self.config["programs"][program]["depends_on"] in started_programs:
                        return program
        return None

    def _execute_program_script( self, program, script_key ):
        if script_key in self.config["programs"][program]:
            script = self.config["programs"][program][script_key]
            logging.debug( "start to execute:%s" % script )
            return os.system( script ) == 0
        return True
    def _start_program( self, program):
        logging.debug( "start program:%s" % program )
        try:
            if self._execute_program_script( program, "pre_start" ):
                if self._execute_program_script( program, "start" ):
                    if self._execute_program_script( program, "post_start"):
                        return True
        except Exception as e:
            logging.error( sys.exc_info() )
        return False
    def _stop_program( self, program ):
        logging.debug( "stop program:%s" % program )
        try:
            if self._execute_program_script( program, "pre_stop" ):
                if self._execute_program_script( program, "stop" ):
                    if self._execute_program_script( program, "post_stop" ):
                        return True
        except Exception as e:
            logging.error( sys.exc_info() )
        return False

    def _is_yaml_file( self, fileName ):
        """
        check if it is a yaml file from the fileNamew
        """
        return fileName.endswith( ".yml" ) or fileName.endswith( ".yaml" )

    def _load_config( self, config_file ):
        """
        load the config from the configure file.
        The configure file can be in json or yaml file
        """
        with open( config_file ) as fp:
            if self._is_yaml_file( config_file ):
                return yaml.safe_load( fp )
            else:
                return json.load( fp )
        return None

if __name__ == "__main__":
    logging.basicConfig( filename="program_starter.log", level=logging.DEBUG )
    parser = argparse.ArgumentParser(description='start/stop a group of depend program from configuration file')
    parser.add_argument( "-f", "--config_file", help = "config file, default is program-starter.yml", default='program-starter.yml')
    parser.add_argument( "command", choices=["start","stop"], help="start/stop a group of programs" )
    parser.add_argument( "program", nargs='*', help="program to be started/stopped" )
    parser.add_argument( "-r", "--recursive", action='store_true', default=False, help = "recursively start/stop programs" )
    args = parser.parse_args()

    starter = ProgramStarter( args.config_file )
    if args.command == 'start':
        starter.start( args.recursive, args.program )
    else:
        starter.stop( args.recursive, args.program )


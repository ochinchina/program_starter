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
        self._update_env()

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
    def _update_env( self ):
        """
        update the environment variable setting in the configuration file
        """
        if "envs" in self.config:
            envs = self.config["envs"]
            if isinstance( envs, dict ):
                os.environ.update( envs )

    def start( self, recursive, start_programs):
        """
        start program(s), if programs is empty, start all the program
        """
        #get programs the start_programs depend on
        programs = self._get_depend_programs( start_programs )
        #if start all the programs
        if not start_programs:
            start_programs = programs

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

        if not stop_programs:
            stop_programs = programs
        programs.reverse()
        for program in programs:
            if recursive or program in stop_programs:
                self._stop_program(program)

    def _get_depend_programs(self, programs ):
        """
        get all the depend programs. These depend programs should be started before.
        """
        if not programs:
            return self._get_all_programs()
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
        program_info = self.config["programs"][program]
        if script_key in program_info:
            envs = os.environ.copy()
            envs['PROGRAM']=program
            if "envs" in program_info:
                envs.update( program_info["envs"] )
            script = program_info[script_key]
            script = eval_with_env( script, envs )
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
        logging.debug( "try to load configure file:%s" % config_file )
        with open( config_file ) as fp:
            if self._is_yaml_file( config_file ):
                return yaml.safe_load( fp )
            else:
                return json.load( fp )
        logging.error( "fail to load the configure file" )
        return None

def eval_with_env( s, envs ):
    n = len( s )
    i = 0
    r = ""
    while i < n:
        if s[i] == '\\': #escape char \
            i = i + 1
            if i < n:
                r = r + s[i]
                i = i + 1
        elif s[i] == '$' and i + 1 < n and s[i+1] == '{': #if find starter of env var
            j = s.find( '}', i + 1 )
            #if end of env is found
            if j == -1:
                r = r + s[i:]
                i = n
            else:
                #check if default value is provided
                env = s[i+2:j]
                pos = env.find( ":" )
                if pos != -1:
                    def_value = env[pos+1:].strip()
                    env = env[0:pos].strip()
                #if environment variable exists
                if env in envs:
                    r = r + eval_with_env( envs[env], envs ) #support embded environment variable
                elif def_value: # set to default value if environment variable does not exist
                    r = r + def_value
                    def_value = "" #reset tht def_value to empty
                i = j + 1
        else: # for other case
            r = r + s[i]
            i = i + 1
    return r

def load_env_file( fileName ):
    logging.info( "load environment variable file:%s" % fileName )
    try:
        with open( fileName ) as f:
            for line in f:
                line = line.strip()
                if len( line ) > 0:
                    if line[0] == '#':
                        continue
                    pos = line.find( '=')
                    if pos != -1:
                        name = line[0:pos].strip()
                        value = line[pos+1:].strip()
                        os.environ[name] = value
    except Exception as ex:
        logging.error( "get exception when loading environment file %s:%r" %( fileName, ex ) )
if __name__ == "__main__":
    logging.basicConfig( filename="program_starter.log", level=logging.DEBUG )
    parser = argparse.ArgumentParser(description='start/stop a group of depend program from configuration file')
    parser.add_argument( "-f", "--config_file", help = "config file, default is program-starter.yml", default='program-starter.yml')
    parser.add_argument( "command", choices=["start","stop"], help="start/stop a group of programs" )
    parser.add_argument( "program", nargs='*', help="program to be started/stopped" )
    parser.add_argument( "-r", "--recursive", action='store_true', default=False, help = "recursively start/stop programs" )
    parser.add_argument( "-e", "--env_file", help = "environment file" )
    args = parser.parse_args()
    if args.env_file:
        load_env_file( args.env_file )

    starter = ProgramStarter( args.config_file )
    if args.command == 'start':
        starter.start( args.recursive, args.program )
    else:
        starter.stop( args.recursive, args.program )


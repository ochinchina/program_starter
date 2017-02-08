### Description

In a typical project, there will be more than one programs and there are some dependencies amoung them. These programs needs to be started in a specific order. To manage the program start-up, the project team maybe:
- write a script to start there programs in order. Different projects use different script to start the program
- use some tools, such as supervisor, docker-compose... manages these programs starting. Some tools defines the dependencies amoung the programs (such as docker-compose) and some tools does not(such as supervisor). Even the start-up order is defined, but there is no mechanism to check if a program is ready or not.

To solve the above paint-points, this application is designed. 

### Configuration file

This program requires a yaml or json configuration file. This configuration file includes:
* Optional pre-start script. The pre-start script can be used to check if some dependencies( include the dependency environment and its dependency programs) are ready or not.
* Optional start script. The start script will be used to start the program
* Optional post_start script. The post-start script can be used to check if the program is ready or not.
* Optional pre_stop script. The pre-stop script will be called before the stop script is called.
* Optional stop script. The stop script is used to stop the program.
* Optional post_stop script. The post-stop script will be called after the stop script is called.
* Optional depends-on programs. A list of programs that this program depends on.

Following is an example configuration file in yaml:

```yaml
programs:
  db:
    start: 'docker run --name db-1 -d db'
    post_start: 'sleep 10'
    stop: 'docker stop db-1'
    post_stop: 'docker rm db-1'
  web:
    start: 'docker run --name web-1 -d web'
    stop: 'docker stop web-1'
    post_stop: 'docker rm web-1'
    depends_on:
      - db
```

The above configuration file describe how to start two docker programs with dependencies. The web application depends on the db. So the db will be started at first and after 10 seconds the web application will be started.

### Start programs

After the configuration file is ready, we can start them by simply call:
```shell
$ ./program_starter.py -f <configuration_file> start
```

The programs will be started in order: 
- start db first
- sleep 10 seconds
- start web program.

If want to start web and its dependencies, simply call (with -r option):
```shell
$ ./program_starter.py -f <configuration_file> -r start web
```

This above command will start the web and its dependecy program db in order:
- start db
- sleep 10 seconds
- start web

If want to start db program only, simply call(without -r):
```shell
$ ./program_starter.py -f <configuration_file> start db
```

### Stop programs

If want to stop all program, simply call:
```shell
$ ./program_starter.py -f <configuration_file> stop
```
The above script will stop all the programs in order (reverse of start order).

If want to stop a program and the related depends program, simply call:
```shell
$./program_starter.py -f <configuration_file> -r stop db
```

The above command will stop the db and web ( depends on db).

But the command:
```shell
$ ./program_starter.py -f <configuration_file> stop db
```
only stop the program db, the program web will not be stopped.

### Enviroment variables in program script

Some environment variables can be put in the program script( pre-start, start, post-start, pre-stop, stop and pos-start script). The environment variable is in format:

```shell
${ENV_VAR:def_value}
```

So if java will be used in the program script, we can simply put the environemt variable JAVA_HOME in the script like:
```shell
${JAVA_HOME:/your/default/java/home}
```
if the environment variable JAVA_HOME is set, the above string will be replaced with the value of JAVA_HOME enviornment variable. If JAV_HOME is not set, the above string will be "/your/default/java/home".

#### Environment variable file
The environment variable can be set in the shell or can be loaded from a environment file by command line argument "-e" or "--env_file". One environment variable should be put in one line and line start with '#' will be regarded as comments and will be ignored.

```text
# java home
JAVA_HOME=/opt/jdk1.8
ANT_HOME=/opt/ant1.9.1
```

#### The special environment variable ${PROGRAM}

There is a sepcial environment variable named ${PROGRAM}, this envirment variable is not set by shell or loaded from the environment file. It is set by the program itself. Its value is the name of current start/stop program.

So the configure file:
```yaml
programs:
  db:
    start: 'docker run --name db-1 -d db'
    post_start: 'sleep 10'
    stop: 'docker stop db-1'
    post_stop: 'docker rm db-1'
  web:
    start: 'docker run --name web-1 -d web'
    stop: 'docker stop web-1'
    post_stop: 'docker rm web-1'
    depends_on:
      - db
```

can be replaced with:

```yaml
programs:
  db:
    start: 'docker run --name ${PROGRAM}-1 -d ${PROGRAM}'
    post_start: 'sleep 10'
    stop: 'docker stop ${PROGRAM}-1'
    post_stop: 'docker rm ${PROGRAM}-1'
  web:
    start: 'docker run --name ${PROGRAM}-1 -d ${PROGRAM}'
    stop: 'docker stop ${PROGRAM}-1'
    post_stop: 'docker rm ${PROGRAM}-1'
    depends_on:
      - db
```
in the program db, the environment variable ${PROGRAM} stands for the "db" and in the web program, the ${PROGRAM} stands for the "web".

### MIT License
Copyright 2017 Steven Ou

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.


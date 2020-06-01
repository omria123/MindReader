![build status](https://travis-ci.com/omria123/MindReader.svg?branch=master)
[![codecov](https://codecov.io/gh/omria123/MindReader/branch/master/graph/badge.svg)](https://codecov.io/gh/omria123/MindReader)


1. Clone the repository:

   ```shell script
   $ clone https://github.com/omria123/MindReader.git
   ...
   $ cd MindReader 
   ```
2. Run the install script:

    ```shell script
    $ ./scripts/install.sh
    ...
    $ source .env/bin/activate
    [MindReader] $ # you're good to go!
   
## Usage

The package implements a pipeline of uploading and processing snapshots from different users.

The package provides the following Interface:

- Client Side
    
    The client side can read a sample from given URL/PATH and upload it to the server.
    
    - CLI
    
        ```shell script
        $ python -m MindReader.client upload-sample [OPTIONS] PATH/URL  
        ```
        
        With the different options the user can control the following attributes:
        
        1. The server which receives the data. (Default to localhost:8000)
    
        2. The format of the sample. (Default to protobuf)
        
        3. How the sample is achieved (As a normal file, compressed one or maybe from HTTP URL).
        Controlled by the scheme of the URL or as a separate argument.
        
        4. The amount of snapshots taken from that sample.
    
    - Python
    
        The following functions are available:
        
        ```python
      from MindReader.client import upload_sample, publish_sample
      publish_sample(path, user_publisher, ...)
      upload_sample(path, host, port)
        ```
      The only difference is that publish_sample publishes the user with a given function 
      (The function should return the snapshot publisher). While the other one is uploading it directly to the server.
      

- Server Side
    
    The server side is responsible for receiving the snapshots from the endpoint users.
    The server saves the snapshot raw data to a file, and transfer it to the workers on the message queue.
    - CLI
        ```shell script
        $ python -m MindReader.server [OPTIONS] run-server MQ-URL  
        ```
      
        While the user can control the following options:
        
        1. The address which the server binds on.
     
        2. The DATA Directory which stores the Snapshots.
        
    - Python
    
        ```python
        from MindReader.server import run_server, run_server_publisher
        run_server(mq_url, host, port, data_dir) # All but mq_url are optional
        run_server_publisher(host, port, user_publisher, snapshot_publisher)       
        ```
        The first one is exactly as the CLI version 
        
        The latter function is less conventional, but great for experimenting. Simply publishes the results to functions.
        
       
      
- Parsers
    
    The different parsers take the server as published from the server, parse it and move it forward to 
    saver (Will be discussed later), to save it to a DB.
   
   - CLI
       
        ```shell script
          $ python -m MindReader.parsers run-parsers -n name1 -n name2 ... MQ-URL 
        ```
        Attaches the given parsers to work on the queue. The process will begin to consume immediately.
        
        Note: The MQ-URL should also include the scheme which imply the specific MQ.
        For example rabbitmq://127.0.0.1:5672. (The same goes in the future and for DB-URL)
        
        Note: When running parsers together in the same command, all of them works on the same process.
        (Which is ideally better/fine for one computer or any simple case)
        
        ```shell script
          $ python -m MindReader.parsers parse PATH NAME
        ```    
        Parses a single snapshot from some path. 
        Note: The parsers uses the snapshot suffix to interpreter the encoding of the snapshot.
        
   - Python
            
        ```python
        from MindReader.parsers import parse, run_parsers
        parse(result_name, path)
        run_parsers(parser_names, mq_url)
        ```
        The two correlate to their twin CLI function. 

- Saver
    The saver responsible to take the information from the MQ from his own queue, and save it to the DB.
    
    Note: For now the client is received as JSON (The server receives it like it). 
    So it transferred directly to the saver from the server. In future case of several formats, we can simply give it a
    special middle queue from the server to the saver.
    
    - CLI
        
        ```shell script
        $ python -m MindReader.saver run-saver MQ-URL DB-URL 
        ```
        
    - Python
        
        ```python
        from MindReader.saver import Saver
        saver = Saver(DB_URL)
        saver.save(name, value)
        saver.save_user(user) # Dict with all the attributes
        ```
        
        Note that the value must be a dict as returned from `parse`, but with the user_id, snapshot_id.


- API Server
       
   The API server consumes the DB and publishes give a REST-API to get the data.
   The API also expose a GUI interface from http://host:port/.
   
   To invoke the API one should do one of the following:
   
   - CLI
        ```shell script
        $ python -m MindReader.api run-api-server [OPTIONS] DB-URL
        ```
        The user can use the options to change the address of the server
   
   - Python
   
        ```python
        from MindReader.api import run_api_server
        run_api_server(host, port, database)
        ```  
- CLI Access to read Server

    The package also supports CLI reading of the
    
    ```shell script
    $ python -m cortex.cli get-users
    ...
    $ python -m cortex.cli get-user USER-ID
    ...
    $ python -m cortex.cli get-snapshots USER-ID
    ...
    $ python -m cortex.cli get-snapshot USER-ID SNAPSHOT-ID
    ...
    $ python -m cortex.cli get-result USER-ID SNAPSHOT-ID NAME
    ```

## SUBPACKAGES

- Database
    
    This subpackage offers abstraction to the database interface.
    
    ```python
    from MindReader.Database import Database
    db = Database('mongo://localhost:27017')
    user = db.get_user(user_id)
    ...
    ```

- MessageQueue

    This subpackage offers abstraction to the database interface.
    
    ```python
    from MindReader.MessageQueue import MessageQueue
    mq = MessageQueue('rabbimq://localhost:5672')
    mq.publish_user(user)
    ...
    ```
- IOAccess
    This subpackage offers abstraction for all read/write operations.
    
    The subpackage offer 3 different utilities:
    
    - Driver
        
        A driver is a simple file-like object. We identify them by scheme, and then later can call them by their scheme.
        
        For abstracting this method, we have Driver.open
        
        ```python
        from MindReader import IOAccess
        for path in ['http://website.com/file', 'file:///etc/passwd', 'gzip://sample.mind.gz']
              fd = IOAccess.open(path,scheme=scheme,...) # Totally works!!
        ```
        The scheme can be given as key-argument or in the path. 
        When no scheme is given (The path or as key-arg) file is used
          
    - Writers & Readers
   
        Those utilities are used to abstract the different formats to read/write an object.
        A writer/reader are identified by two - (object-name, version)
        
        The object name says what we are reading/writing, and the version represent the format.
        Those will be used to select them
        
        The usage goes as following:
        ```python
        from MindReader import IOAccess
        with IOAccess.open('path/to/file', mode='rb') as fd:
          IOAccess.read(fd, 'object-name', version='format/version of encoding', ...)  # ... will get to the reader
        
        with IOAccess.open('path/to/file', mode='wb') as fd:
          IOAccess.write(fd, 'object-name', version='format/version of encoding', ...) # ... will get to the writer
        
        IOAccess.read_url('scheme://path', 'object-name',version='format/version of encoding',...)
        IOAccess.write_url('scheme://path', 'object-name',version='format/version of encoding',...)
        ```
        
        The access_url functions are used for the comfort of the user.


## TESTING

For the simple tests simply run: (From the project folder)
   
    $ pytest tests/
    
To confirm everything works.

For some more complicated and long test you should run 

    $ pytest tests/some_test_file.py

Where the file is not one of the default test modules (It's name doesn't start with test).

Those tests use Message Queue and the Databases as dockers, and for sync they use a lot of sleep.


## LOGGING

The logging settings are stored in MindReader/utils/log.ini

You can change the logging level for any logger (A logger for every module) as you wish.

## MAINTENANCE 

For all the subpackages there is a documentation for this in each dunder-init.py.
This will allow us change the sample, client-server communication and the sample source, without much refactoring.
This gives us plenty of freedom to expand the functionality of the system. For example, 
Let the server save the snapshots on remote location, maybe adding SMB. 
        
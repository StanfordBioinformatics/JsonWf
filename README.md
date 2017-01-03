©2014 The Board of Trustees of the Leland Stanford Junior University

JsonWf
======
Created:  March 31, 2014  
Nathaniel Watson  
Stanford University Department of Genetics  
SCGPM http://scgpm.stanford.edu  
nathankw@stanford.edu

NOTE - This documentation is under active development.

#### Abstract:
JsonWf is a JSON format specification for defining workflow configuration; it is also the software supports executing pipelines written according to this specification.  A worfklow is defined as a set of related tasks, or jobs, that are to be executed for some given input data. Separating the configuration from the workflow code itself allows for ease in workflow management and customization.  In JsonWf, the workflow configuration is written in JSON in a format that abides by a built-in schema, which allows for powerful error checking.  Parameters, input and output file names, and job depencendies can easily be defined without any redundancy through the use of variables.  A workflow's complete set of configuration, which shall be referred to as a (workflow) definition, may be programatically parsed via the API for use in downstream software. In addition, JsonWf includes a built-in tool to write the definition into a SJM pipeline.
  

The main script that reads a file in JsonWf format is called jsonWorkflow.py.  Given a definition, JsonWf will:
	
	1) ensure that the workflow definition is all valid JSON,
	2) validate the configuration against the built-in schema.  This will catch many types of potential errors in the configuration, including typos, undefined variables, and circular job dependencies,
	3) create a directed acyclic graph (DAG) to deconvolute job dependencies,
	4) write the validated and parsed configuration to a file in a format known as SJM format, which is understood by the SJM (Simple Job Manager) tool. The file in SJM format should be thought of as the worklfow itself (and not the workflow definition as previously discussed), and 
	5) call SJM to execute the SJM file (workflow) locally or on either the OGE or LSF compute cluster.  More about SJM further below.


A prototype workflow definition for demonstrating the capabilities of JsonWf is Kwality, which is the first definition written in JsonWf. There is a useful Google Slides document [1] that demonstrates the usage of JsonWf and introduces you to the Kwality workflow.  In fact, JsonWf and Kwality co-evolved together, and in the beginning were part of the same piece of software.  Kwality contains a set of commands for obtaining statistics and other QC measaures for DNA sequence data analysis, and is shipped with JsonWf especially for demonstration purposes.  Another prototype definition is called bwa-aln-se.json, which also ships with this software; and this prototype demonstrates the use of dependencies whereas Kwality does not at present.

SJM is currently not included with the JsonWf distribution, but is a accessible from github at https://github.com/StanfordBioinformatics/SJM/blob/master/doc/MANUAL.txt . SJM is a tool for managing a set of jobs that are run on OGE or LSF compute cluster, or locally on one's personal computer. **Note!** Here at Stanford we only support the software on SGE/OGE. We have not thoroughly tested SJM on other grid engines; nonetheless it should work with any DRMAA 1.0 compliant grid engines.

Required arguments of jsonWorkflow.py are the workflow definition file (-c) and the output directory (--outdir). Job standard output (stdout) and standard error (stderr) streams will be written to files within the JobStatus directory. This directory is a sub-directory of the output directory given to jsonWorkflow.py, and is automatically created.

#### JSON SCHEMA:
The packaged schema schema.json defines the rules and structure of the 
user-generated workflow definition file. Take a look at the template conf.json as a guide while you read about the schema below.  Also, feel free to browse the schema file schema.json directly. Each analysis that you want to execute is defined within a JSON object called "analyses", which is an array.  Each analysis in this array can enabled (turned on) or disabled (turned off) with the "enable" keyword.  The schema allows for desired JSON keys to act as global variables, which can then be referenced across analyses.  For example, the output file of some analysis (call it Analysis1) may need to be the input file of some other analysis (call it Analysis2), and the output file can thus be defined as a resource in order for the latter analysis to have access to it. 

Resources can be defined in several ways. First, they may defined on the command line as arguments of the form key=value, where key is the resrouce name. Second, the definition file is allowed to have a top-level "resources" object that may contain a "qsub" child object, along with custom user-defined resources specified as JSON "key": "value" properties. Any keys defined in the "resources" object may reference any pre-defined resources on the command-line. The reference definition is formatted as a variable in BASH syntax.  For example, if input=x was was passed as an argument on the command-line, then the resource "input" could be referenced in the value of a property in the "resource" object as so: "$input" or "${input}". The "qsub" object serves to define settings for the job submission mechanism of the cluster, such as "qsub" for SGE or OGE.  These settings will be used for all analyses. Any analysis can overwride any of these qsub settings by defining it's own, local "qsub" object. Local qsub settings overwrite global qsub settings for that analysis, and can also define additional local qsub parameters not defined in the global qsub object. Finally, each analysis can have object "outdirs", which specifies output directory names, and "outfiles, which specifies output file names. The properties defined within these two objects are also global resources. An analysis can reference an output file or output directory resource of another analysis only if it depends on that analysis; dependencies are defined below.  An analysis can reference any global resource that was defined on the command-line or in the "resources" object (except for the "resources" qsub child object).


Comments - Any key prefixed with a "#" will be ignored.  The "#" must be within the quotation marks of the key.

Analyses - Multiple analyses can be defined within the top-level "analyses"
object.  An analysis is defined as an executable that can have command-line options and
arguments. Dependencies on other analyses can be specified. Each analysis object may contain a
"params" object, an "args" object, and a "qsub" object.  The params object
lays out the analysis parameters/options, while the args object contains an array of all the non-option arguments of the analysis.
The qsub object of an analysis is used to specialize the global qsub object by means of locally overwriting global qsub properties and adding additional ones. When an analysis is executed by one of the supported grid engines, the name of the grid engine job will be the same as the analysis name, unless the "name" key of the "qsub" object is defined which takes precedence.

Qsub object properties:
1) 'directory' sets the working direcory in which the analysis will be executed on the cluster. 

There is limited support JSON pointers see, as defined in rfc6901 (http://tools.ietf.org/html/rfc6901). Currently, only absolute JSON pointers to values within the same document are supported. Instead of using pointers, use the resource mechanism described above.

More documentation coming ...

#### References:
[1] Google Slides document for Kwality https://docs.google.com/a/stanford.edu/presentation/d/1sOQ2dJhI9bFvlU7GDiyrNfRP2r9Op06xc4qp2JTni5U/edit?usp=drive_web

#### ABBREVIATIONS:

SGE - Sun Grid Engine  
OGE - Open Grid Engine

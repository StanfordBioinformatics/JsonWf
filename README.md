JsonWf
======

clinical qc package

March 31, 2014
Nathaniel Watson

Abstract:
JsonWf is a tool for building structured workflows in JSON format.  Each JSON workflow is structured according to a built-in schema.  
Kwality performs multiple QC analyses for data in FASTQ, BAM, and VCF format. Analyses run in parallel, apart from specified dependencies, on a cluster.  The tool is executed with the script kwality.py, which requires a configuration (conf) file in JSON format, a directory name in which to execute all analyses, and a job file name.  The conf file is validated against a built-in JSON schema. The output job file is written in Simple Job Manager (SJM) format, and is executed with the sjm command; see https://github.com/StanfordBioinformatics/SJM/blob/master/doc/MANUAL.txt for more details.  SJM is a tool for managing a set of jobs that are run on a cluster (i.e. Open Grid Engine). SJM is not included in the kwality bundle. Job stdout and stderr streams will be written to files within the JobStatus directory. This directory is a sub-directory of the output directory given to kwality.py, and is automatically created.

JSON SCHEMA:
The packaged schema schema.json defines the rules and structure of the 
user-generated conf file. Take a look at the template conf.json config file as a guide while you read about the schema below.  Also, feel free to browse the schema file directly. Each analysis that you want to execute is defined within a JSON object called "analyses", which is an array.  Each analysis in this array can enabled (turned on) or disabled (turned off) with the "enable" keyword.  The schema allows for desired JSON keys to act as global variables, which can then be referenced across analyses.  For example, the output file of some analysis (call it Analysis1) may need to be the input file of some other analysis (call it Analysis2), and the output file can thus be defined as a resource in order for the latter analysis to have access to it. 

Resources can be defined in several ways. First, they may defined on the command line as arguments of the form key=value, where key is the resrouce name. Second, the conf file is allowed to have a top-level "resources" object that may contain a "qsub" child object, along with custom user-defined resources specified as JSON "key": "value" properties. Any keys defined in the "resources" object may reference any pre-defined resources on the command-line. The reference definition is formatted as a variable in BASH syntax.  For example, if input=x was was passed as an argument on the command-line, then the resource "input" could be referenced in the value of a property in the "resource" object as so: "$var" or "${var}". The "qsub" object serves to define settings for the job submission mechanism of the cluster, such as "qsub" for SGE or OGE.  These settings will be used for all analyses. Any analysis can overwride any of these qsub settings by defining it's own, local "qsub" object. Local qsub settings overwrite global qsub settings for that analysis, and can also define additional local qsub parameters not defined in the global qsub object. Finally, each analysis can have object "outdirs", which specifies output directory names, and "outfiles, which specifies output file names. The properties defined within these two objects are also global resources. An analysis can reference an output file or output directory resource of another analysis only if it depends on that analysis; dependencies are defined below.  An analysis can reference any global resource that was defined on the command-line or in the "resources" object (except for the "resources" qsub child object).


Comments - Any key prefixed with a "#" will be ignored.  The "#" must be within the quotation marks of the key.

Analyses - Multiple analyses can be defined within the top-level "analyses"
object.  An analysis is defined as an executable that can have command-line options and
arguments. Dependencies on other analyses can be specified. Each analysis object may contain a
"params" object, an "args" object, and a "qsub" object.  The params object
lays out the analysis parameters/options, while the args object contains an array of all the non-option arguments of the analysis.
The qsub object of an analysis is used to specialize the global qsub object by means of locally overwriting global qsub properties and adding additional ones.

Qsub object properties:
1) 'directory' sets the working direcory in which the analysis will be executed on the cluster. 

There is limitid support JSON pointers see, as defined in rfc6901 (http://tools.ietf.org/html/rfc6901). Currently, only absolute JSON pointers to values within the same document are supported. Instead of using pointers, use the resource mechanism described above.

More documentation coming ...

ABBREVIATIONS:
SGE - Sun Grid Engine
OGE - Open Grid Engine

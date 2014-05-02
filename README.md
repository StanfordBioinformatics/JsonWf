March 31, 2014
Nathaniel Watson

Kwality: A tool for running multiple quality metrics on read, mapping, and
variant inputs


SUMMARY: 
Kwality performs multiple QC analyses for data in FASTQ, BAM, and VCF format. Analyses run in parallel, apart from specified dependencies, on a cluster.  The tool is executed with the script kwality.py, which requires a configuration (conf) file in JSON format, a directory in which to output the resulting data files, and a job file name.  The conf file must abide by the built-in schema, and kwality.py ensures this with validation. The job file will be written in Simple Job Manager (SJM) format; see https://github.com/StanfordBioinformatics/SJM/blob/master/doc/MANUAL.txt for more details.  This format specifies how jobs are to run on a cluster (i.e. Open Grid Engine), such as as what resources to allocate per job and job dependencies.  The SJM file can be luanched with the sjm command.  SJM is not included in the kwality bundle.

Job stdout and stderr streams will be written to individual files within a JobStatus directory. This directory is a sub-directory of the output directory given to kwality.py, and is automatically created.

JSON SCHEMA:
The packaged schema schema.json defines the rules and structure of the
user-generated conf file. Take a look at the template conf.json config file as a guide while you read about it's schema below.  Also, feel free to browse the schema file directly.
The schema allows for:

1) Comments - Any key prefixed with a "#" will be ignored.  The "#" must be within the quotation marks of the key.

2) Analyses - Multiple analyses can be defined within the top-level "analyses"
object.  An analysis is defined as an executable that can have command-line (CL) options and
arguments. Dependencies on other analyses can be specified. Each analysis object may contain a
"params" object, an "args" object, and a "qsub" object.  The params object
lays out the analysis parameters/options, while the args object contains an array of all the non-option arguments of the analysis, 
whereas the qsub object gives the Grid Engine job arguments and values for running the analysis on the cluster.

2) General Resources - A top-level 'resources' object.  This is where you may 
define common keys that can appear in multiple analyses. A particular key in an analysis can reference a
resource by setting its value to the resource name, prefixed with "${" and suffixed with "}", which is a variable.  For example, the config file could
have this key and value pair:   "name": "${name}"   and all resources will then be checked for one by the name of 'name'.  Furthermore, a variable can appear 
within other text.  For example:
	"path": "/data/dev/${project}/all"
Furthermore, all resources are added to the list of environment variables, and each JSON string value is evaluated through the shell. Therefore, BASH syntax of any sort is supported in the value and will be evaulated through the shell's 'echo' utility.

3) QSUB Resources - A top-level 'qsub' object that contains qsub options to
use across all analyses. This is usefule for setting common options only once,
rather that repetitively for each analysis. A reference is made to a qsub
resource in the same way as to a general resource.

4) Limitid support JSON pointers see, as defined in rfc6901 (http://tools.ietf.org/html/rfc6901). Currently, only absolute JSON pointers to values within the same document are supported.


In addition to the general resources specified in the conf file, resources may
also be specified on the CL as arguments in key=value form, where
each argument is spearated by whitespace. These CL resources will be added to
the conf's resources, and replacing any having the same name. 
Read the schema for a full understanding of the structure and semantics of a
conf file.



